# FinStart – Smart Money Management

Website edukasi dan pengelolaan keuangan bulanan untuk pemula.
Dibuat dengan **Python Flask**, **SQLite**, HTML, CSS, JavaScript, dan **Chart.js**.
Chart.js dan ikon sudah disertakan di folder `static/vendor/`, jadi aplikasi **bisa berjalan tanpa internet**.

## Cara menjalankan

Syarat: Python 3.9 atau lebih baru.

1. Buka terminal di folder `finstart/` (di Antigravity: menu *Terminal → New Terminal*).
2. (Disarankan) buat virtual environment:

   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS / Linux
   ```

3. Pasang dependensi dan jalankan:

   ```
   pip install -r requirements.txt

   python app.py
   ```

4. Buka browser ke **http://127.0.0.1:5000**

Jika perintah `python` tidak dikenali, gunakan `python3`.
Untuk menghentikan server tekan `Ctrl + C`.

## Catatan data

- File `database.db` dibuat otomatis saat pertama kali dijalankan dan berisi data contoh.
- Data tersimpan permanen di `database.db`, tidak hilang saat server ditutup.
- Untuk mengosongkan ke kondisi awal, hentikan server, hapus `database.db`, lalu jalankan lagi.
- Ganti port bila 5000 terpakai: ubah `port=5000` di baris terakhir `app.py`.

## Fitur

| Halaman | Isi |
|---|---|
| Dashboard | Pemasukan, pengeluaran, tabungan, sisa saldo, grafik 6 bulan, grafik kategori, transaksi terbaru, penggunaan anggaran, filter bulan & tahun |
| Transaksi | Tambah, ubah, hapus, cari, filter jenis/kategori/bulan/tahun, riwayat |
| Anggaran | Metode 50/30/20 dengan persentase yang bisa diatur, progres, peringatan hampir habis (≥ 80%) dan terlampaui |
| Target Tabungan | Buat target, saldo awal, tambah dana, persentase, sisa target, riwayat setoran |
| Panduan Keuangan | 6 langkah interaktif dengan checklist dan tombol tandai selesai (disimpan di database) |
| Edukasi | 6 artikel singkat |
| Kalkulator | Pembagian anggaran, target tabungan, sisa uang bulanan, batas pengeluaran harian |

## Aturan perhitungan

- **Sisa saldo = pemasukan − pengeluaran − setoran tabungan** pada bulan yang dipilih.
- Setoran tabungan disimpan di tabel terpisah, jadi **tidak dihitung sebagai pengeluaran** dan tidak terhitung dua kali.
- **Saldo awal** target tabungan adalah uang yang sudah kamu miliki sebelumnya: masuk ke total tabungan, tetapi tidak mengurangi sisa saldo bulanan.
- Kategori anggaran: *Kebutuhan* = Makanan, Transportasi, Kebutuhan kuliah, Tagihan, Kesehatan. *Keinginan* = Belanja, Hiburan, Lainnya. *Tabungan* = setoran ke target tabungan bulan itu.
- Alokasi anggaran = total pemasukan bulan itu × persentase.

## Struktur proyek

```
finstart/
├── app.py            # Flask: database, perhitungan, routes, validasi
├── content.py        # Kategori, isi panduan, artikel edukasi
├── database.db       # Database SQLite (dibuat otomatis)
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html  dashboard.html  transactions.html  budget.html
│   ├── savings.html  guide.html  education.html  calculator.html
│   └── _macros.html  _transaction_modal.html  error.html
└── static/
    ├── css/style.css
    ├── js/script.js
    └── vendor/       # Chart.js & Bootstrap Icons (lokal)
```

## Tabel database

`transactions`, `budgets`, `savings_goals`, `savings_deposits`, `guide_progress`, `meta`.
Semua query memakai parameterized SQL.

## Pengembangan lanjutan (ide)

Ekspor CSV, anggaran per kategori, login pengguna, transaksi berulang.
