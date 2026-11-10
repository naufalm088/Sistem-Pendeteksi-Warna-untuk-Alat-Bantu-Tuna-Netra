import os
import sys
import time
from pathlib import Path
from collections import Counter

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

import numpy as np
import pandas as pd
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import torch
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score, hamming_loss, accuracy_score

from train import (BASE_DIR, PREPARED_DIR, MODELS_DIR, FIGURES_DIR,
                   ColorDataset, get_transforms, build_model, ALL_LABELS, NUM_CLASSES)

BASIC_GROUPS = {
    "merah": ["red", "orange", "pink"],
    "biru": ["blue", "purple"],
    "hijau": ["green"],
    "kuning": ["yellow", "gold"],
    "putih": ["white", "silver"],
    "hitam": ["black", "grey"],
    "coklat": ["brown"],
}
BASIC_LABELS = list(BASIC_GROUPS.keys())

RESULTS_DIR = BASE_DIR / "results"

LABEL_HEX = {
    "black": "#000000", "blue": "#2196F3", "brown": "#795548", "gold": "#DAA520",
    "green": "#4CAF50", "grey": "#9E9E9E", "orange": "#FF9800", "pink": "#E91E63",
    "purple": "#9C27B0", "red": "#F44336", "silver": "#C0C0C0", "white": "#EEEEEE",
    "yellow": "#FFEB3B",
}
BASIC_HEX = {
    "merah": "#F44336", "biru": "#2196F3", "hijau": "#4CAF50", "kuning": "#FFEB3B",
    "putih": "#EEEEEE", "hitam": "#212121", "coklat": "#795548",
}


def collect_predictions(model, loader, device):
    model.eval()
    probs, tgts = [], []
    total_time = 0.0
    n_imgs = 0
    with torch.no_grad():
        for imgs, labels in loader:
            t0 = time.time()
            p = torch.sigmoid(model(imgs.to(device))).cpu().numpy()
            total_time += time.time() - t0
            n_imgs += imgs.size(0)
            probs.append(p)
            tgts.append(labels.numpy())
    return np.vstack(probs), np.vstack(tgts).astype(int), total_time / max(n_imgs, 1)


def tune_thresholds(P, T):
    thresholds = []
    for i in range(P.shape[1]):
        p, t = P[:, i], T[:, i]
        best_t, best_f = 0.5, 0.0
        for thr in np.arange(0.05, 0.96, 0.05):
            f = f1_score(t, (p >= thr).astype(int), zero_division=0)
            if f > best_f:
                best_t, best_f = float(thr), f
        thresholds.append(best_t)
    return np.array(thresholds)


def group_matrix(T):
    return np.stack(
        [T[:, [ALL_LABELS.index(m) for m in members]].max(axis=1) for members in BASIC_GROUPS.values()],
        axis=1,
    )


def group_probs(P):
    return np.stack(
        [P[:, [ALL_LABELS.index(m) for m in members]].max(axis=1) for members in BASIC_GROUPS.values()],
        axis=1,
    )


def metrics_block(T, P, labels, thresholds):
    pred = (P >= thresholds).astype(int)
    macro = f1_score(T, pred, average="macro", zero_division=0)
    micro = f1_score(T, pred, average="micro", zero_division=0)
    weighted = f1_score(T, pred, average="weighted", zero_division=0)
    hamming = hamming_loss(T, pred)
    subset = accuracy_score(T, pred)
    lines = []
    lines.append(f"  Macro-F1    : {macro:.4f}")
    lines.append(f"  Micro-F1    : {micro:.4f}")
    lines.append(f"  Weighted-F1 : {weighted:.4f}")
    lines.append(f"  Hamming Loss: {hamming:.4f}")
    lines.append(f"  Subset Acc  : {subset:.4f}")
    per_class = []
    for j, lab in enumerate(labels):
        prec = precision_score(T[:, j], pred[:, j], zero_division=0)
        rec = recall_score(T[:, j], pred[:, j], zero_division=0)
        f1 = f1_score(T[:, j], pred[:, j], zero_division=0)
        sup = int(T[:, j].sum())
        per_class.append((lab, prec, rec, f1, sup, thresholds[j]))
    return {
        "pred": pred, "macro": macro, "micro": micro, "weighted": weighted,
        "hamming": hamming, "subset": subset, "per_class": per_class,
    }


def fmt_class_table(per_class, header):
    lines = [header]
    lines.append(f"  {'Label':<8s} | {'Prec':>6s} | {'Rec':>6s} | {'F1':>6s} | {'Support':>7s} | {'Thr':>5s}")
    lines.append("  " + "-" * 52)
    for lab, prec, rec, f1, sup, thr in per_class:
        lines.append(f"  {lab:<8s} | {prec:>6.3f} | {rec:>6.3f} | {f1:>6.3f} | {sup:>7d} | {thr:>5.2f}")
    return lines


def plot_detail_f1(details, save_path):
    labels = [f"{p[0]}" for _, p in [(None, pc) for pc in details]]
    labels = [pc[0] for pc in details]
    f1s = [pc[3] for pc in details]
    colors = [LABEL_HEX.get(l, "#666") for l in labels]
    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(labels, f1s, color=colors, edgecolor="black", linewidth=0.5)
    ax.axhline(np.mean(f1s), color="#F44336", linestyle="--", linewidth=1.5, label=f"Macro F1 = {np.mean(f1s):.3f}")
    for bar, val in zip(bars, f1s):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01, f"{val:.2f}",
                ha="center", va="bottom", fontsize=9)
    ax.set_title("F1-Score per Kelas Warna (Data Test)", fontsize=13, fontweight="bold")
    ax.set_ylabel("F1-Score")
    ax.set_ylim(0, 1.0)
    ax.legend()
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_basic_f1(basics, save_path):
    labels = [pc[0] for pc in basics]
    f1s = [pc[3] for pc in basics]
    colors = [BASIC_HEX.get(l, "#666") for l in labels]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(labels, f1s, color=colors, edgecolor="black", linewidth=0.5)
    ax.axhline(np.mean(f1s), color="#F44336", linestyle="--", linewidth=1.5, label=f"Macro F1 = {np.mean(f1s):.3f}")
    for bar, val in zip(bars, f1s):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01, f"{val:.2f}",
                ha="center", va="bottom", fontsize=9)
    ax.set_title("F1-Score per Kelompok Warna Dasar (Data Test)", fontsize=13, fontweight="bold")
    ax.set_ylabel("F1-Score")
    ax.set_ylim(0, 1.0)
    ax.legend()
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_sample_predictions(df, pred_detail, test_dir, img_size, save_path, n=8):
    fig, axes = plt.subplots(2, 4, figsize=(16, 9))
    samples = df.iloc[:n]
    for idx, (ax_primary, (i, row)) in enumerate(zip(axes.flatten(), samples.iterrows())):
        img_path = Path(test_dir) / row["file_name"]
        img = Image.open(img_path).convert("RGB")
        img_resized = img.resize((img_size, img_size))
        pred_labels = [ALL_LABELS[j] for j in range(len(ALL_LABELS)) if pred_detail[i][j] == 1]
        pred_text = ", ".join(pred_labels) if pred_labels else "(tidak ada)"
        ax_primary.imshow(img_resized)
        ax_primary.set_title(f"TRUE: {row['labels']}\nPRED: {pred_text}", fontsize=9)
        ax_primary.axis("off")
    plt.suptitle("Contoh Prediksi pada Data Test", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


def main():
    print("=" * 60)
    print("EVALUASI - Sistem Pendeteksi Warna")
    print("=" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    ckpt = torch.load(MODELS_DIR / "best_model.pth", map_location="cpu", weights_only=False)
    print(f"Checkpoint -> epoch: {ckpt.get('epoch')} | val_f1: {ckpt.get('val_f1'):.4f}")
    thr_detail_val = np.array(ckpt.get("thresholds", [0.5] * NUM_CLASSES))
    print(f"Threshold detail (dari validasi): {thr_detail_val}")

    model = build_model()
    model.load_state_dict(ckpt["model_state_dict"])
    model = model.to(device)

    val_csv = PREPARED_DIR / "val_labels.csv"
    test_csv = PREPARED_DIR / "test_labels.csv"
    test_dir = PREPARED_DIR / "test"

    val_ds = ColorDataset(val_csv, PREPARED_DIR / "val", get_transforms("val"))
    test_ds = ColorDataset(test_csv, test_dir, get_transforms("val"))
    val_loader = DataLoader(val_ds, batch_size=16, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=16, shuffle=False)

    print(f"\nMemproses data validasi ({len(val_ds)}) & test ({len(test_ds)}) ...")
    P_val, T_val, _ = collect_predictions(model, val_loader, device)
    P_test, T_test, per_img_time = collect_predictions(model, test_loader, device)
    print(f"Selesai. Inferensi rata-rata: {per_img_time*1000:.1f} ms/gambar")

    thr_basic_val = tune_thresholds(group_probs(P_val), group_matrix(T_val))
    thr_basic_val = np.clip(thr_basic_val, 0.3, 0.8)

    detail = metrics_block(T_test, P_test, ALL_LABELS, thr_detail_val)
    basic = metrics_block(group_matrix(T_test), group_probs(P_test), BASIC_LABELS, thr_basic_val)

    report_lines = []
    report_lines.append("=" * 64)
    report_lines.append("LAPORAN EVALUASI - Sistem Pendeteksi Warna")
    report_lines.append("=" * 64)
    report_lines.append(f"Data test        : {len(test_ds)} gambar")
    report_lines.append(f"Data validasi    : {len(val_ds)} gambar")
    report_lines.append(f"Jumlah kelas     : {NUM_CLASSES} (detail) / {len(BASIC_LABELS)} (dasar)")
    report_lines.append(f"Inferensi        : {per_img_time*1000:.1f} ms/gambar")
    report_lines.append("")
    report_lines.append("[A] MODE DETAIL (13 kelas warna)")
    report_lines.extend(fmt_class_table(detail["per_class"], ""))
    report_lines.append("")
    report_lines.append(f"  Macro-F1    : {detail['macro']:.4f}")
    report_lines.append(f"  Micro-F1    : {detail['micro']:.4f}")
    report_lines.append(f"  Weighted-F1 : {detail['weighted']:.4f}")
    report_lines.append(f"  Hamming Loss: {detail['hamming']:.4f}")
    report_lines.append("")
    report_lines.append("[B] MODE DASAR (7 kelompok warna)")
    report_lines.extend(fmt_class_table(basic["per_class"], ""))
    report_lines.append("")
    report_lines.append(f"  Macro-F1    : {basic['macro']:.4f}")
    report_lines.append(f"  Micro-F1    : {basic['micro']:.4f}")
    report_lines.append(f"  Weighted-F1 : {basic['weighted']:.4f}")
    report_lines.append(f"  Hamming Loss: {basic['hamming']:.4f}")
    report_lines.append("")
    report_lines.append("[C] Sklearn classification report (detail)")
    report_lines.append(classification_report(T_test, detail["pred"], target_names=ALL_LABELS, digits=3, zero_division=0))
    report_path = RESULTS_DIR / "evaluation_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\n[REPORT] Disimpan: {report_path}")

    print("\n[A] DETAIL (13 kelas):")
    for line in fmt_class_table(detail["per_class"], ""):
        print(line)
    print(f"  Macro-F1 {detail['macro']:.4f} | Micro-F1 {detail['micro']:.4f} | Weighted-F1 {detail['weighted']:.4f} | Hamming {detail['hamming']:.4f}")

    print("\n[B] DASAR (7 kelompok):")
    for line in fmt_class_table(basic["per_class"], ""):
        print(line)
    print(f"  Macro-F1 {basic['macro']:.4f} | Micro-F1 {basic['micro']:.4f} | Weighted-F1 {basic['weighted']:.4f} | Hamming {basic['hamming']:.4f}")

    print("\n[METRICS GLOBAL]")
    print(f"  Detail: macro={detail['macro']:.4f}  micro={detail['micro']:.4f}  weighted={detail['weighted']:.4f}")
    print(f"  Dasar : macro={basic['macro']:.4f}  micro={basic['micro']:.4f}  weighted={basic['weighted']:.4f}")

    print("\n[FIGURE] Membuat grafik evaluasi ...")
    plot_detail_f1(detail["per_class"], FIGURES_DIR / "eval_detail_f1.png")
    plot_basic_f1(basic["per_class"], FIGURES_DIR / "eval_basic_f1.png")

    test_df = pd.read_csv(test_csv)
    plot_sample_predictions(test_df, detail["pred"], test_dir, 160, FIGURES_DIR / "eval_sample_predictions.png")
    for p in ["eval_detail_f1.png", "eval_basic_f1.png", "eval_sample_predictions.png"]:
        print(f"  -> figures/{p}")

    print("\n" + "=" * 60)
    print("EVALUASI SELESAI!")
    print("=" * 60)


if __name__ == "__main__":
    main()
