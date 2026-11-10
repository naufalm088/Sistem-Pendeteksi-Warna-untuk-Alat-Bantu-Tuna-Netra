# ColorSense - Sistem Pendeteksi Warna untuk Alat Bantu Tuna Netra

ColorSense adalah aplikasi web pendeteksi warna yang dirancang sebagai alat bantu bagi penyandang tuna netra. Pengguna cukup mengarahkan kamera atau mengunggah gambar pakaian/objek, lalu hasil deteksinya dibacakan melalui suara dalam Bahasa Indonesia.

Kalimat keluaran suara dibuat sederhana dan alami, misalnya:

> "Warna dominan: merah, keyakinan 92 persen."

## Fitur

- **Mode Kamera** - analisis warna objek secara langsung melalui webcam, dengan opsi deteksi otomatis setiap 3 detik
- **Mode Unggah** - analisis gambar dari perangkat (klik atau seret file)
- **Dua mode hasil**
  - Mode *Dasar*: 7 kelompok warna (merah, biru, hijau, kuning, putih, hitam, coklat)
  - Mode *Detail*: 13 warna spesifik (termasuk oranye, ungu, emas, perak, dst.)
- **Keluaran suara (TTS)** Bahasa Indonesia, dengan opsi bicara otomatis
- **Aksesibilitas**: kontras tinggi, dukungan pembaca layar, target sentuh besar, dan pintasan keyboard
- **Tema terang/gelap**

Pintasan keyboard: `Spasi` (ambil gambar), `K` (mode kamera), `U` (unggah), `T` (dengarkan hasil), `D` (ganti tema).

## Hasil Model

Model utama adalah **MobileNetV2** (transfer learning ImageNet) dengan kepala klasifikasi multi-label (sigmoid), dilatih pada dataset AI4C Fashion Color. Hasil pada data uji (360 gambar):

| Mode | Macro-F1 | Micro-F1 | Weighted-F1 | Kecepatan inferensi |
|---|---|---|---|---|
| Dasar (7 kelompok) | **0,767** | 0,788 | 0,790 | 9,7 ms/gambar (CPU) |
| Detail (13 kelas) | 0,622 | 0,764 | 0,755 | 9,7 ms/gambar (CPU) |

## Cara Menjalankan Aplikasi

1. Kloning repositori ini:
   ```bash
   git clone https://github.com/naufalm088/Sistem-Pendeteksi-Warna-untuk-Alat-Bantu-Tuna-Netra.git
   cd Sistem-Pendeteksi-Warna-untuk-Alat-Bantu-Tuna-Netra
   ```
2. (Direkomendasikan) Buat virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```
3. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
   > Khusus pengguna CPU yang ingin menghemat ruang disk, gunakan build CPU:
   > ```bash
   > pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   > ```
4. Jalankan aplikasi:
   ```bash
   python app.py
   ```
5. Buka `http://127.0.0.1:8001` di browser.

Bobot model terbaik sudah tersedia di `models/best_model.pth`, jadi aplikasi dapat langsung digunakan tanpa training ulang.

## Melatih Ulang Model (opsional)

1. Unduh dataset di repositori [AI4_C_datasets](https://github.com/datable-be/AI4_C_datasets) (dataset AI4C Fashion Color, rilis 2024). Letakkan isi `color_detection_dataset/` di folder `dataset/AI4_C_datasets-main/color_detection_dataset/`.
2. Jalankan tahap pipeline secara berurutan:
   ```bash
   python src/extract_dataset.py
   python src/prepare_data.py
   python src/train.py
   python src/evaluate.py
   ```
3. Hasil angka evaluasi tersimpan di `results/evaluation_report.txt`, grafik di `figures/`, dan bobot terbaik di `models/best_model.pth`.

## Struktur Proyek

```
.
├── app.py               # server Flask + inferensi
├── templates/
│   └── index.html        # antarmuka web
├── static/
│   ├── css/style.css     # tema terang/gelap
│   └── js/main.js        # logika kamera, unggah, TTS
├── src/
│   ├── extract_dataset.py  # ekstraksi arsip + labels.csv
│   ├── prepare_data.py     # split 70/15/15 + pra-pemrosesan
│   ├── train.py            # pelatihan MobileNetV2
│   └── evaluate.py         # evaluasi data uji
├── models/
│   └── best_model.pth    # bobot + ambang batas kedua mode
├── figures/              # grafik dan figur untuk laporan
├── results/              # laporan evaluasi otomatis
└── scripts/              # skrip pendukung
```

## Tim

Kelompok Malam B - Project Akhir Pengolahan Citra Digital, STT Wastukancana Purwakarta

- Ananda Nur Hafidz
- Mutiara Shella Widiaanggraeni
- Mutiara Shelly Widia Anggraeni

## Atribusi Dataset

Dataset AI4C Fashion Color (2024) digunakan sebagai data utama pelatihan model:
https://github.com/datable-be/AI4_C_datasets
