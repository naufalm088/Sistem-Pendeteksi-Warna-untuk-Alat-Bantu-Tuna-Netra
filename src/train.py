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
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from sklearn.metrics import f1_score

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
PREPARED_DIR = DATASET_DIR / "prepared"
IMAGES_DIR = DATASET_DIR / "images"
MODELS_DIR = BASE_DIR / "models"
FIGURES_DIR = BASE_DIR / "figures"

ALL_LABELS = [
    "black", "blue", "brown", "gold", "green", "grey",
    "orange", "pink", "purple", "red", "silver", "white", "yellow"
]
NUM_CLASSES = len(ALL_LABELS)

IMG_SIZE = 128
BATCH_SIZE = 16
NUM_EPOCHS = 20
LEARNING_RATE = 3e-4
BACKBONE_LR = 5e-5
NUM_WORKERS = 0
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class ColorDataset(Dataset):
    def __init__(self, csv_path, img_dir, transform=None):
        self.df = pd.read_csv(csv_path)
        self.img_dir = Path(img_dir)
        self.transform = transform
        self.label_columns = ALL_LABELS

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = self.img_dir / row["file_name"]
        img = Image.open(img_path).convert("RGB")

        if self.transform:
            img = self.transform(img)

        labels = torch.tensor(
            [row[col] for col in self.label_columns],
            dtype=torch.float32
        )
        return img, labels


def get_transforms(split="train"):
    if split == "train":
        return transforms.Compose([
            transforms.Resize((IMG_SIZE + 32, IMG_SIZE + 32)),
            transforms.RandomResizedCrop(IMG_SIZE, scale=(0.75, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    else:
        return transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])


def build_model():
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, 512),
        nn.ReLU(),
        nn.BatchNorm1d(512),
        nn.Dropout(p=0.2),
        nn.Linear(512, NUM_CLASSES),
    )
    return model


def compute_class_weights(csv_path):
    df = pd.read_csv(csv_path)
    total = len(df)
    weights = []
    for col in ALL_LABELS:
        pos = df[col].sum()
        neg = total - pos
        w = neg / max(pos, 1)
        weights.append(min(w, 10.0))
    return torch.tensor(weights, dtype=torch.float32)


def train_one_epoch(model, loader, criterion, optimizer):
    model.train()
    running_loss = 0.0
    all_preds = []
    all_targets = []

    for imgs, labels in loader:
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        running_loss += loss.item() * imgs.size(0)
        preds = (torch.sigmoid(outputs) > 0.5).cpu().numpy()
        all_preds.append(preds)
        all_targets.append(labels.cpu().numpy())

    all_preds = np.vstack(all_preds)
    all_targets = np.vstack(all_targets)
    epoch_loss = running_loss / len(loader.dataset)
    epoch_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    return epoch_loss, epoch_f1


def validate(model, loader, criterion):
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for imgs, labels in loader:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            outputs = model(imgs)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * imgs.size(0)
            preds = (torch.sigmoid(outputs) > 0.5).cpu().numpy()
            all_preds.append(preds)
            all_targets.append(labels.cpu().numpy())

    all_preds = np.vstack(all_preds)
    all_targets = np.vstack(all_targets)
    epoch_loss = running_loss / len(loader.dataset)
    epoch_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    return epoch_loss, epoch_f1


def plot_training_history(history, save_path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(history["train_loss"], label="Train Loss", color="#2196F3", linewidth=2)
    ax1.plot(history["val_loss"], label="Val Loss", color="#F44336", linewidth=2)
    ax1.set_title("Loss per Epoch", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(history["train_f1"], label="Train F1", color="#2196F3", linewidth=2)
    ax2.plot(history["val_f1"], label="Val F1", color="#F44336", linewidth=2)
    ax2.set_title("Macro F1-Score per Epoch", fontsize=13, fontweight="bold")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("F1-Score")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [PLOT] Disimpan: {save_path}")


def main():
    print("=" * 60)
    print("TRAINING - Sistem Pendeteksi Warna")
    print(f"Device: {DEVICE}")
    print("=" * 60)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    train_csv = PREPARED_DIR / "train_labels.csv"
    val_csv = PREPARED_DIR / "val_labels.csv"

    print("\n--- Step 1: Load Dataset ---")
    train_dataset = ColorDataset(train_csv, PREPARED_DIR / "train", get_transforms("train"))
    val_dataset = ColorDataset(val_csv, PREPARED_DIR / "val", get_transforms("val"))

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)

    print(f"  Train: {len(train_dataset)} gambar ({len(train_loader)} batch)")
    print(f"  Val  : {len(val_dataset)} gambar ({len(val_loader)} batch)")

    print("\n--- Step 2: Build Model ---")
    model = build_model().to(DEVICE)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Model: MobileNetV2 + Custom Head (512 hidden + BatchNorm)")
    print(f"  Total params    : {total_params:,}")
    print(f"  Trainable params: {trainable_params:,}")
    print(f"  Output classes  : {NUM_CLASSES}")

    print("\n--- Step 3: Setup Training ---")
    class_weights = compute_class_weights(train_csv).to(DEVICE)
    print(f"  Class weights: {dict(zip(ALL_LABELS, [f'{w:.1f}' for w in class_weights.tolist()]))}")

    criterion = nn.BCEWithLogitsLoss(pos_weight=class_weights)

    backbone_params = []
    head_params = []
    for name, param in model.named_parameters():
        if "classifier" in name:
            head_params.append(param)
        else:
            backbone_params.append(param)

    optimizer = torch.optim.AdamW([
        {"params": backbone_params, "lr": BACKBONE_LR},
        {"params": head_params, "lr": LEARNING_RATE},
    ], weight_decay=1e-4)

    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS, eta_min=1e-6)

    print(f"  Optimizer : AdamW (backbone_lr={BACKBONE_LR}, head_lr={LEARNING_RATE})")
    print(f"  Scheduler : CosineAnnealingLR")
    print(f"  Loss      : BCEWithLogitsLoss + class weights")
    print(f"  Epochs    : {NUM_EPOCHS}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Grad clip : 1.0")

    print(f"\n--- Step 4: Training ---")
    history = {"train_loss": [], "val_loss": [], "train_f1": [], "val_f1": []}
    best_val_f1 = 0.0
    best_epoch = 0
    patience = 8
    no_improve = 0
    start_time = time.time()

    for epoch in range(1, NUM_EPOCHS + 1):
        epoch_start = time.time()

        train_loss, train_f1 = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_f1 = validate(model, val_loader, criterion)
        scheduler.step()

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_f1"].append(train_f1)
        history["val_f1"].append(val_f1)

        epoch_time = time.time() - epoch_start
        marker = ""

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch
            no_improve = 0
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_f1": val_f1,
                "val_loss": val_loss,
                "labels": ALL_LABELS,
            }, MODELS_DIR / "best_model.pth")
            marker = " <-- BEST"
        else:
            no_improve += 1

        print(f"  Epoch {epoch:>2d}/{NUM_EPOCHS} | "
              f"Train Loss: {train_loss:.4f} F1: {train_f1:.4f} | "
              f"Val Loss: {val_loss:.4f} F1: {val_f1:.4f} | "
              f"{epoch_time:.1f}s{marker}")

        if no_improve >= patience:
            print(f"\n  Early stopping: no improvement for {patience} epochs")
            break

    total_time = time.time() - start_time
    print(f"\n  Training selesai dalam {total_time:.1f}s ({total_time/60:.1f} menit)")
    print(f"  Best model: Epoch {best_epoch}, Val F1: {best_val_f1:.4f}")
    print(f"  Model disimpan: {MODELS_DIR / 'best_model.pth'}")

    print("\n--- Tuning threshold per kelas (data validasi) ---")
    best_ckpt = torch.load(MODELS_DIR / "best_model.pth", map_location=DEVICE, weights_only=False)
    model.load_state_dict(best_ckpt["model_state_dict"])
    model.eval()
    probs_list, tgts_list = [], []
    with torch.no_grad():
        for imgs, labels in val_loader:
            probs_list.append(torch.sigmoid(model(imgs.to(DEVICE))).cpu().numpy())
            tgts_list.append(labels.numpy())
    P_arr = np.vstack(probs_list)
    T_arr = np.vstack(tgts_list).astype(int)
    thresholds = []
    for i, label in enumerate(ALL_LABELS):
        best_t, best_f = 0.5, 0.0
        for thr in np.arange(0.05, 0.96, 0.05):
            f = f1_score(T_arr[:, i], (P_arr[:, i] >= thr).astype(int), zero_division=0)
            if f > best_f:
                best_t, best_f = float(thr), f
        thresholds.append(best_t)
        print(f"  {label:>8s}: thr={best_t:.2f}  F1={best_f:.3f}")
    tuned_pred = (P_arr >= np.array(thresholds)).astype(int)
    base_pred = (P_arr > 0.5).astype(int)
    print(f"  Macro F1 (thr 0.5)   : {f1_score(T_arr, base_pred, average='macro', zero_division=0):.4f}")
    print(f"  Macro F1 (thr tuned) : {f1_score(T_arr, tuned_pred, average='macro', zero_division=0):.4f}")
    best_ckpt["thresholds"] = thresholds
    torch.save(best_ckpt, MODELS_DIR / "best_model.pth")
    print("  Threshold optimal disimpan di best_model.pth")

    print("\n--- Step 5: Plot Training History ---")
    plot_training_history(history, FIGURES_DIR / "training_history.png")

    torch.save(model.state_dict(), MODELS_DIR / "last_model.pth")
    print(f"  Last model disimpan: {MODELS_DIR / 'last_model.pth'}")

    print(f"\n{'='*60}")
    print("TRAINING SELESAI!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
