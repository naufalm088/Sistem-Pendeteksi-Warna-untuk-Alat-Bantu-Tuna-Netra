import os
import sys
import json
import tarfile
import csv
from collections import defaultdict, Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
COLOR_DIR = DATASET_DIR / "AI4_C_datasets-main" / "color_detection_dataset"
IMAGES_DIR = DATASET_DIR / "images"
JSON_PATH = COLOR_DIR / "AI4C_Fashion_Color_Dataset_2024-06-01_0.json"
TAR_FILES = [COLOR_DIR / f"col{i}.tar.gz" for i in range(1, 4)]
OUTPUT_CSV = DATASET_DIR / "labels.csv"

DROP_LABELS = {"beige", "multicoloured"}


def extract_tar_files():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    total_extracted = 0
    for tar_path in TAR_FILES:
        if not tar_path.exists():
            print(f"[SKIP] {tar_path.name} tidak ditemukan")
            continue
        print(f"[EXTRACT] {tar_path.name} ...")
        with tarfile.open(tar_path, "r:gz") as tar:
            members = [m for m in tar.getmembers() if m.isfile() and m.name.endswith(".jpg")]
            for member in members:
                member.name = os.path.basename(member.name)
                tar.extract(member, IMAGES_DIR)
                total_extracted += 1
        print(f"  -> {len(members)} gambar di-extract")
    print(f"[DONE] Total gambar di-extract: {total_extracted}")
    return total_extracted


def build_label_csv():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    cat_map = {c["id"]: c["label"] for c in data["categories"]}
    img_map = {img["id"]: img["file_name"] for img in data["images"]}

    img_labels = defaultdict(set)
    for ann in data["annotations"]:
        label = cat_map[ann["category_id"]]
        if label in DROP_LABELS:
            continue
        img_labels[ann["image_id"]].add(label)

    existing_files = set(os.listdir(IMAGES_DIR))

    rows = []
    skipped_no_file = 0
    skipped_no_label = 0

    for img_id, file_name in img_map.items():
        if file_name not in existing_files:
            skipped_no_file += 1
            continue
        labels = img_labels.get(img_id, set())
        if not labels:
            skipped_no_label += 1
            continue
        rows.append({
            "file_name": file_name,
            "labels": ",".join(sorted(labels))
        })

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_name", "labels"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[CSV] Disimpan ke: {OUTPUT_CSV}")
    print(f"  Total gambar valid: {len(rows)}")
    print(f"  Gambar tanpa file : {skipped_no_file}")
    print(f"  Gambar tanpa label (setelah drop): {skipped_no_label}")

    all_labels = []
    for row in rows:
        all_labels.extend(row["labels"].split(","))
    dist = Counter(all_labels)
    print(f"\n[DISTRIBUSI] Per kelas ({len(dist)} kelas):")
    for label, count in dist.most_common():
        print(f"  {label:>10s}: {count}")

    label_counts = Counter(len(row["labels"].split(",")) for row in rows)
    print(f"\n[MULTI-LABEL] Distribusi jumlah label per gambar:")
    for n, count in sorted(label_counts.items()):
        print(f"  {n} label: {count} gambar")

    return len(rows)


def main():
    print("=" * 60)
    print("EXTRACT DATASET - Sistem Pendeteksi Warna")
    print("=" * 60)

    for tar_path in TAR_FILES:
        if not tar_path.exists():
            print(f"[ERROR] File tidak ditemukan: {tar_path}")
            sys.exit(1)
    if not JSON_PATH.exists():
        print(f"[ERROR] JSON tidak ditemukan: {JSON_PATH}")
        sys.exit(1)

    print(f"\n--- Step 1: Extract gambar dari tar.gz ---")
    extract_tar_files()

    print(f"\n--- Step 2: Build label CSV ---")
    build_label_csv()

    print(f"\n{'=' * 60}")
    print("SELESAI!")
    print("=" * 60)


if __name__ == "__main__":
    main()
