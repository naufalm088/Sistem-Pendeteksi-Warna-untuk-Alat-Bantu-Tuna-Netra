import os
import csv
import shutil
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import torch
from torch.utils.data import Dataset
from torchvision import transforms
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
IMAGES_DIR = DATASET_DIR / "images"
LABELS_CSV = DATASET_DIR / "labels.csv"
PREPARED_DIR = DATASET_DIR / "prepared"
FIGURES_DIR = BASE_DIR / "figures"

IMG_SIZE = 224
RANDOM_SEED = 42

ALL_LABELS = [
    "black", "blue", "brown", "gold", "green", "grey",
    "orange", "pink", "purple", "red", "silver", "white", "yellow"
]

BASIC_COLOR_MAP = {
    "red": "merah", "orange": "merah", "pink": "merah",
    "blue": "biru", "purple": "biru",
    "green": "hijau",
    "yellow": "kuning", "gold": "kuning",
    "white": "putih", "silver": "putih",
    "black": "hitam", "grey": "hitam",
    "brown": "coklat",
}

BASIC_LABELS = ["merah", "biru", "hijau", "kuning", "putih", "hitam", "coklat"]


def load_labels():
    df = pd.read_csv(LABELS_CSV)
    df["label_list"] = df["labels"].apply(lambda x: x.split(","))
    return df


def verify_images(df):
    print("[VERIFY] Mengecek integritas gambar ...")
    valid_rows = []
    corrupt = 0
    for _, row in df.iterrows():
        img_path = IMAGES_DIR / row["file_name"]
        try:
            img = Image.open(img_path)
            img.verify()
            valid_rows.append(row)
        except Exception:
            corrupt += 1
    print(f"  Valid: {len(valid_rows)}, Corrupt/Error: {corrupt}")
    return pd.DataFrame(valid_rows)


def encode_multilabel(label_list, label_names):
    vec = [0] * len(label_names)
    for label in label_list:
        if label in label_names:
            idx = label_names.index(label)
            vec[idx] = 1
    return vec


def split_dataset(df, test_size=0.15, val_size=0.15):
    df["stratify_key"] = df["labels"]

    label_counts = df["stratify_key"].value_counts()
    rare_labels = label_counts[label_counts < 3].index
    df.loc[df["stratify_key"].isin(rare_labels), "stratify_key"] = "__rare__"

    train_val, test = train_test_split(
        df, test_size=test_size, random_state=RANDOM_SEED, stratify=df["stratify_key"]
    )

    train_val_counts = train_val["stratify_key"].value_counts()
    rare_labels_tv = train_val_counts[train_val_counts < 2].index
    train_val.loc[train_val["stratify_key"].isin(rare_labels_tv), "stratify_key"] = "__rare__"

    val_ratio = val_size / (1 - test_size)
    train, val = train_test_split(
        train_val, test_size=val_ratio, random_state=RANDOM_SEED, stratify=train_val["stratify_key"]
    )

    train = train.drop(columns=["stratify_key"])
    val = val.drop(columns=["stratify_key"])
    test = test.drop(columns=["stratify_key"])

    return train.reset_index(drop=True), val.reset_index(drop=True), test.reset_index(drop=True)


def save_split(df, split_name):
    split_dir = PREPARED_DIR / split_name
    split_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for _, row in df.iterrows():
        src = IMAGES_DIR / row["file_name"]
        dst = split_dir / row["file_name"]
        if not dst.exists():
            shutil.copy2(src, dst)
        vec = encode_multilabel(row["label_list"], ALL_LABELS)
        records.append({"file_name": row["file_name"], "labels": row["labels"], **{l: v for l, v in zip(ALL_LABELS, vec)}})

    records_df = pd.DataFrame(records)
    records_df.to_csv(PREPARED_DIR / f"{split_name}_labels.csv", index=False)
    return records_df


def plot_distribution(df, title, save_path):
    all_labels = []
    for labels in df["label_list"]:
        all_labels.extend(labels)
    counts = Counter(all_labels)
    ordered = [(l, counts.get(l, 0)) for l in ALL_LABELS]
    labels_sorted = [x[0] for x in ordered]
    values_sorted = [x[1] for x in ordered]

    color_map_plot = {
        "black": "#000000", "blue": "#2196F3", "brown": "#795548",
        "gold": "#FFD700", "green": "#4CAF50", "grey": "#9E9E9E",
        "orange": "#FF9800", "pink": "#E91E63", "purple": "#9C27B0",
        "red": "#F44336", "silver": "#C0C0C0", "white": "#EEEEEE",
        "yellow": "#FFEB3B",
    }
    colors = [color_map_plot.get(l, "#666") for l in labels_sorted]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(labels_sorted, values_sorted, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Warna")
    ax.set_ylabel("Jumlah")
    for bar, val in zip(bars, values_sorted):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2, str(val),
                ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [PLOT] Disimpan: {save_path}")


def plot_split_comparison(train_df, val_df, test_df, save_path):
    def count_labels(df):
        all_l = []
        for labels in df["label_list"]:
            all_l.extend(labels)
        return Counter(all_l)

    train_c = count_labels(train_df)
    val_c = count_labels(val_df)
    test_c = count_labels(test_df)

    x = np.arange(len(ALL_LABELS))
    width = 0.25

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(x - width, [train_c.get(l, 0) for l in ALL_LABELS], width, label="Train", color="#2196F3")
    ax.bar(x, [val_c.get(l, 0) for l in ALL_LABELS], width, label="Validasi", color="#FF9800")
    ax.bar(x + width, [test_c.get(l, 0) for l in ALL_LABELS], width, label="Test", color="#4CAF50")
    ax.set_xticks(x)
    ax.set_xticklabels(ALL_LABELS, rotation=45, ha="right")
    ax.set_title("Distribusi Warna per Split (Train / Validasi / Test)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Jumlah")
    ax.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [PLOT] Disimpan: {save_path}")


def plot_sample_images(df, save_path, n=12):
    fig, axes = plt.subplots(3, 4, figsize=(16, 12))
    samples = df.sample(n=min(n, len(df)), random_state=RANDOM_SEED)
    for idx, (ax, (_, row)) in enumerate(zip(axes.flatten(), samples.iterrows())):
        img_path = IMAGES_DIR / row["file_name"]
        img = Image.open(img_path).convert("RGB")
        ax.imshow(img)
        ax.set_title(row["labels"], fontsize=9)
        ax.axis("off")
    plt.suptitle("Contoh Gambar Dataset dengan Label Warna", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [PLOT] Disimpan: {save_path}")


def plot_preprocessing_demo(df, save_path):
    sample = df.iloc[0]
    img_path = IMAGES_DIR / sample["file_name"]
    img = Image.open(img_path).convert("RGB")
    img_resized = img.resize((IMG_SIZE, IMG_SIZE))

    img_np = np.array(img_resized).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    img_normalized = (img_np - mean) / std
    img_norm_display = (img_normalized - img_normalized.min()) / (img_normalized.max() - img_normalized.min())

    from PIL import ImageFilter
    img_gray = img_resized.convert("L")
    img_edges = img_gray.filter(ImageFilter.FIND_EDGES)

    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    axes[0].imshow(img)
    axes[0].set_title(f"Original ({img.size[0]}x{img.size[1]})")
    axes[0].axis("off")

    axes[1].imshow(img_resized)
    axes[1].set_title(f"Resized ({IMG_SIZE}x{IMG_SIZE})")
    axes[1].axis("off")

    axes[2].imshow(img_norm_display)
    axes[2].set_title("Normalized (ImageNet)")
    axes[2].axis("off")

    axes[3].imshow(img_edges, cmap="gray")
    axes[3].set_title("Edge Detection")
    axes[3].axis("off")

    plt.suptitle(f"Preprocessing Pipeline - Label: {sample['labels']}", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [PLOT] Disimpan: {save_path}")


def print_summary(train_df, val_df, test_df):
    print(f"\n{'='*60}")
    print("RINGKASAN DATA PREPARATION")
    print(f"{'='*60}")
    print(f"  Total gambar valid : {len(train_df) + len(val_df) + len(test_df)}")
    print(f"  Train              : {len(train_df)} ({len(train_df)/(len(train_df)+len(val_df)+len(test_df))*100:.1f}%)")
    print(f"  Validasi           : {len(val_df)} ({len(val_df)/(len(train_df)+len(val_df)+len(test_df))*100:.1f}%)")
    print(f"  Test               : {len(test_df)} ({len(test_df)/(len(train_df)+len(val_df)+len(test_df))*100:.1f}%)")
    print(f"  Jumlah kelas detail: {len(ALL_LABELS)}")
    print(f"  Jumlah kelas dasar : {len(BASIC_LABELS)}")
    print(f"  Ukuran gambar      : {IMG_SIZE}x{IMG_SIZE} px")
    print(f"  Normalisasi        : ImageNet (mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])")

    print(f"\n  Distribusi per split:")
    print(f"  {'Warna':>10s} | {'Train':>6s} | {'Val':>5s} | {'Test':>5s} | {'Total':>6s}")
    print(f"  {'-'*10}-+-{'-'*6}-+-{'-'*5}-+-{'-'*5}-+-{'-'*6}")

    def count_l(df):
        c = Counter()
        for labels in df["label_list"]:
            c.update(labels)
        return c

    tc, vc, tec = count_l(train_df), count_l(val_df), count_l(test_df)
    for l in ALL_LABELS:
        t, v, te = tc.get(l, 0), vc.get(l, 0), tec.get(l, 0)
        print(f"  {l:>10s} | {t:>6d} | {v:>5d} | {te:>5d} | {t+v+te:>6d}")


def main():
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    print("=" * 60)
    print("DATA PREPARATION - Sistem Pendeteksi Warna")
    print("=" * 60)

    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("\n--- Step 1: Load & Verify Data ---")
    df = load_labels()
    print(f"  Total data dari CSV: {len(df)}")
    df = verify_images(df)

    print("\n--- Step 2: Visualisasi Data ---")
    plot_distribution(df, "Distribusi Jumlah Citra per Kelas Warna (Dataset Lengkap)", FIGURES_DIR / "distribusi_warna.png")
    plot_sample_images(df, FIGURES_DIR / "contoh_gambar.png")

    print("\n--- Step 3: Split Dataset (70/15/15) ---")
    train_df, val_df, test_df = split_dataset(df, test_size=0.15, val_size=0.15)
    print(f"  Train: {len(train_df)}, Validasi: {len(val_df)}, Test: {len(test_df)}")

    print("\n--- Step 4: Simpan Split + Copy Gambar ---")
    save_split(train_df, "train")
    save_split(val_df, "val")
    save_split(test_df, "test")
    print("  [DONE] Data tersimpan di dataset/prepared/")

    print("\n--- Step 5: Visualisasi Split ---")
    plot_split_comparison(train_df, val_df, test_df, FIGURES_DIR / "distribusi_per_split.png")
    plot_preprocessing_demo(train_df, FIGURES_DIR / "preprocessing_pipeline.png")

    print_summary(train_df, val_df, test_df)

    print(f"\n{'='*60}")
    print("DATA PREPARATION SELESAI!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
