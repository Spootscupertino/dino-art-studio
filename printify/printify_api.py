"""Thin wrapper around the Printify REST v1 API.

Stdlib-only (urllib) so it runs anywhere — no `requests` dependency required.

Auth: reads PRINTIFY_API_KEY (preferred) or PRINTIFY_API_TOKEN from os.environ.
Surfaces 4xx errors with the request payload visible. Never silently retries.
"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

API_BASE = "https://api.printify.com/v1"
USER_AGENT = "jurassinkart-printify-publisher/0.1"


class PrintifyError(RuntimeError):
    def __init__(self, status: int, method: str, url: str, body: Any, payload: Any = None):
        self.status = status
        self.method = method
        self.url = url
        self.body = body
        self.payload = payload
        super().__init__(
            f"Printify API {status} on {method} {url}\n"
            f"  request payload: {json.dumps(payload)[:1000] if payload is not None else '(none)'}\n"
            f"  response body  : {json.dumps(body)[:2000] if not isinstance(body, str) else body[:2000]}"
        )


def _load_env_file(env_path: Path) -> None:
    """Tiny .env loader (no python-dotenv dependency)."""
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


def get_token() -> str:
    # Auto-load .env from repo root if present.
    repo_root = Path(__file__).resolve().parent.parent
    _load_env_file(repo_root / ".env")
    tok = os.environ.get("PRINTIFY_API_KEY") or os.environ.get("PRINTIFY_API_TOKEN")
    if not tok:
        raise RuntimeError(
            "PRINTIFY_API_KEY (or PRINTIFY_API_TOKEN) not set. Check .env at repo root."
        )
    return tok


def _request(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json_body: Any = None,
    raw_body: Optional[bytes] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    timeout: int = 60,
) -> Any:
    url = path if path.startswith("http") else f"{API_BASE}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    data: Optional[bytes] = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json;charset=utf-8"
    elif raw_body is not None:
        data = raw_body

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            text = body.decode("utf-8", errors="replace")
            try:
                return json.loads(text) if text else None
            except json.JSONDecodeError:
                return text
    except urllib.error.HTTPError as e:
        raw = e.read()
        text = raw.decode("utf-8", errors="replace") if raw else ""
        try:
            body = json.loads(text)
        except Exception:
            body = text
        raise PrintifyError(e.code, method, url, body, payload=json_body) from None
    except urllib.error.URLError as e:
        raise PrintifyError(0, method, url, str(e), payload=json_body) from None


# ---------- Public surface ----------

_shop_cache: Dict[str, Any] = {}


def list_shops() -> List[Dict[str, Any]]:
    if "shops" not in _shop_cache:
        _shop_cache["shops"] = _request("GET", "/shops.json")
    return _shop_cache["shops"]


def get_shop_id() -> int:
    """Resolve shop id. Prefer PRINTIFY_SHOP_ID env, else first Etsy shop, else first shop."""
    env_id = os.environ.get("PRINTIFY_SHOP_ID")
    if env_id:
        try:
            return int(env_id)
        except ValueError:
            pass
    shops = list_shops()
    if not shops:
        raise RuntimeError("No Printify shops linked to this token.")
    for s in shops:
        if (s.get("sales_channel") or "").lower() == "etsy":
            return int(s["id"])
    return int(shops[0]["id"])


def list_products(shop_id: int, *, limit: int = 50) -> List[Dict[str, Any]]:
    """Paginate through all products in a shop."""
    out: List[Dict[str, Any]] = []
    page = 1
    while True:
        resp = _request(
            "GET",
            f"/shops/{shop_id}/products.json",
            params={"limit": limit, "page": page},
        )
        data = resp.get("data", []) if isinstance(resp, dict) else []
        out.extend(data)
        last_page = (resp or {}).get("last_page") or 1
        current_page = (resp or {}).get("current_page") or page
        if current_page >= last_page or not data:
            break
        page += 1
    return out


def get_product(shop_id: int, product_id: str) -> Dict[str, Any]:
    return _request("GET", f"/shops/{shop_id}/products/{product_id}.json")


def get_blueprint(blueprint_id: int) -> Dict[str, Any]:
    return _request("GET", f"/catalog/blueprints/{blueprint_id}.json")


def get_blueprint_variants(blueprint_id: int, print_provider_id: int) -> Dict[str, Any]:
    return _request(
        "GET",
        f"/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json",
    )


def get_provider_shipping(blueprint_id: int, print_provider_id: int) -> Dict[str, Any]:
    return _request(
        "GET",
        f"/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/shipping.json",
    )


def upload_image(file_path: str) -> Dict[str, Any]:
    """Upload image to Printify Image Library via base64 contents."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(file_path)
    data_b64 = b64encode(p.read_bytes()).decode("ascii")
    payload = {"file_name": p.name, "contents": data_b64}
    return _request("POST", "/uploads/images.json", json_body=payload)


def create_product(shop_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return _request("POST", f"/shops/{shop_id}/products.json", json_body=payload)


def get_etsy_shipping_profiles(shop_id: int) -> Any:
    """Return the list of Etsy shipping profiles/templates for this shop.

    Printify exposes this via two possible endpoints — we try the newer one
    first and fall back to the legacy path so the caller doesn't need to care.
    The raw response is returned unchanged so the user can inspect it with
    ``--list-shipping``.
    """
    try:
        return _request("GET", f"/shops/{shop_id}/shipping_profiles.json")
    except PrintifyError as e:
        if e.status == 404:
            # Fall back to legacy endpoint.
            return _request("GET", f"/shops/{shop_id}/shipping.json")
        raise


def publish_product(
    shop_id: int,
    product_id: str,
    *,
    title: bool = True,
    description: bool = True,
    images: bool = True,
    variants: bool = True,
    tags: bool = True,
    keyFeatures: bool = True,
    shipping_template: bool = True,
    shipping_profile_id: Optional[int] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "title": title,
        "description": description,
        "images": images,
        "variants": variants,
        "tags": tags,
        "keyFeatures": keyFeatures,
        "shipping_template": shipping_template,
    }
    if shipping_profile_id is not None:
        # Printify uses "shipping_template" as the key for the Etsy profile ID
        # when a numeric ID is supplied (overrides the boolean flag above).
        payload["shipping_template"] = shipping_profile_id
    return _request(
        "POST",
        f"/shops/{shop_id}/products/{product_id}/publish.json",
        json_body=payload,
    )


# ---------- CLI smoke test ----------

if __name__ == "__main__":
    # Minimal sanity probe: list shops, count products in resolved shop.
    try:
        shops = list_shops()
        print(f"Shops linked to token: {len(shops)}")
        for s in shops:
            print(f"  - id={s.get('id')} title={s.get('title')!r} channel={s.get('sales_channel')}")
        sid = get_shop_id()
        print(f"Resolved shop_id: {sid}")
        prods = list_products(sid)
        print(f"Existing products in shop: {len(prods)}")
        for p in prods[:5]:
            print(
                f"  - {p.get('id')} blueprint={p.get('blueprint_id')} "
                f"provider={p.get('print_provider_id')} title={p.get('title')!r}"
            )
    except PrintifyError as e:
        print(f"API error: {e}", file=sys.stderr)
        sys.exit(1)
