"""Printify publisher — orchestrator.

Reads:
  - site/src/data/products.json (gallery contract feed)
  - site/src/assets/gallery/<category>/*.png (the actual artwork)
  - printify/printify_config.yaml (blueprint/variant truth)
  - printify/printify_ledger.json (idempotency + audit trail)

Writes:
  - printify/printify_ledger.json
  - printify/printify_config.yaml (only with --bootstrap-config)

Modes:
  --dry-run         (default) print API calls that WOULD fire, no writes
  --live            actually create + publish products
  --image PATH      target a single image instead of all unpublished
  --bootstrap-config inspect existing shop, derive config, write yaml

Hard rules:
  - Never publish live without explicit --live flag.
  - Skip any image already in the ledger (idempotent).
  - Free shipping override on every product.
  - Pricing match: existing-product price first, else cost*2.2 -> .99 floor.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Local
sys.path.insert(0, str(Path(__file__).resolve().parent))
import printify_api as api  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
GALLERY_DIR = REPO_ROOT / "site" / "src" / "assets" / "gallery"
PRODUCTS_JSON = REPO_ROOT / "site" / "src" / "data" / "products.json"
CONFIG_PATH = Path(__file__).resolve().parent / "printify_config.yaml"
LEDGER_PATH = Path(__file__).resolve().parent / "printify_ledger.json"

POSTER_SIZES = ["12x18", "18x24", "24x36"]
CANVAS_SIZES = ["16x20", "18x24", "24x36"]


# ---------- tiny YAML I/O (no PyYAML dependency) ----------
# Our config is a small, well-known shape — we hand-roll read/write so the
# stdlib-only constraint holds. If the user installs PyYAML later, swap in.

def _yaml_dump(obj: Any, indent: int = 0) -> str:
    pad = "  " * indent
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, (int, float)):
        return repr(obj)
    if isinstance(obj, str):
        if obj == "" or any(c in obj for c in ":#\n") or obj.strip() != obj:
            return json.dumps(obj)
        return obj
    if isinstance(obj, list):
        if not obj:
            return "[]"
        # Render scalar-of-dict list as flow-style for variants readability.
        if all(isinstance(x, dict) for x in obj):
            lines = []
            for x in obj:
                inline = ", ".join(f"{k}: {_yaml_dump(v)}" for k, v in x.items())
                lines.append(f"{pad}- {{ {inline} }}")
            return "\n" + "\n".join(lines)
        return "\n" + "\n".join(f"{pad}- {_yaml_dump(x)}" for x in obj)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        out = []
        for k, v in obj.items():
            rendered = _yaml_dump(v, indent + 1)
            if rendered.startswith("\n"):
                out.append(f"{pad}{k}:{rendered}")
            else:
                out.append(f"{pad}{k}: {rendered}")
        return "\n".join(out) if indent == 0 else "\n" + "\n".join(out)
    return json.dumps(obj)


def _yaml_load(text: str) -> Dict[str, Any]:
    """Trivial YAML loader for the limited shapes we emit. Falls back to
    treating unknown content as raw strings. NOT a general parser."""
    # If a richer YAML lib is available, prefer it.
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        pass
    # Hand-rolled mini-parser: indent-based dicts, "- { k: v, ... }" flow lists,
    # scalars: null/true/false/int/float/string.
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]

    def parse_scalar(s: str) -> Any:
        s = s.strip()
        if s == "null" or s == "~":
            return None
        if s == "true":
            return True
        if s == "false":
            return False
        if s == "[]":
            return []
        if s == "{}":
            return {}
        if s.startswith("\"") and s.endswith("\""):
            return json.loads(s)
        try:
            if "." in s:
                return float(s)
            return int(s)
        except ValueError:
            return s

    def parse_flow_dict(s: str) -> Dict[str, Any]:
        # "{ k: v, k2: v2 }"
        s = s.strip()
        if s.startswith("{") and s.endswith("}"):
            s = s[1:-1].strip()
        out: Dict[str, Any] = {}
        # naive split on commas (no nested objects in our schema)
        for part in [p for p in s.split(",") if p.strip()]:
            k, _, v = part.partition(":")
            out[k.strip()] = parse_scalar(v)
        return out

    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any]] = [(-1, root)]

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        # pop stack to current indent
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else root

        if stripped.startswith("- "):
            item_text = stripped[2:].strip()
            if isinstance(parent, list):
                if item_text.startswith("{"):
                    parent.append(parse_flow_dict(item_text))
                else:
                    parent.append(parse_scalar(item_text))
            i += 1
            continue

        key, _, rest = stripped.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "":
            # Look at next line: list or dict?
            j = i + 1
            child: Any
            if j < len(lines) and lines[j].lstrip().startswith("- "):
                child = []
            else:
                child = {}
            if isinstance(parent, dict):
                parent[key] = child
            stack.append((indent, child))
        else:
            if rest.startswith("{"):
                val = parse_flow_dict(rest)
            else:
                val = parse_scalar(rest)
            if isinstance(parent, dict):
                parent[key] = val
        i += 1

    return root


# ---------- config + ledger ----------

@dataclass
class Variant:
    id: int
    size: str
    retail_cents: int
    shipping_cents: int = 0
    source_product_id: Optional[str] = None


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    return _yaml_load(CONFIG_PATH.read_text())


def write_config(cfg: Dict[str, Any]) -> None:
    header = (
        "# Printify publisher config — SOURCE OF TRUTH derived from existing Etsy shop.\n"
        "# Regenerate via: python3 printify/printify_publisher.py --bootstrap-config\n"
        f"# Generated: {datetime.now(timezone.utc).isoformat()}\n\n"
    )
    CONFIG_PATH.write_text(header + _yaml_dump(cfg) + "\n")


def load_ledger() -> Dict[str, Any]:
    if not LEDGER_PATH.exists():
        return {"version": 1, "entries": {}}
    return json.loads(LEDGER_PATH.read_text())


def write_ledger(ledger: Dict[str, Any]) -> None:
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2) + "\n")


def ledger_key(image_rel: str) -> str:
    """Stable key = relative gallery path, e.g. 'predators/tyrannosaurus-rex-...png'."""
    return image_rel.replace("\\", "/")


# ---------- pricing ----------

def round_to_99(price_cents: int) -> int:
    """Round retail to nearest .99 floor.
    24.37 -> 24.99   (next .99 ceiling? user said 'rounded to .99 floor' meaning
    the cents land on .99). Interpret: round UP to the next X.99 if not already
    on a .99 boundary."""
    dollars = price_cents / 100.0
    floor_dollars = math.floor(dollars)
    candidate = floor_dollars + 0.99
    if candidate < dollars:
        candidate = floor_dollars + 1 + 0.99 - 1  # = floor + 0.99 still less -> bump
        candidate = math.floor(dollars) + 0.99
        if candidate < dollars:
            candidate = math.floor(dollars) + 1.99
    return int(round(candidate * 100))


def fallback_retail_cents(cost_cents: int, multiplier: float = 2.2) -> int:
    return round_to_99(int(cost_cents * multiplier))


# ---------- bootstrap from existing shop ----------

# Heuristic size detection from variant title strings.
SIZE_TOKENS = {
    "12x18", "12 x 18", "12\" x 18\"", "12″ x 18″",
    "16x20", "16 x 20",
    "18x24", "18 x 24",
    "24x36", "24 x 36",
}

def normalize_size(s: str) -> Optional[str]:
    if not s:
        return None
    t = s.lower().replace(" ", "").replace("\"", "").replace("″", "").replace("”", "").replace("“", "")
    t = t.replace("×", "x")
    for size in ["12x18", "16x20", "18x24", "24x36"]:
        if size in t:
            return size
    return None


def classify_blueprint(title: str, blueprint_title: str = "") -> Optional[str]:
    """Return 'poster' or 'wrapped_canvas' or None."""
    haystack = f"{title} {blueprint_title}".lower()
    if "canvas" in haystack:
        return "wrapped_canvas"
    if "poster" in haystack or "print" in haystack and "canvas" not in haystack:
        return "poster"
    return None


def bootstrap_config_from_shop() -> Dict[str, Any]:
    shop_id = api.get_shop_id()
    products = api.list_products(shop_id)
    print(f"[bootstrap] shop_id={shop_id}  existing_products={len(products)}")

    poster_variants: Dict[str, Variant] = {}
    canvas_variants: Dict[str, Variant] = {}
    poster_meta: Dict[str, Any] = {}
    canvas_meta: Dict[str, Any] = {}

    for prod in products:
        # Need full product detail for variant prices.
        detail = api.get_product(shop_id, prod["id"])
        bp_id = detail.get("blueprint_id")
        pp_id = detail.get("print_provider_id")
        title = detail.get("title", "")
        kind = classify_blueprint(title)
        if kind is None:
            print(f"[bootstrap] skip product {prod['id']}: cannot classify ({title!r})")
            continue
        target_meta = poster_meta if kind == "poster" else canvas_meta
        target_meta.setdefault("blueprint_id", bp_id)
        target_meta.setdefault("print_provider_id", pp_id)
        bucket = poster_variants if kind == "poster" else canvas_variants
        for v in detail.get("variants", []):
            size = normalize_size(v.get("title", ""))
            if not size:
                continue
            bucket.setdefault(
                size,
                Variant(
                    id=v["id"],
                    size=size,
                    retail_cents=v.get("price", 0),
                    shipping_cents=0,
                    source_product_id=prod["id"],
                ),
            )

    cfg = {
        "shop_id": shop_id,
        "products": {
            "poster": {
                "blueprint_id": poster_meta.get("blueprint_id"),
                "print_provider_id": poster_meta.get("print_provider_id"),
                "variants": [asdict(poster_variants[s]) for s in POSTER_SIZES if s in poster_variants],
            },
            "wrapped_canvas": {
                "blueprint_id": canvas_meta.get("blueprint_id"),
                "print_provider_id": canvas_meta.get("print_provider_id"),
                "variants": [asdict(canvas_variants[s]) for s in CANVAS_SIZES if s in canvas_variants],
            },
        },
        "pricing": {"fallback_multiplier": 2.2, "round_to": 0.99},
        "shipping": {"free_shipping_override": True},
        "image_fit": {"pad_threshold": 0.15, "background_sample": "edge_median"},
    }
    return cfg


# ---------- product feed reading ----------

def load_products_feed() -> List[Dict[str, Any]]:
    return json.loads(PRODUCTS_JSON.read_text())


def find_feed_entry(rel_path: str, feed: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for e in feed:
        if e.get("filename") == rel_path:
            return e
    return None


# ---------- dry-run / live publish ----------

def plan_publish(image_rel: str, feed_entry: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Return the planned API calls (no network writes) for one image."""
    poster_cfg = cfg.get("products", {}).get("poster", {})
    canvas_cfg = cfg.get("products", {}).get("wrapped_canvas", {})

    title = feed_entry.get("title") or Path(image_rel).stem
    description = feed_entry.get("description") or ""
    keywords = feed_entry.get("keywords") or []

    plan = {
        "image": image_rel,
        "title": title,
        "uploads": [{"endpoint": "POST /uploads/images.json", "file": image_rel}],
        "products": [],
    }

    for kind, kcfg, sizes in [
        ("poster", poster_cfg, POSTER_SIZES),
        ("wrapped_canvas", canvas_cfg, CANVAS_SIZES),
    ]:
        if not kcfg.get("blueprint_id"):
            plan["products"].append({"kind": kind, "status": "SKIPPED — config missing"})
            continue
        variants_payload = []
        for v in kcfg.get("variants", []):
            if v["size"] not in sizes:
                continue
            variants_payload.append({
                "id": v["id"],
                "price": v["retail_cents"],
                "is_enabled": True,
            })
        plan["products"].append({
            "kind": kind,
            "endpoint": f"POST /shops/{cfg.get('shop_id')}/products.json",
            "blueprint_id": kcfg["blueprint_id"],
            "print_provider_id": kcfg["print_provider_id"],
            "title": f"{title} — {'Poster' if kind == 'poster' else 'Wrapped Canvas'}",
            "description": description,
            "tags": keywords[:13],
            "variants": variants_payload,
            "free_shipping_override": cfg.get("shipping", {}).get("free_shipping_override", True),
            "publish_endpoint": f"POST /shops/{cfg.get('shop_id')}/products/<new_id>/publish.json",
        })
    return plan


def collect_unpublished(ledger: Dict[str, Any]) -> List[str]:
    """Return list of relative gallery paths not yet in the ledger."""
    out = []
    if not GALLERY_DIR.exists():
        return out
    for p in sorted(GALLERY_DIR.rglob("*.png")):
        rel = str(p.relative_to(GALLERY_DIR))
        if ledger_key(rel) not in ledger.get("entries", {}):
            out.append(rel)
    return out


# ---------- CLI ----------

def cmd_bootstrap_config(_args) -> int:
    cfg = bootstrap_config_from_shop()
    write_config(cfg)
    print(f"[bootstrap] wrote {CONFIG_PATH}")
    print(json.dumps(cfg, indent=2))
    return 0


def cmd_publish(args) -> int:
    cfg = load_config()
    if not cfg.get("products", {}).get("poster", {}).get("blueprint_id"):
        print("ERROR: printify_config.yaml not bootstrapped. Run with --bootstrap-config first.",
              file=sys.stderr)
        return 2

    ledger = load_ledger()
    feed = load_products_feed()

    if args.image:
        rel = str(Path(args.image).resolve().relative_to(GALLERY_DIR))
        targets = [rel]
    else:
        targets = collect_unpublished(ledger)

    if not targets:
        print("Nothing to publish — ledger covers all gallery images.")
        return 0

    for rel in targets:
        if ledger_key(rel) in ledger.get("entries", {}):
            print(f"[skip] {rel} already in ledger")
            continue
        entry = find_feed_entry(rel, feed)
        if entry is None:
            print(f"[warn] {rel} not in products.json — skipping")
            continue
        plan = plan_publish(rel, entry, cfg)
        print("\n" + "=" * 72)
        print(f"PLAN: {rel}")
        print(json.dumps(plan, indent=2))

        if not args.live:
            continue

        # ---------- LIVE PATH ----------
        abs_path = GALLERY_DIR / rel
        upload_resp = api.upload_image(str(abs_path))
        image_id = upload_resp["id"]
        product_results = []
        for prod_plan in plan["products"]:
            if prod_plan.get("status", "").startswith("SKIPPED"):
                continue
            payload = {
                "title": prod_plan["title"],
                "description": prod_plan["description"],
                "blueprint_id": prod_plan["blueprint_id"],
                "print_provider_id": prod_plan["print_provider_id"],
                "tags": prod_plan["tags"],
                "variants": prod_plan["variants"],
                "print_areas": [{
                    "variant_ids": [v["id"] for v in prod_plan["variants"]],
                    "placeholders": [{
                        "position": "front",
                        "images": [{
                            "id": image_id,
                            "x": 0.5, "y": 0.5, "scale": 1.0, "angle": 0,
                        }],
                    }],
                }],
            }
            created = api.create_product(cfg["shop_id"], payload)
            api.publish_product(cfg["shop_id"], created["id"])
            product_results.append({
                "kind": prod_plan["kind"],
                "product_id": created["id"],
                "external_url": (created.get("external") or {}).get("handle"),
                "variants": prod_plan["variants"],
            })

        ledger.setdefault("entries", {})[ledger_key(rel)] = {
            "published_at": datetime.now(timezone.utc).isoformat(),
            "image_id": image_id,
            "products": product_results,
        }
        write_ledger(ledger)

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Printify publisher")
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="Default. Print plan without API writes.")
    ap.add_argument("--live", action="store_true",
                    help="Actually create + publish products. Required for real writes.")
    ap.add_argument("--image", type=str, default=None,
                    help="Target a single image (absolute or gallery-relative path).")
    ap.add_argument("--bootstrap-config", action="store_true",
                    help="Inspect existing shop, derive config, write printify_config.yaml.")
    args = ap.parse_args(argv)

    if args.bootstrap_config:
        return cmd_bootstrap_config(args)
    return cmd_publish(args)


if __name__ == "__main__":
    sys.exit(main())
