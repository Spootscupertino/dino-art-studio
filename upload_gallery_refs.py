"""One-off: upload best MJ/training-ref T. rex images to Discord CDN
and store them in sref_urls.json as gallery_best/ entries.
"""
import sys, time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from upload_refs import upload_to_discord, load_webhook_url, load_sref, save_sref

SPECIES = "Tyrannosaurus rex"
LABEL_PREFIX = "gallery_best"

FOLDERS = [
    ROOT / "assets/gallery/flux/training_refs/tyrannosaurus/v5_full_body_action",
    ROOT / "assets/gallery/flux/training_refs/tyrannosaurus/corrected_mj",
    ROOT / "assets/gallery/flux/training_refs/tyrannosaurus/paleoart",
    ROOT / "assets/gallery/flux/training_refs/tyrannosaurus/extremes_macro",
    ROOT / "assets/gallery/flux/training_refs/tyrannosaurus/v5_mouth_macro",
    ROOT / "assets/gallery/flux/training_refs/tyrannosaurus/biomech_mouth",
    ROOT / "assets/gallery/flux/training_refs/tyrannosaurus/v5_hindfoot_claw",
    ROOT / "assets/gallery/flux/training_refs/tyrannosaurus/v5_forelimb_hand",
]


def main():
    webhook_url = load_webhook_url()
    sref = load_sref()
    existing_labels = {
        e.get("label", "")
        for e in sref.get(SPECIES, [])
        if isinstance(e, dict)
    }

    uploaded = 0
    skipped = 0

    for folder in FOLDERS:
        if not folder.exists():
            print("Skipping missing folder: %s" % folder.name)
            continue
        imgs = sorted(folder.glob("*.png")) + sorted(folder.glob("*.jpg")) + sorted(folder.glob("*.jpeg"))
        if not imgs:
            print("No images in %s" % folder.name)
            continue
        print("\n[%s] — %d images" % (folder.name, len(imgs)))
        for img in imgs:
            label = "%s/%s/%s" % (LABEL_PREFIX, folder.name, img.name)
            if label in existing_labels:
                print("  skip: %s" % img.name)
                skipped += 1
                continue
            print("  uploading: %s" % img.name)
            url = upload_to_discord(webhook_url, img, "gallery_best")
            if url:
                sref.setdefault(SPECIES, []).append({"label": label, "url": url})
                existing_labels.add(label)
                save_sref(sref)
                print("    -> %s..." % url[:70])
                uploaded += 1
            else:
                print("    FAILED")
            time.sleep(1.5)

    print("\nDone: %d uploaded, %d skipped" % (uploaded, skipped))
    gallery = [e for e in sref.get(SPECIES, []) if isinstance(e, dict) and e.get("label", "").startswith("gallery_best/")]
    print("T. rex gallery_best refs in sref_urls.json: %d" % len(gallery))


if __name__ == "__main__":
    main()
