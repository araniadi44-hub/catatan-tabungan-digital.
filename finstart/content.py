"""Konten statis FinStart: kategori, langkah panduan, dan artikel edukasi.

Dipisahkan dari app.py supaya app.py tetap ringkas dan mudah dibaca.
"""

# ---------------------------------------------------------------------------
# Kategori transaksi
# ---------------------------------------------------------------------------
INCOME_CATEGORIES = ["Gaji", "Uang saku", "Freelance", "Bonus", "Lainnya"]

EXPENSE_CATEGORIES = [
    "Makanan",
    "Transportasi",
    "Kebutuhan kuliah",
    "Tagihan",
    "Belanja",
    "Hiburan",
    "Kesehatan",
    "Lainnya",
]

# Pemetaan kategori pengeluaran ke kelompok anggaran 50/30/20.
# Kategori "Lainnya" dihitung sebagai keinginan agar tidak melonggarkan kebutuhan.
NEEDS_CATEGORIES = ["Makanan", "Transportasi", "Kebutuhan kuliah", "Tagihan", "Kesehatan"]
WANTS_CATEGORIES = ["Belanja", "Hiburan", "Lainnya"]

# Ikon Bootstrap Icons untuk tiap kategori pengeluaran (dipakai di tabel & grafik)
CATEGORY_ICONS = {
    "Gaji": "bi-briefcase",
    "Uang saku": "bi-wallet2",
    "Freelance": "bi-laptop",
    "Bonus": "bi-gift",
    "Makanan": "bi-egg-fried",
    "Transportasi": "bi-bus-front",
    "Kebutuhan kuliah": "bi-book",
    "Tagihan": "bi-receipt",
    "Belanja": "bi-bag",
    "Hiburan": "bi-controller",
    "Kesehatan": "bi-heart-pulse",
    "Lainnya": "bi-three-dots",
}

MONTH_NAMES = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

# ---------------------------------------------------------------------------
# Enam langkah panduan keuangan
# ---------------------------------------------------------------------------
GUIDE_STEPS = [
    {
        "step": 1,
        "title": "Mencatat seluruh pemasukan",
        "icon": "bi-cash-coin",
        "summary": "Langkah pertama adalah tahu persis berapa uang yang masuk setiap bulan.",
        "explanation": (
            "Jumlahkan semua sumber uang yang kamu terima dalam satu bulan: uang saku, gaji, "
            "hasil freelance, bonus, sampai hadiah. Gunakan angka yang pasti diterima, bukan "
            "perkiraan optimis. Jika pemasukanmu tidak tetap, pakai rata-rata 3 bulan terakhir "
            "atau angka bulan terendah sebagai patokan."
        ),
        "example": (
            "Rina menerima uang saku Rp1.500.000 dan mendapat Rp500.000 dari freelance desain. "
            "Total pemasukan bulanannya Rp2.000.000."
        ),
        "checklist": [
            "Saya sudah menuliskan semua sumber pemasukan bulan ini",
            "Saya tahu total pemasukan bulanan saya",
            "Saya sudah mencatat pemasukan di menu Transaksi",
        ],
    },
    {
        "step": 2,
        "title": "Menentukan kebutuhan wajib",
        "icon": "bi-house-check",
        "summary": "Pisahkan pengeluaran yang tidak bisa ditunda dari yang bisa dikurangi.",
        "explanation": (
            "Kebutuhan wajib adalah pengeluaran yang harus dibayar agar hidupmu tetap berjalan: "
            "makan, transportasi, kos/sewa, listrik, pulsa/internet, perlengkapan kuliah, dan "
            "kesehatan. Tulis semuanya beserta nominal rata-ratanya, lalu jumlahkan."
        ),
        "example": (
            "Makan Rp700.000, transportasi Rp200.000, kuota internet Rp100.000, dan fotokopi "
            "Rp50.000. Total kebutuhan wajib Rp1.050.000 per bulan."
        ),
        "checklist": [
            "Saya sudah membuat daftar kebutuhan wajib",
            "Saya tahu total kebutuhan wajib per bulan",
            "Saya sudah membedakan kebutuhan dan keinginan",
        ],
    },
    {
        "step": 3,
        "title": "Menentukan target tabungan",
        "icon": "bi-piggy-bank",
        "summary": "Tabung di awal, bukan dari sisa uang di akhir bulan.",
        "explanation": (
            "Tentukan tujuan menabung yang jelas (dana darurat, laptop, liburan) lengkap dengan "
            "nominal dan batas waktu. Bagilah nominal target dengan jumlah bulan untuk mengetahui "
            "setoran bulanan. Patokan umum: sisihkan minimal 10-20% dari pemasukan."
        ),
        "example": (
            "Ingin membeli laptop Rp6.000.000 dalam 10 bulan. Setoran yang dibutuhkan "
            "Rp600.000 per bulan."
        ),
        "checklist": [
            "Saya punya minimal satu tujuan menabung yang jelas",
            "Saya sudah menghitung setoran tabungan per bulan",
            "Saya sudah membuat target di menu Target Tabungan",
        ],
    },
    {
        "step": 4,
        "title": "Membuat anggaran pengeluaran",
        "icon": "bi-pie-chart",
        "summary": "Beri 'jatah' untuk setiap kelompok pengeluaran sebelum bulan dimulai.",
        "explanation": (
            "Anggaran adalah rencana pembagian uang. Metode 50/30/20 cocok untuk pemula: 50% "
            "kebutuhan, 30% keinginan, 20% tabungan. Sesuaikan persentasenya dengan kondisimu. "
            "Jika kebutuhanmu besar, kurangi porsi keinginan terlebih dahulu."
        ),
        "example": (
            "Pemasukan Rp2.000.000 dibagi menjadi kebutuhan Rp1.000.000, keinginan Rp600.000, "
            "dan tabungan Rp400.000."
        ),
        "checklist": [
            "Saya sudah memilih pembagian persentase anggaran",
            "Saya sudah melihat alokasi dalam rupiah di menu Anggaran",
            "Saya tahu batas pengeluaran untuk tiap kelompok",
        ],
    },
    {
        "step": 5,
        "title": "Mencatat setiap transaksi",
        "icon": "bi-journal-text",
        "summary": "Catat setiap rupiah yang keluar, sekecil apa pun, secepat mungkin.",
        "explanation": (
            "Pengeluaran kecil yang sering terjadi (jajan, ongkos, top-up) mudah terlupa tetapi "
            "jumlahnya besar jika dijumlahkan. Biasakan mencatat transaksi di hari yang sama. "
            "Gunakan kategori yang tepat supaya laporan dan grafik akurat."
        ),
        "example": (
            "Kopi Rp18.000 + parkir Rp3.000 + gorengan Rp10.000 terlihat kecil, tetapi bisa "
            "mencapai Rp600.000 dalam sebulan jika terjadi setiap hari."
        ),
        "checklist": [
            "Saya mencatat transaksi di hari yang sama",
            "Saya memilih kategori dengan benar",
            "Saya mengecek riwayat transaksi minimal seminggu sekali",
        ],
    },
    {
        "step": 6,
        "title": "Melakukan evaluasi keuangan",
        "icon": "bi-clipboard-data",
        "summary": "Di akhir bulan, bandingkan rencana dengan kenyataan lalu perbaiki.",
        "explanation": (
            "Buka Dashboard dan lihat kategori mana yang paling besar, apakah ada anggaran yang "
            "terlampaui, dan apakah target tabungan tercapai. Evaluasi bukan untuk menyalahkan "
            "diri, tetapi untuk menemukan satu-dua kebiasaan yang bisa diperbaiki bulan depan."
        ),
        "example": (
            "Pengeluaran hiburan melampaui anggaran 40%. Bulan depan batasnya diturunkan dan "
            "selisihnya dialihkan ke tabungan."
        ),
        "checklist": [
            "Saya sudah melihat ringkasan bulan ini di Dashboard",
            "Saya tahu kategori pengeluaran terbesar saya",
            "Saya menentukan satu perbaikan untuk bulan depan",
        ],
    },
]

# ---------------------------------------------------------------------------
# Artikel edukasi
# ---------------------------------------------------------------------------
ARTICLES = [
    {
        "id": "mengatur-uang-pemula",
        "title": "Mengatur Uang untuk Pemula",
        "icon": "bi-lightbulb",
        "tag": "Dasar",
        "excerpt": "Mulai dari tiga kebiasaan sederhana yang bisa langsung dipraktikkan.",
        "paragraphs": [
            "Mengatur uang tidak membutuhkan penghasilan besar, hanya kebiasaan yang konsisten. "
            "Mulailah dengan tiga hal: catat pemasukan, catat pengeluaran, dan sisihkan tabungan "
            "di awal bulan.",
            "Pisahkan uang untuk kebutuhan, keinginan, dan tabungan. Jika memungkinkan, "
            "gunakan rekening atau dompet digital terpisah untuk tabungan agar tidak tercampur "
            "dengan uang harian.",
            "Tinjau catatanmu seminggu sekali. Kebiasaan kecil yang dilakukan rutin jauh lebih "
            "efektif daripada rencana besar yang tidak dijalankan.",
        ],
    },
    {
        "id": "kebutuhan-vs-keinginan",
        "title": "Membedakan Kebutuhan dan Keinginan",
        "icon": "bi-signpost-split",
        "tag": "Dasar",
        "excerpt": "Tanyakan tiga pertanyaan ini sebelum membeli sesuatu.",
        "paragraphs": [
            "Kebutuhan adalah hal yang jika tidak dipenuhi akan mengganggu hidup atau studimu, "
            "seperti makan, transportasi, tempat tinggal, dan buku kuliah. Keinginan adalah "
            "hal yang membuat hidup lebih nyaman tetapi bisa ditunda.",
            "Sebelum membeli, tanyakan: apakah ini benar-benar kubutuhkan? Apakah ada pilihan "
            "yang lebih murah? Apakah aku akan tetap menginginkannya 48 jam lagi?",
            "Satu barang bisa menjadi keduanya. Ponsel adalah kebutuhan, tetapi ponsel "
            "termahal biasanya keinginan. Pilih yang memenuhi fungsi, bukan gengsi.",
        ],
    },
    {
        "id": "menghindari-boros",
        "title": "Menghindari Kebiasaan Boros",
        "icon": "bi-shield-exclamation",
        "tag": "Kebiasaan",
        "excerpt": "Kenali pemicu belanja impulsif dan cara mengendalikannya.",
        "paragraphs": [
            "Boros biasanya bukan karena satu pembelian besar, melainkan banyak pembelian kecil "
            "yang tidak disadari: jajan berlebih, langganan yang jarang dipakai, dan diskon "
            "yang memancing belanja tidak perlu.",
            "Terapkan aturan tunggu 24-48 jam untuk barang non-esensial. Hapus aplikasi belanja "
            "yang sering menggoda, dan tinjau langganan bulanan secara berkala.",
            "Tetapkan batas uang untuk hiburan setiap bulan. Ketika batas habis, berhenti sampai "
            "bulan berikutnya tanpa menambah dari pos lain.",
        ],
    },
    {
        "id": "menabung-uang-terbatas",
        "title": "Menabung dengan Uang Terbatas",
        "icon": "bi-piggy-bank",
        "tag": "Tabungan",
        "excerpt": "Menabung kecil tetapi rutin lebih baik daripada menunggu uang berlebih.",
        "paragraphs": [
            "Jika uangmu terbatas, mulailah dari nominal kecil, misalnya Rp5.000 sampai "
            "Rp10.000 per hari. Yang terpenting adalah kebiasaannya; nominal bisa dinaikkan "
            "ketika pemasukan bertambah.",
            "Menabunglah di awal, begitu uang masuk, bukan dari sisa di akhir bulan. Sisa uang "
            "hampir selalu habis sebelum sempat ditabung.",
            "Beri nama pada setiap tabunganmu, seperti 'Dana Darurat' atau 'Laptop Baru'. "
            "Tujuan yang jelas membuat kamu lebih termotivasi untuk konsisten.",
        ],
    },
    {
        "id": "anggaran-bulanan",
        "title": "Membuat Anggaran Bulanan",
        "icon": "bi-calendar-check",
        "tag": "Anggaran",
        "excerpt": "Metode 50/30/20 dan cara menyesuaikannya dengan kondisimu.",
        "paragraphs": [
            "Anggaran bulanan adalah rencana pembagian uang sebelum kamu membelanjakannya. "
            "Metode 50/30/20 membagi pemasukan menjadi 50% kebutuhan, 30% keinginan, dan 20% "
            "tabungan.",
            "Jika kebutuhanmu lebih besar dari 50%, misalnya karena biaya kos tinggi, ubah "
            "menjadi 60/20/20 atau 70/10/20. Yang penting porsi tabungan tetap ada.",
            "Evaluasi anggaran setiap akhir bulan lalu sesuaikan. Anggaran yang baik adalah "
            "anggaran yang realistis dan benar-benar kamu jalankan.",
        ],
    },
    {
        "id": "keuangan-mahasiswa",
        "title": "Mengelola Uang bagi Mahasiswa",
        "icon": "bi-mortarboard",
        "tag": "Mahasiswa",
        "excerpt": "Tips praktis mengatur uang saku agar cukup sampai akhir bulan.",
        "paragraphs": [
            "Bagi mahasiswa, uang saku sering datang sekaligus di awal bulan sehingga terasa "
            "banyak. Bagi menjadi empat bagian mingguan agar tidak habis di minggu pertama.",
            "Manfaatkan diskon pelajar, masak sendiri, dan patungan untuk fotokopi atau buku. "
            "Hemat kecil di banyak pos hasilnya terasa besar.",
            "Coba cari penghasilan tambahan seperti freelance atau mengajar privat, dan catat "
            "sebagai pemasukan terpisah agar kamu tahu kontribusinya terhadap keuanganmu.",
        ],
    },
]
