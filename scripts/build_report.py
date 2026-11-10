from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Laporan ColorSense - Pendeteksi Warna untuk Alat Bantu Tuna Netra.docx"

RED = RGBColor(0xC0, 0x00, 0x00)
BLACK = RGBColor(0, 0, 0)
FONT = "Times New Roman"


def num_id(n):
    return f"{n:,}".replace(",", ".")


def num_dec(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")

CENTER = WD_ALIGN_PARAGRAPH.CENTER
JUSTIFY = WD_ALIGN_PARAGRAPH.JUSTIFY
LEFT = WD_ALIGN_PARAGRAPH.LEFT

FIG_TITLE = {
    1: "Halaman repositori GitHub AI4_C_datasets",
    2: "Isi folder dataset hasil ekstraksi",
    3: "Contoh gambar dari dataset",
    4: "Distribusi jumlah gambar untuk setiap label warna",
    5: "Distribusi jumlah gambar pada data latih, validasi, dan uji",
    6: "Alur tahapan pra-pemrosesan data",
    7: "Kurva loss dan macro-F1 selama pelatihan model",
    8: "F1-score setiap kelas pada mode detail (data uji)",
    9: "F1-score setiap kelas pada mode dasar (data uji)",
    10: "Contoh hasil prediksi model pada beberapa gambar uji",
    11: "Tampilan awal aplikasi web ColorSense",
    12: "Mode kamera dengan hasil deteksi mode dasar",
    13: "Hasil deteksi mode detail beserta bar kemungkinan warna",
}

FIG_FILE = {
    3: "figures\\contoh_gambar.png",
    4: "figures\\distribusi_warna.png",
    5: "figures\\distribusi_per_split.png",
    6: "figures\\preprocessing_pipeline.png",
    7: "figures\\training_history.png",
    8: "figures\\eval_detail_f1.png",
    9: "figures\\eval_basic_f1.png",
    10: "figures\\eval_sample_predictions.png",
}

FIG_INSTR = {
    1: "Buka https://github.com/datable-be/AI4_C_datasets di browser, tangkap layar halaman utama repositori (README dan daftar file), lalu sisipkan di sini (lebar sekitar 14 cm).",
    2: "Buka folder 'dataset' di File Explorer (folder project ini), tangkap layar isi folder (folder images + file JSON), lalu sisipkan di sini.",
    3: "Sisipkan file figures\\contoh_gambar.png dari folder project (Insert > Pictures > This Device), lebar sekitar 14 cm.",
    4: "Sisipkan file figures\\distribusi_warna.png.",
    5: "Sisipkan file figures\\distribusi_per_split.png.",
    6: "Sisipkan file figures\\preprocessing_pipeline.png.",
    7: "Sisipkan file figures\\training_history.png.",
    8: "Sisipkan file figures\\eval_detail_f1.png.",
    9: "Sisipkan file figures\\eval_basic_f1.png.",
    10: "Sisipkan file figures\\eval_sample_predictions.png.",
    11: "Jalankan aplikasi (python app.py), buka http://127.0.0.1:8001, tangkap layar tampilan awal lengkap dengan tombol Kamera, Unggah Gambar, dan panel Hasil Deteksi, lalu sisipkan di sini.",
    12: "Aktifkan tombol Kamera, arahkan objek berwarna (buku/pakaian), klik Ambil & Deteksi, tangkap layar saat hasil mode Dasar tampil, lalu sisipkan di sini.",
    13: "Pindah ke mode Detail pada panel Hasil, tangkap layar hasil dengan bar kemungkinan warna, lalu sisipkan di sini.",
}

TABLE_TITLES = [
    "Pengguna sistem dan keperluannya",
    "Struktur data dataset AI4C Fashion Color",
    "Distribusi jumlah gambar untuk setiap label warna",
    "Jumlah label warna per gambar (multi-label)",
    "Pemetaan kelas detail ke kelompok warna dasar",
    "Pembagian data latih, validasi, dan uji",
    "Isu kualitas data dan penanganannya",
    "Arsitektur model deteksi warna",
    "Hyperparameter pelatihan model",
    "Bobot kelas (pos_weight) data latih",
    "Hasil evaluasi mode detail per kelas",
    "Hasil evaluasi ringkas mode detail dan mode dasar",
    "Hasil evaluasi mode dasar per kelas",
    "Fitur aplikasi web ColorSense",
]


def setup(doc):
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(12)
    normal.font.color.rgb = BLACK
    normal.paragraph_format.space_after = Pt(6)

    h1 = doc.styles["Heading 1"]
    h1.font.name = FONT
    h1.font.size = Pt(14)
    h1.font.bold = True
    h1.font.color.rgb = BLACK
    h1.paragraph_format.alignment = CENTER
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(14)

    h2 = doc.styles["Heading 2"]
    h2.font.name = FONT
    h2.font.size = Pt(12)
    h2.font.bold = True
    h2.font.color.rgb = BLACK
    h2.paragraph_format.alignment = LEFT
    h2.paragraph_format.space_before = Pt(10)
    h2.paragraph_format.space_after = Pt(6)

    section = doc.sections[0]
    section.left_margin = Cm(4)
    section.right_margin = Cm(3)
    section.top_margin = Cm(3)
    section.bottom_margin = Cm(3)

    footer = section.footer.paragraphs[0]
    footer.alignment = CENTER
    run = footer.add_run()
    run.font.name = FONT
    run.font.size = Pt(10)
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.text = "PAGE"
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)

    settings = doc.settings.element
    uf = OxmlElement("w:updateFields")
    uf.set(qn("w:val"), "true")
    settings.append(uf)


def par(doc, text, align=JUSTIFY, size=12, bold=False, italic=False, color=None,
        space_after=6, line=1.5):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line
    run = p.add_run(text)
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    return p


def body(doc, *texts):
    for t in texts:
        par(doc, t)


def box_border(p):
    ppr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "12")
        el.set(qn("w:space"), "6")
        el.set(qn("w:color"), "C00000")
        pbdr.append(el)
    ppr.append(pbdr)


def slot_text(p, headline, text):
    r1 = p.add_run(headline)
    r1.font.name = FONT
    r1.font.size = Pt(10)
    r1.font.bold = True
    r1.font.color.rgb = RED
    r1.add_break()
    r2 = p.add_run(text)
    r2.font.name = FONT
    r2.font.size = Pt(10)
    r2.font.color.rgb = RED


def slot(doc, number):
    p = doc.add_paragraph()
    p.alignment = LEFT
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    box_border(p)
    slot_text(p, "[ SISIPKAN GAMBAR DI SINI - Gambar " + str(number) + " ]", FIG_INSTR[number])


def fig_caption(doc, number):
    par(doc, f"Gambar {number}. {FIG_TITLE[number]}", align=CENTER, size=11,
        italic=True, space_after=12, line=1.15)


def fig(doc, number):
    slot(doc, number)
    fig_caption(doc, number)


def table_caption(doc, number):
    par(doc, f"Tabel {number}. {TABLE_TITLES[number - 1]}", align=LEFT, size=11,
        bold=True, space_after=4, line=1.15)


def shade_cell(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    tcpr.append(shd)


def fill_cell(cell, text, bold=False, center=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    if center:
        p.alignment = CENTER
    run = p.add_run(text)
    run.font.name = FONT
    run.font.size = Pt(10)
    run.font.bold = bold


def table(doc, number, headers, rows, widths, center_cols=None):
    table_caption(doc, number)
    center_cols = center_cols or set()
    t = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, head in enumerate(headers):
        cell = t.rows[0].cells[j]
        fill_cell(cell, head, bold=True, center=True)
        shade_cell(cell, "D9E2F3")
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            fill_cell(t.rows[i].cells[j], str(val), center=(j in center_cols))
    for j, w in enumerate(widths):
        for cell in t.columns[j].cells:
            cell.width = Cm(w)
    par(doc, "", space_after=6, line=1.0)
    return t


def add_toc(doc):
    p = doc.add_paragraph()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), r'TOC \o "1-2" \h \z \u')
    run = OxmlElement("w:r")
    txt = OxmlElement("w:t")
    txt.text = "(Daftar isi akan terisi otomatis oleh Microsoft Word)"
    run.append(txt)
    fld.append(run)
    p._p.append(fld)


def cover(doc):
    p = doc.add_paragraph()
    p.alignment = CENTER
    p.paragraph_format.space_after = Pt(18)
    box_border(p)
    slot_text(p, "[ SISIPKAN LOGO DI SINI ]",
              "Cari 'logo STT Wastukancana' di internet, sisipkan di tengah "
              "kotak ini dengan lebar sekitar 6 cm, lalu hapus tulisan bingkai ini.")

    body(doc, "PENGOLAHAN CITRA DIGITAL", )
    doc.paragraphs[-1].alignment = CENTER
    par(doc, "PROJECT AKHIR", align=CENTER, size=12, bold=True)
    par(doc, "", align=CENTER, space_after=10)
    par(doc, "SISTEM PENDETEKSI WARNA UNTUK ALAT BANTU TUNA NETRA",
        align=CENTER, size=18, bold=True, space_after=30)
    par(doc, "Disusun oleh:", align=CENTER, size=12)
    par(doc, "Ananda Nur Hafidz", align=CENTER, size=12, bold=True, space_after=2)
    par(doc, "Mutiara Shella Widiaanggraeni", align=CENTER, size=12, bold=True, space_after=2)
    par(doc, "Mutiara Shelly Widia Anggraeni", align=CENTER, size=12, bold=True, space_after=2)
    par(doc, "Kelas: Malam B", align=CENTER, size=12, space_after=40)
    par(doc, "PROGRAM STUDI TEKNIK INFORMATIKA", align=CENTER, size=14, bold=True)
    par(doc, "SEKOLAH TINGGI TEKNOLOGI WASTUKANCANA", align=CENTER, size=14, bold=True)
    par(doc, "PURWAKARTA", align=CENTER, size=14, bold=True)
    par(doc, "2026", align=CENTER, size=14, bold=True)
    doc.add_page_break()


def front_matter(doc):
    doc.add_heading("DAFTAR ISI", level=1)
    add_toc(doc)
    doc.add_page_break()

    doc.add_heading("DAFTAR TABEL", level=1)
    for i, title in enumerate(TABLE_TITLES, start=1):
        par(doc, f"Tabel {i}. {title}", align=LEFT, space_after=4, line=1.15)
    doc.add_page_break()

    doc.add_heading("DAFTAR GAMBAR", level=1)
    for i in range(1, 14):
        if i in FIG_FILE:
            note = f"  (file: {FIG_FILE[i]})"
        else:
            note = "  (screenshot manual, instruksi tersedia di bab terkait)"
        par(doc, f"Gambar {i}. {FIG_TITLE[i]}{note}", align=LEFT, space_after=4, line=1.15)
    doc.add_page_break()


def bab1(doc):
    doc.add_heading("I. BUSINESS UNDERSTANDING", level=1)

    doc.add_heading("A. Latar Belakang", level=2)
    body(doc,
        "Tuna netra merupakan kondisi kehilangan penglihatan, baik seluruhnya "
        "maupun sebagian, sehingga informasi visual tidak dapat diperoleh secara "
        "langsung. Warna sebenarnya menyimpan banyak informasi dalam kehidupan "
        "sehari-hari: warna pakaian menentukan penampilan dan kenyamanan diri, "
        "warna pada objek tertentu memberikan peringatan (misalnya indikator "
        "lampu atau tingkat panas perangkat), serta warna menjadi bagian penting "
        "dalam melakukan koordinasi busana. Penyandang tuna netra umumnya harus "
        "meminta bantuan orang lain hanya untuk mengetahui warna baju yang akan "
        "dipakainya.")
    body(doc,
        "Alat bantu konvensional seperti tongkat putih dan kacamata membantu "
        "navigasi dan menghindari rintangan, tetapi tidak menyampaikan informasi "
        "warna. Di sisi lain, perkembangan pengolahan citra digital dan jaringan "
        "saraf tiruan membuat komputer mampu mengenali isi sebuah gambar dengan "
        "andal, termasuk mengenali warna objek pada gambar. Ketersediaan dataset "
        "riset AI4C Fashion Color (2024) yang menganotasi warna pakaian "
        "memperkuat bahwa identifikasi warna merupakan kebutuhan nyata.")
    body(doc,
        "Berdasarkan kenyataan tersebut, proyek ini membangun sistem pembaca "
        "warna yang murah dan mudah digunakan. Pengguna cukup mengarahkan kamera "
        "atau mengunggah gambar, sistem memproses citra menggunakan jaringan "
        "konvolusi terlatih, kemudian hasilnya dibacakan dalam Bahasa Indonesia "
        "menggunakan teknologi text-to-speech (TTS).")

    doc.add_heading("B. Tujuan", level=2)
    body(doc, "Tujuan proyek ini adalah:")
    par(doc, "1. Membangun model klasifikasi warna gambar multi-label berbasis "
             "MobileNetV2 (transfer learning) yang mampu mengenali lebih dari "
             "satu warna pada satu gambar.", space_after=4)
    par(doc, "2. Menyediakan dua mode hasil, yaitu mode Dasar dengan 7 kelompok "
             "warna umum Bahasa Indonesia dan mode Detail dengan 13 warna "
             "spesifik.", space_after=4)
    par(doc, "3. Membangun aplikasi web sederhana berbasis Flask dengan masukan "
             "melalui kamera atau unggahan gambar serta keluaran berupa tampilan "
             "dan suara (TTS) Bahasa Indonesia.", space_after=4)
    par(doc, "4. Mengevaluasi kinerja model menggunakan metrik precision, "
             "recall, dan F1-score agar kualitas hasil dapat dipertanggung-"
             "jawabkan.", space_after=4)

    doc.add_heading("C. Solusi", level=2)
    body(doc,
        "Sistem bekerja dengan alur sebagai berikut: (1) pengguna mengaktifkan "
        "kamera atau mengunggah gambar melalui aplikasi; (2) citra diperkecil "
        "ke 128x128 piksel dan dinormalisasi sesuai standar ImageNet; (3) model "
        "MobileNetV2 memprediksi probabilitas 13 warna secara bersamaan "
        "(multi-label); (4) setiap probabilitas dibandingkan dengan ambang batas "
        "(threshold) kelasnya untuk menetapkan warna-warna yang aktif; (5) nama "
        "warna hasil ditampilkan pada layar dan dibacakan oleh suara (TTS).")
    body(doc,
        "MobileNetV2 dipilih karena tidak terlalu banyak parameter sehingga "
        "ringan berjalan di CPU biasa; hasil pengukuran pada komputer proyek ini "
        "menunjukkan kecepatan inferensi rata-rata 9,7 ms per gambar sehingga "
        "terasa real-time. Teknik transfer learning dari ImageNet membantu model "
        "belajar dari data yang terbatas. Aplikasi dibuat berbasis web agar tidak "
        "memerlukan instalasi khusus di sisi pengguna.")

    doc.add_heading("D. Pengguna", level=2)
    body(doc, "Sasaran utama pengguna sistem serta keperluannya dirangkum pada "
              "Tabel 1 berikut.")
    table(doc, 1,
        ["Pengguna", "Keperluan"],
        [
            ["Penyandang tuna netra dan penderita low vision",
             "Mengenali warna pakaian dan objek secara mandiri melalui keluaran suara"],
            ["Keluarga dan pendamping",
             "Memeriksa warna pakaian/objek dengan cepat saat membantu penyandang"],
            ["Peneliti dan pengembang",
             "Menjadikan hasil sebagai dasar pengembangan sistem deteksi warna selanjutnya"],
        ],
        [5.5, 8.5])


def bab2(doc):
    doc.add_page_break()
    doc.add_heading("II. DATA UNDERSTANDING", level=1)

    doc.add_heading("A. Sumber Data", level=2)
    body(doc,
        "Data yang digunakan adalah AI4C Fashion Color Dataset, sebuah dataset "
        "riset tahun 2024 yang diterbitkan lewat repositori publik GitHub "
        "datable-be/AI4_C_datasets. Dataset berisi kumpulan foto produk fashion "
        "beserta anotasi warna dalam format COCO (.json). File dataset tersedia "
        "dalam tiga arsip terpisah dan satu file anotasi, sebagaimana dirinci "
        "pada Tabel 2.")
    fig(doc, 1)
    table(doc, 2,
        ["Nama berkas", "Keterangan"],
        [
            ["col1.tar.gz", "Arsip 1.000 gambar pakaian (JPEG)"],
            ["col2.tar.gz", "Arsip 1.000 gambar pakaian (JPEG)"],
            ["col3.tar.gz", "Arsip 405 gambar pakaian (JPEG)"],
            ["AI4C_Fashion_Color_Dataset_2024-06-01_0.json",
             "Anotasi format COCO: daftar images, annotations (bounding box dan category_id), serta categories berisi 15 label warna"],
        ],
        [6.0, 8.0])

    doc.add_heading("B. Deskripsi Data", level=2)
    body(doc,
        "Dataset memuat total 2.405 gambar produk fashion dengan 3.295 anotasi "
        "warna. Gambar umumnya berupa foto produk busana (baju, sepatu, tas, "
        "aksesori) pada latar polos, dengan ukuran asli bervariasi hingga sekitar "
        "500 piksel. Terdapat 15 label warna, yaitu white, black, brown, red, "
        "blue, yellow, grey, pink, green, purple, gold, orange, silver, beige, "
        "dan multicoloured.")
    body(doc,
        "Sifat penting dari dataset ini adalah multi-label, sebagaimana terlihat "
        "dari jumlah anotasi (3.295) yang lebih besar daripada jumlah gambar "
        "(2.405). Artinya, satu gambar dapat memiliki lebih dari satu warna, "
        "misalnya baju dasi berwarna putih dan biru sekaligus.")
    fig(doc, 2)

    doc.add_heading("C. Explore Data", level=2)
    body(doc,
        "Hasil penghitungan distribusi label disajikan pada Tabel 3. Label "
        "white dan black mendominasi dataset, sementara beige dan multicoloured "
        "masing-masing hanya muncul pada 4 gambar.")
    n = 3295
    rows = [
        ["white", 964], ["black", 844], ["brown", 336], ["red", 237],
        ["blue", 202], ["yellow", 155], ["grey", 133], ["pink", 116],
        ["green", 97], ["purple", 70], ["gold", 58], ["orange", 49],
        ["silver", 26], ["beige", 4], ["multicoloured", 4],
    ]
    table(doc, 3,
        ["Label warna", "Jumlah gambar", "Persentase"],
        [[label, num_id(count), num_dec(count / n * 100, 1) + " %"] for label, count in rows],
        [5.5, 4.5, 4.0], center_cols={1, 2})
    body(doc,
        "Komposisi banyaknya warna pada tiap gambar (multi-label) ditampilkan "
        "pada Tabel 4; sebagian besar gambar (66,7%) hanya memiliki satu label.")
    table(doc, 4,
        ["Jumlah label per gambar", "Jumlah gambar", "Persentase"],
        [
            ["1", "1.599", "66,7 %"],
            ["2", "717", "29,9 %"],
            ["3", "71", "3,0 %"],
            ["4", "9", "0,4 %"],
            ["5", "1", "0,0 %"],
        ],
        [5.5, 4.5, 4.0], center_cols={0, 1, 2})
    fig(doc, 3)
    fig(doc, 4)

    doc.add_heading("D. Kualitas Data", level=2)
    body(doc,
        "Secara umum dataset berada dalam kondisi baik: seluruh gambar terbaca "
        "dengan benar dan setiap gambar memiliki minimal satu label. Meski demikian, "
        "namun beberapa isu berikut perlu diperhatikan:")
    par(doc, "1. Dataset tidak seimbang (imbalanced): label white mencapai 964 "
             "gambar sementara silver hanya 26, selisih hingga 37 kali.", space_after=4)
    par(doc, "2. Label beige dan multicoloured hanya memiliki 4 sampel, terlalu "
             "sedikit untuk pelatihan model yang wajar.", space_after=4)
    par(doc, "3. Sifat multi-label menuntut pendekatan klasifikasi khusus, karena "
             "lebih dari satu warna boleh sah pada satu gambar.", space_after=4)
    par(doc, "4. Terdapat pasangan warna yang mirip (misal silver vs white, "
             "gold vs yellow) sehingga batasan antar klas menantang.", space_after=4)
    body(doc, "Seluruh isu tersebut ditangani pada tahap Data Preparation.")


def bab3(doc):
    doc.add_page_break()
    doc.add_heading("III. DATA PREPARATION", level=1)

    doc.add_heading("A. Pemilihan Data", level=2)
    body(doc,
        "Dua kelas dengan sampel sangat sedikit, beige dan multicoloured "
        "(masing-masing 4 gambar), dikeluarkan karena tidak cukup untuk "
        "pelatihan maupun pengujian yang adil. Tahap selanjutnya adalah "
        "mengidentifikasi gambar yang hanya berlabel kedua kelas tersebut; "
        "hasil pemeriksaan menemukan 8 gambar seperti itu, yang kemudian "
        "dibuang dari dataset.")
    body(doc,
        "Tahapan ini menghasilkan dataset bersih berisi 2.397 gambar dengan 13 "
        "kelas warna, tetap mempertahankan sifat multi-label. Untuk kebutuhan "
        "keluaran yang menyenangkan suaranya bagi tuna netra, 13 kelas detail "
        "dirangkum menjadi 7 kelompok warna dasar Bahasa Indonesia seperti pada "
        "Tabel 5; kedua mode tetap dapat dipakai dari satu model yang sama.")
    table(doc, 5,
        ["Kelompok dasar", "Anggota kelas detail"],
        [
            ["merah", "red, orange, pink"],
            ["biru", "blue, purple"],
            ["hijau", "green"],
            ["kuning", "yellow, gold"],
            ["putih", "white, silver"],
            ["hitam", "black, grey"],
            ["coklat", "brown"],
        ],
        [5.5, 8.5], center_cols=set())

    doc.add_heading("B. Data Preprocessing", level=2)
    body(doc,
        "Label seluruh gambar disusun ke file labels.csv (nama berkas dan daftar "
        "label). Target pelatihan di-encode menjadi vektor 13 dimensi (multi-hot); "
        "nilai 1 menandakan kelas hadir pada gambar tersebut. Label 7 kelompok "
        "dasar dihitung dengan menggabungkan perkumpulan anggota dari Tabel 5.")
    body(doc,
        "Data dibagi menjadi tiga bagian dengan strategi stratified agar "
        "proporsi label tetap terjaga: 70% data latih (1.677 gambar), 15% data "
        "validasi (360 gambar), dan 15% data uji (360 gambar), sebagaimana pada "
        "Tabel 6.")
    table(doc, 6,
        ["Bagian data", "Jumlah gambar", "Proporsi"],
        [
            ["Data latih (train)", "1.677", "70,0 %"],
            ["Data validasi (validation)", "360", "15,0 %"],
            ["Data uji (test)", "360", "15,0 %"],
            ["Total", "2.397", "100,0 %"],
        ],
        [6.0, 4.5, 3.5], center_cols={1, 2})
    body(doc,
        "Semua citra dinormalisasi ukurannya ke 128x128 piksel sesuai masukan "
        "MobileNetV2, kemudian setiap piksel dinormalisasi memakai rata-rata dan "
        "simpangan ImageNet (mean = [0,485; 0,456; 0,406], std = [0,229; 0,224; "
        "0,225]). Untuk data latih diberikan augmentasi ringan, yaitu resize ke "
        "160 piksel, RandomResizedCrop 128 piksel (rasio luas 0,75-1,0), "
        "pembalikan horizontal (p=0,5), rotasi maksimum 10 derajat, serta "
        "ColorJitter pada brightness, contrast, dan saturation dengan besaran "
        "0,15. Data validasi dan uji tidak diaugmentasi; keduanya hanya resize "
        "dan normalisasi.")
    body(doc,
        "Augmentasi warna yang umum (pengubahan hue serta grayscale) "
        "sengaja TIDAK digunakan. Pada klasifikasi warna, pengubahan yang "
        "mengubah warna citra sedangkan label tetap akan menyebabkan kontradiksi "
        "data-latih; eksperimen pada proyek ini membuktikan penghapusan "
        "augmentasi tersebut meningkatkan kinerja model secara signifikan "
        "(dibahas pada Bab IV).")
    fig(doc, 5)
    fig(doc, 6)

    doc.add_heading("C. Data Issue", level=2)
    body(doc, "Rangkuman isu data dan penanganannya pada proyek ini disajikan "
              "pada Tabel 7.")
    table(doc, 7,
        ["No", "Isu", "Penanganan"],
        [
            ["1", "Satu gambar dapat memuat lebih dari satu warna (multi-label)",
             "Klasifikasi multi-label: aktivasi sigmoid dan loss BCEWithLogitsLoss"],
            ["2", "Ketidakseimbangan kelas (white 964 vs silver 26)",
             "Bobot kelas pos_weight = neg/pos untuk setiap kelas, dibatasi 10"],
            ["3", "Kelas beige dan multicoloured hanya 4 sampel",
             "Kelas dihapus; 8 gambar yang hanya berlabel kedua kelas itu dibuang"],
            ["4", "Augmentasi warna (hue/grayscale) merusak korespondensi citra-label",
             "Augmentasi dilakukan tanpa pengubahan hue; macro-F1 validasi naik dari 0,44 menjadi 0,62"],
            ["5", "Ukuran gambar tidak seragam (hingga sekitar 500 piksel)",
             "Resize menyeluruh ke 128x128 piksel"],
            ["6", "Kemungkinan gambar korup",
             "Pemeriksaan kelas di tahap awal; hasilnya 0 gambar korup"],
            ["7", "Nama 13 warna detail terlalu panjang untuk disebutkan",
             "Mode Dasar merangkum menjadi 7 kelompok Bahasa Indonesia"],
        ],
        [1.0, 6.0, 7.0])


def bab4(doc):
    doc.add_page_break()
    doc.add_heading("IV. MODELING", level=1)

    doc.add_heading("A. Pemilihan Model dan Teknik", level=2)
    body(doc,
        "Model utama yang digunakan adalah MobileNetV2 yang diinisialisasi "
        "dengan bobot pra-latih ImageNet (transfer learning). Backbone berperan "
        "mengekstraksi ciri visual universal, kemudian kepala (head) klasifikasi "
        "diganti dengan kepala baru yang menghasilkan 13 keluaran. "
        "Setiap keluaran kelas melewati fungsi sigmoid yang terpisah sehingga "
        "lebih dari satu kelas dapat aktif bersamaan (multi-label). Untuk mode "
        "Dasar, probabilitas setiap kelompok dihitung sebagai nilai maksimum "
        "probabilitas anggota kelompoknya.")

    doc.add_heading("B. Arsitektur Model", level=2)
    table(doc, 8,
        ["Komponen", "Keterangan"],
        [
            ["Backbone MobileNetV2 (ImageNet)",
             "Ekstraksi fitur berjalan hingga fitur 1x1x1280, seluruh lapisan ikut dilatih (fine-tuning)"],
            ["Dropout (p = 0,3)", "Regularisasi agar tidak overfitting"],
            ["Linear 1280 -> 512 + ReLU", "Lapisan tersembunyi kepala klasifikasi"],
            ["BatchNorm1d (512)", "Stabilisasi distribusi aktivasi"],
            ["Dropout (p = 0,2)", "Regularisasi tambahan"],
            ["Linear 512 -> 13", "Logit untuk tiap kelas detail"],
            ["Sigmoid (saat inferensi)", "Mengubah logit menjadi probabilitas tiap kelas"],
            ["Agregasi kelompok", "Mode dasar mengambil nilai maksimum probabilitas anggota"],
        ],
        [6.5, 7.5])

    doc.add_heading("C. Perancangan Pelatihan", level=2)
    table(doc, 9,
        ["Parameter", "Nilai"],
        [
            ["Ukuran masukan", "128 x 128 piksel (3 kanal warna)"],
            ["Ukuran batch", "16"],
            ["Epoch maksimum", "20"],
            ["Optimizer", "AdamW (lr kepala 3x10^-4, lr backbone 5x10^-5)"],
            ["Penjadwal learning rate", "CosineAnnealingLR (1 siklus)"],
            ["Fungsi loss", "BCEWithLogitsLoss dengan bobot kelas"],
            ["Bobot kelas", "pos_weight = neg/pos tiap kelas, batas atas 10"],
            ["Gradient clipping", "1.0"],
            ["Early stopping", "Berhenti bila 8 epoch tanpa perbaikan macro-F1 validasi"],
            ["Metrik utama", "Macro-F1 pada data validasi"],
            ["Ambang batas (threshold)", "Disetel per kelas melalui data validasi"],
        ],
        [6.0, 8.0])
    body(doc,
        "Bobot pos_weight setiap kelas dihitung dari rasio banyaknya sampel "
        "negatif dibanding sampel positif, seperti pada Tabel 10, sehingga kelas "
        "yang jarang memperoleh porsi yang lebih besar dalam loss.")
    table(doc, 10,
        ["Kelas", "pos_weight"],
        [
            ["black", "1,9"], ["blue", "10,0"], ["brown", "6,1"],
            ["gold", "10,0"], ["green", "10,0"], ["grey", "10,0"],
            ["orange", "10,0"], ["pink", "10,0"], ["purple", "10,0"],
            ["red", "8,9"], ["silver", "10,0"], ["white", "1,5"],
            ["yellow", "10,0"],
        ],
        [5.5, 3.5], center_cols={1})

    doc.add_heading("D. Pelatihan dan Perbaikan", level=2)
    body(doc,
        "Percobaan pertama memakai augmentasi warna yang kuat (pengubahan hue, "
        "grayscale, dan jitter ekstensif). Hasilnya kegagalan pembelajaran: "
        "macro-F1 validasi hanya 0,444 setelah 15 epoch, karena warna citra "
        "diubah sedangkan labelnya tetap sehingga model memperoleh informasi "
        "yang berkontradiksi.")
    body(doc,
        "Setelah augmentasi diperbaiki seperti diuraikan pada Bab III, "
        "pelatihan ulang 20 epoch menghasilkan macro-F1 validasi 0,617 pada "
        "epoch ke-14, lalu penyetingan ambang batas per kelas pada data "
        "validasi menaikkan nilai menjadi 0,665. Perkembangan loss dan F1 "
        "selama pelatihan disajikan pada Gambar 7.")
    fig(doc, 7)


def bab5(doc):
    doc.add_page_break()
    doc.add_heading("V. EVALUATION", level=1)

    doc.add_heading("A. Metrik Evaluasi", level=2)
    body(doc,
        "Sesuai sifat multi-label, evaluasi memakai precision, recall, dan "
        "F1-score per keluaran, lalu dirangkum dalam tiga cara: macro-F1 (rata-rata "
        "tanpa menimbang jumlah sampel), micro-F1 (dihitung dari seluruh "
        "prediksi), dan weighted-F1 (dibobot jumlah sampel kelas). Hamming loss "
        "menambahkan proporsi label yang salah per gambar; nilainya lebih rendah "
        "berarti lebih baik. Evaluasi dilakukan menyeluruh pada 360 gambar data "
        "uji yang belum pernah dilihat model (total 490 anotasi label).")

    doc.add_heading("B. Hasil Evaluasi", level=2)
    body(doc, "Hasil lengkap mode Detail per kelas tersaji pada Tabel 11.")
    table(doc, 11,
        ["Kelas", "Precision", "Recall", "F1-Score", "Support", "Ambang"],
        [
            ["black", "0,813", "0,883", "0,846", "128", "0,35"],
            ["blue", "0,548", "0,793", "0,648", "29", "0,60"],
            ["brown", "0,851", "0,800", "0,825", "50", "0,80"],
            ["gold", "0,667", "0,250", "0,364", "8", "0,95"],
            ["green", "1,000", "0,667", "0,800", "15", "0,75"],
            ["grey", "0,769", "0,526", "0,625", "19", "0,90"],
            ["orange", "0,200", "0,111", "0,143", "9", "0,50"],
            ["pink", "0,688", "0,688", "0,688", "16", "0,65"],
            ["purple", "0,500", "0,167", "0,250", "12", "0,50"],
            ["red", "0,756", "0,939", "0,838", "33", "0,95"],
            ["silver", "0,667", "0,500", "0,571", "4", "0,75"],
            ["white", "0,790", "0,785", "0,787", "144", "0,55"],
            ["yellow", "0,643", "0,783", "0,706", "23", "0,55"],
        ],
        [3.0, 2.4, 2.4, 2.4, 2.0, 2.0],
        center_cols={1, 2, 3, 4, 5})
    body(doc, "Ringkasan kedua mode pada data uji disajikan pada Tabel 12, dan "
              "detail mode dasar pada Tabel 13.")
    table(doc, 12,
        ["Mode", "Macro-F1", "Micro-F1", "Weighted-F1", "Hamming Loss"],
        [
            ["Detail (13 kelas)", "0,622", "0,764", "0,755", "0,050"],
            ["Dasar (7 kelompok)", "0,767", "0,788", "0,790", "0,081"],
        ],
        [4.5, 2.5, 2.5, 2.5, 2.5],
        center_cols={1, 2, 3, 4})
    table(doc, 13,
        ["Kelompok", "Precision", "Recall", "F1-Score", "Support", "Ambang"],
        [
            ["merah", "0,703", "0,897", "0,788", "58", "0,55"],
            ["biru", "0,551", "0,675", "0,607", "40", "0,50"],
            ["hijau", "1,000", "0,667", "0,800", "15", "0,75"],
            ["kuning", "0,800", "0,645", "0,714", "31", "0,80"],
            ["putih", "0,828", "0,750", "0,787", "148", "0,70"],
            ["hitam", "0,836", "0,859", "0,847", "142", "0,45"],
            ["coklat", "0,851", "0,800", "0,825", "50", "0,80"],
        ],
        [3.0, 2.4, 2.4, 2.4, 2.0, 2.0],
        center_cols={1, 2, 3, 4, 5})
    fig(doc, 8)
    fig(doc, 9)
    fig(doc, 10)

    doc.add_heading("C. Interpretasi Hasil", level=2)
    body(doc,
        "Mode dasar mencapai macro-F1 0,767 dengan kecepatan inferensi 9,7 ms "
        "per gambar pada CPU biasa, memadai untuk penggunaan nyata. Kelompok "
        "dengan data terbanyak tampil paling baik: hitam (F1 0,847), coklat "
        "(0,825), hijau (0,800), merah (0,788), dan putih (0,787).")
    body(doc,
        "Pada mode detail, kelas dengan support sangat kecil masih lemah: "
        "orange (F1 0,143, support 9), purple (0,250, support 12), dan gold "
        "(0,364, support 8). Hal ini wajar karena kurangnya contoh dan "
        "ketika mirip dengan tetangganya (orange vs merah/kuning, gold vs "
        "kuning). Pendekatan mode dasar tepat mengatasi kelemahan tersebut; "
        "hasil kelompok kuning yang meliputi gold melaporkan F1 0,714.")
    body(doc,
        "Hamming loss rendah (0,050 pada mode detail) menunjukkan kesalahan "
        "per label per gambar sangat kecil. Dengan begitu, sistem layak dijadikan "
        "alat bantu harian dengan perhatian pada warna-warna langka.")


def bab6(doc):
    doc.add_page_break()
    doc.add_heading("VI. DEPLOYMENT", level=1)

    doc.add_heading("A. Arsitektur Aplikasi", level=2)
    body(doc,
        "Aplikasi dikerahkan sebagai server web Flask lokal (app.py) yang "
        "memuat model terbaik models\\best_model.pth beserta ambang batas "
        "kedua mode. Antarmuka dibangun dari template index.html beserta "
        "style.css dan main.js di folder static. Aplikasi berjalan pada alamat "
        "http://127.0.0.1:8001 dan menyediakan tiga lapisan antarmuka: GET / "
        "(halaman utama), POST /predict (analisis gambar), dan GET /health "
        "(status server).")
    body(doc,
        "Alur kerja satu klik deteksi: browser menangkap frame kamera "
        "(atau membaca file unggahan), memampatkannya ke JPEG maksimum 640 "
        "piksel, mengirim sebagai base64 melalui POST /predict; server "
        "melakukan praproses yang sama dengan tahap latihan, menjalankan "
        "inferensi, membandingkan probabilitas dengan ambang kelas; hasil "
        "dikembalikan sebagai JSON berisi daftar detail, daftar dasar, dan "
        "waktu inferensi (time_ms). Browser kemudian menampilkan warna dominan, "
        "bar kemungkinan warna, dan membacakan hasil menggunakan "
        "speechSynthesis dengan suara Bahasa Indonesia (id-ID).")

    doc.add_heading("B. Fitur Aplikasi", level=2)
    table(doc, 14,
        ["Fitur", "Deskripsi"],
        [
            ["Unggah gambar", "Gambar dipilih dari perangkat dan langsung dianalisis"],
            ["Kamera webcam", "Mode langsung: objek diarahkan ke kamera lalu dianalisis"],
            ["Deteksi otomatis", "Analisis berulang otomatis setiap 3 detik saat kamera aktif"],
            ["Mode Dasar / Detail", "Dapat berganti kapan saja; mode dasar memakai 7 kelompok"],
            ["Suara (TTS)", "Warna dominan dan warna tambahan dibacakan dalam Bahasa Indonesia; bisa diatur bicara otomatis"],
            ["Tema terang/gelap", "Tema terang berkontras tinggi; tema gelap tersedia"],
            ["Pintasan keyboard", "Spasi (ambil), U (unggah), T (dengarkan), K (kamera), D (tema)"],
            ["Aksesibilitas", "Dukungan pembaca layar (aria-live), target sentuh besar, indikator fokus jelas"],
        ],
        [5.0, 9.0])
    fig(doc, 11)
    fig(doc, 12)
    fig(doc, 13)

    doc.add_heading("C. Cara Menjalankan", level=2)
    par(doc, "1. Buka folder project di terminal.", space_after=4)
    par(doc, "2. Jalankan perintah: .\\.venv\\Scripts\\python.exe app.py", space_after=4)
    par(doc, "3. Buka http://127.0.0.1:8001 pada browser.", space_after=4)
    par(doc, "4. Gunakan tombol Kamera atau Unggah Gambar; pilih mode Dasar atau "
             "Detail; klik Dengarkan Hasil (atau aktifkan bicara otomatis) untuk "
             "mendengar warna terdeteksi.", space_after=4)


def penutup(doc):
    doc.add_page_break()
    doc.add_heading("KESIMPULAN DAN SARAN", level=1)
    doc.add_heading("A. Kesimpulan", level=2)
    body(doc,
        "Proyek ini berhasil menghasilkan tiga hal utama. Pertama, dataset "
        "AI4C Fashion Color berhasil diproses menjadi data latih yang bersih "
        "(2.397 gambar, 13 kelas warna, pembagian 70/15/15). Kedua, model "
        "MobileNetV2 multi-label yang dilatih mencapai macro-F1 0,622 pada mode "
        "detail dan 0,767 pada mode dasar di data uji, dengan kecepatan 9,7 ms "
        "per gambar pada CPU. Ketiga, aplikasi web ColorSense yang dilengkapi "
        "keluaran suara Bahasa Indonesia berhasil dijalankan dan memenuhi "
        "kebutuhan pemakaian bagi tuna netra melalui pendekatan "
        "audio-first, kontras tinggi, dan pintasan keyboard.")
    doc.add_heading("B. Saran", level=2)
    par(doc, "1. Menambah data kelas langka (orange, purple, gold, silver) dari "
             "dataset lain atau proses penambahan data sintetis agar mode detail "
             "lebih seimbang.", space_after=4)
    par(doc, "2. Mencoba backbone atau resolusi lain (misalnya EfficientNet atau "
             "masukan 224 piksel) untuk membandingkan akurasi versus "
             "kecepatan.", space_after=4)
    par(doc, "3. Menyelidiki metode penyetelan ambang batas yang lebih adaptif "
             "demi memenuhi kebutuhan masing-masing mode.", space_after=4)
    par(doc, "4. Menerapkan model ke perangkat mobile (misal TFLite) dan melakukan "
             "pengujian langsung bersama penyandang tuna netra.", space_after=4)


def main():
    doc = Document()
    setup(doc)
    cover(doc)
    front_matter(doc)
    bab1(doc)
    bab2(doc)
    bab3(doc)
    bab4(doc)
    bab5(doc)
    bab6(doc)
    penutup(doc)
    doc.save(OUT)
    print("OK", OUT)


if __name__ == "__main__":
    main()
