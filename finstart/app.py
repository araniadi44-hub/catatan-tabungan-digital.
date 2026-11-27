"""FinStart - Smart Money Management.

Aplikasi Flask + SQLite untuk membantu pemula mengelola keuangan bulanan.
Jalankan dengan:  python app.py   lalu buka http://127.0.0.1:5000
"""

import json
import os
import re
import sqlite3
from calendar import monthrange
from datetime import date, datetime, timedelta

from flask import (
    Flask, flash, g, jsonify, redirect, render_template, request, url_for,
)

from content import (
    ARTICLES, CATEGORY_ICONS, EXPENSE_CATEGORIES, GUIDE_STEPS,
    INCOME_CATEGORIES, MONTH_NAMES, NEEDS_CATEGORIES, WANTS_CATEGORIES,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

MAX_AMOUNT = 1_000_000_000_000  # batas wajar agar angka tidak meluap
WARNING_THRESHOLD = 80  # persen: anggaran dianggap hampir habis

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FINSTART_SECRET", "finstart-dev-key-ganti-di-produksi")


# ===========================================================================
# 1. DATABASE
# ===========================================================================
def get_db():
    """Ambil koneksi SQLite untuk request saat ini."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    type       TEXT    NOT NULL CHECK (type IN ('income', 'expense')),
    category   TEXT    NOT NULL,
    amount     INTEGER NOT NULL CHECK (amount > 0),
    date       TEXT    NOT NULL,
    note       TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (date);

CREATE TABLE IF NOT EXISTS budgets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    group_key  TEXT    NOT NULL UNIQUE CHECK (group_key IN ('needs', 'wants', 'savings')),
    percentage INTEGER NOT NULL CHECK (percentage BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS savings_goals (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    target_amount  INTEGER NOT NULL CHECK (target_amount > 0),
    initial_amount INTEGER NOT NULL DEFAULT 0 CHECK (initial_amount >= 0),
    created_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS savings_deposits (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL REFERENCES savings_goals (id) ON DELETE CASCADE,
    amount  INTEGER NOT NULL CHECK (amount > 0),
    date    TEXT    NOT NULL,
    note    TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_deposits_date ON savings_deposits (date);

CREATE TABLE IF NOT EXISTS guide_progress (
    step         INTEGER PRIMARY KEY,
    completed    INTEGER NOT NULL DEFAULT 0,
    checklist    TEXT    NOT NULL DEFAULT '[]',
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def init_db():
    """Buat tabel (jika belum ada) lalu isi data contoh sekali saja."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA)

    for key, pct in (("needs", 50), ("wants", 30), ("savings", 20)):
        db.execute("INSERT OR IGNORE INTO budgets (group_key, percentage) VALUES (?, ?)", (key, pct))
    for item in GUIDE_STEPS:
        db.execute("INSERT OR IGNORE INTO guide_progress (step) VALUES (?)", (item["step"],))

    seeded = db.execute("SELECT value FROM meta WHERE key = 'seeded'").fetchone()
    if not seeded:
        seed_sample_data(db)
        db.execute("INSERT INTO meta (key, value) VALUES ('seeded', '1')")
    db.commit()
    db.close()


def month_offset(year, month, offset):
    """Geser (year, month) sebanyak offset bulan, mis. -1 = bulan sebelumnya."""
    index = year * 12 + (month - 1) + offset
    return index // 12, index % 12 + 1


def seed_sample_data(db):
    """Data contoh agar dashboard tidak kosong saat pertama kali dibuka."""
    today = date.today()

    # (offset bulan, hari, nama, tipe, kategori, nominal, catatan)
    template = [
        (0, 1, "Uang saku bulanan", "income", "Uang saku", 2_000_000, "Dari orang tua"),
        (0, 3, "Proyek desain logo", "income", "Freelance", 500_000, ""),
        (0, 2, "Bayar kos", "expense", "Tagihan", 600_000, "Kos bulan ini"),
        (0, 4, "Makan siang kantin", "expense", "Makanan", 150_000, "Seminggu pertama"),
        (0, 6, "Isi kuota internet", "expense", "Tagihan", 75_000, ""),
        (0, 8, "Fotokopi modul", "expense", "Kebutuhan kuliah", 45_000, ""),
        (0, 10, "Ongkos ojek online", "expense", "Transportasi", 120_000, ""),
        (0, 12, "Nonton bioskop", "expense", "Hiburan", 60_000, "Bersama teman"),
        (0, 14, "Belanja bulanan", "expense", "Makanan", 230_000, ""),
        (0, 16, "Beli kaos", "expense", "Belanja", 110_000, "Diskon akhir pekan"),
        (0, 18, "Obat flu", "expense", "Kesehatan", 35_000, ""),
        (-1, 1, "Uang saku bulanan", "income", "Uang saku", 2_000_000, ""),
        (-1, 15, "Honor mengajar privat", "income", "Freelance", 400_000, ""),
        (-1, 2, "Bayar kos", "expense", "Tagihan", 600_000, ""),
        (-1, 5, "Belanja makanan", "expense", "Makanan", 620_000, ""),
        (-1, 9, "Transportasi", "expense", "Transportasi", 190_000, ""),
        (-1, 13, "Buku kuliah", "expense", "Kebutuhan kuliah", 150_000, ""),
        (-1, 20, "Langganan streaming", "expense", "Hiburan", 54_000, ""),
        (-1, 24, "Sepatu", "expense", "Belanja", 250_000, ""),
        (-2, 1, "Uang saku bulanan", "income", "Uang saku", 2_000_000, ""),
        (-2, 20, "Bonus lomba", "income", "Bonus", 300_000, ""),
        (-2, 2, "Bayar kos", "expense", "Tagihan", 600_000, ""),
        (-2, 7, "Belanja makanan", "expense", "Makanan", 580_000, ""),
        (-2, 11, "Transportasi", "expense", "Transportasi", 170_000, ""),
        (-2, 19, "Jalan-jalan", "expense", "Hiburan", 200_000, ""),
        (-3, 1, "Uang saku bulanan", "income", "Uang saku", 1_800_000, ""),
        (-3, 2, "Bayar kos", "expense", "Tagihan", 600_000, ""),
        (-3, 8, "Belanja makanan", "expense", "Makanan", 640_000, ""),
        (-3, 12, "Transportasi", "expense", "Transportasi", 160_000, ""),
        (-3, 22, "Belanja online", "expense", "Belanja", 180_000, ""),
        (-4, 1, "Uang saku bulanan", "income", "Uang saku", 1_800_000, ""),
        (-4, 10, "Proyek freelance", "income", "Freelance", 350_000, ""),
        (-4, 2, "Bayar kos", "expense", "Tagihan", 600_000, ""),
        (-4, 6, "Belanja makanan", "expense", "Makanan", 600_000, ""),
        (-4, 14, "Kesehatan", "expense", "Kesehatan", 90_000, "Periksa dokter"),
        (-5, 1, "Uang saku bulanan", "income", "Uang saku", 1_800_000, ""),
        (-5, 2, "Bayar kos", "expense", "Tagihan", 600_000, ""),
        (-5, 9, "Belanja makanan", "expense", "Makanan", 560_000, ""),
        (-5, 17, "Hiburan", "expense", "Hiburan", 120_000, ""),
    ]
    for offset, day, name, ttype, category, amount, note in template:
        year, month = month_offset(today.year, today.month, offset)
        day = min(day, monthrange(year, month)[1])
        tx_date = date(year, month, day)
        # Jangan buat transaksi di masa depan pada bulan berjalan
        if tx_date > today:
            tx_date = today
        db.execute(
            "INSERT INTO transactions (name, type, category, amount, date, note) VALUES (?, ?, ?, ?, ?, ?)",
            (name, ttype, category, amount, tx_date.isoformat(), note),
        )

    # Target tabungan + riwayat setoran
    cur = db.execute(
        "INSERT INTO savings_goals (name, target_amount, initial_amount) VALUES (?, ?, ?)",
        ("Laptop Baru", 8_000_000, 1_000_000),
    )
    laptop_id = cur.lastrowid
    cur = db.execute(
        "INSERT INTO savings_goals (name, target_amount, initial_amount) VALUES (?, ?, ?)",
        ("Dana Darurat", 3_000_000, 500_000),
    )
    emergency_id = cur.lastrowid

    deposits = [
        (laptop_id, -2, 5, 300_000, "Setoran bulanan"),
        (laptop_id, -1, 5, 300_000, "Setoran bulanan"),
        (emergency_id, -1, 6, 150_000, ""),
        (laptop_id, 0, 1, 300_000, "Setoran bulanan"),
        (emergency_id, 0, 1, 100_000, ""),
    ]
    for goal_id, offset, day, amount, note in deposits:
        year, month = month_offset(today.year, today.month, offset)
        day = min(day, monthrange(year, month)[1])
        dep_date = min(date(year, month, day), today)
        db.execute(
            "INSERT INTO savings_deposits (goal_id, amount, date, note) VALUES (?, ?, ?, ?)",
            (goal_id, amount, dep_date.isoformat(), note),
        )


# ===========================================================================
# 2. VALIDASI & FORMAT
# ===========================================================================
class ValidationError(Exception):
    """Dilempar saat input pengguna tidak valid; pesannya aman ditampilkan."""


def parse_amount(raw, field="Nominal", allow_zero=False):
    """Ubah teks nominal menjadi integer rupiah. Menerima '1500000' atau '1.500.000'."""
    text = (raw or "").strip().replace(" ", "")
    text = re.sub(r"^rp\.?", "", text, flags=re.IGNORECASE)
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", text):
        text = text.replace(".", "")
    if not re.fullmatch(r"\d+", text):
        raise ValidationError(f"{field} harus berupa angka bulat positif (tanpa koma/huruf).")
    value = int(text)
    if value == 0 and not allow_zero:
        raise ValidationError(f"{field} harus lebih besar dari nol.")
    if value > MAX_AMOUNT:
        raise ValidationError(f"{field} terlalu besar.")
    return value


def parse_date(raw, field="Tanggal"):
    """Validasi tanggal format YYYY-MM-DD dan kembalikan string ISO."""
    text = (raw or "").strip()
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(f"{field} tidak valid. Gunakan format tahun-bulan-hari.")
    if parsed.year < 2000 or parsed.year > 2100:
        raise ValidationError(f"{field} harus di antara tahun 2000 dan 2100.")
    return parsed.isoformat()


def parse_name(raw, field="Nama", max_len=80):
    text = (raw or "").strip()
    if not text:
        raise ValidationError(f"{field} tidak boleh kosong.")
    if len(text) > max_len:
        raise ValidationError(f"{field} maksimal {max_len} karakter.")
    return text


def parse_note(raw, max_len=200):
    text = (raw or "").strip()
    if len(text) > max_len:
        raise ValidationError(f"Catatan maksimal {max_len} karakter.")
    return text


def format_rupiah(value):
    """12345 -> 'Rp 12.345' (negatif -> '-Rp 12.345')."""
    try:
        number = int(round(float(value or 0)))
    except (TypeError, ValueError):
        number = 0
    sign = "-" if number < 0 else ""
    return f"{sign}Rp {abs(number):,}".replace(",", ".")


def format_date_id(iso_date):
    """'2026-11-27' -> '27 Nov 2026'."""
    try:
        parsed = datetime.strptime(iso_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return iso_date or ""
    return f"{parsed.day} {MONTH_NAMES[parsed.month][:3]} {parsed.year}"


app.jinja_env.filters["rupiah"] = format_rupiah
app.jinja_env.filters["tanggal"] = format_date_id


def safe_next(target, fallback):
    """Hanya izinkan redirect ke path internal (cegah open redirect)."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return fallback


# ===========================================================================
# 3. PERIODE (FILTER BULAN & TAHUN)
# ===========================================================================
def get_period(default_all=False):
    """Baca ?month=&year= dari URL. month/year 0 berarti 'semua' (jika diizinkan)."""
    today = date.today()

    def read(name, low, high, default):
        raw = request.args.get(name, "").strip()
        if raw == "":
            return default
        try:
            value = int(raw)
        except ValueError:
            return default
        if value == 0 and default_all:
            return 0
        return value if low <= value <= high else default

    month = read("month", 1, 12, today.month)
    year = read("year", 2000, 2100, today.year)
    return month, year


def period_bounds(month, year):
    """Kembalikan (awal, akhir_eksklusif) string tanggal untuk satu bulan."""
    next_year, next_month = month_offset(year, month, 1)
    return f"{year}-{month:02d}-01", f"{next_year}-{next_month:02d}-01"


def period_label(month, year):
    if month and year:
        return f"{MONTH_NAMES[month]} {year}"
    if year:
        return f"Tahun {year}"
    if month:
        return f"Bulan {MONTH_NAMES[month]} (semua tahun)"
    return "Semua waktu"


# ===========================================================================
# 4. PERHITUNGAN KEUANGAN
# ===========================================================================
def get_summary(db, month, year):
    """Ringkasan bulan terpilih.

    Sisa saldo = pemasukan - pengeluaran - dana yang dialokasikan ke tabungan.
    Setoran tabungan disimpan di tabel terpisah sehingga TIDAK pernah ikut
    dihitung sebagai pengeluaran konsumtif dan tidak terhitung dua kali.
    """
    start, end = period_bounds(month, year)
    row = db.execute(
        """SELECT
               COALESCE(SUM(CASE WHEN type = 'income'  THEN amount END), 0) AS income,
               COALESCE(SUM(CASE WHEN type = 'expense' THEN amount END), 0) AS expense
           FROM transactions WHERE date >= ? AND date < ?""",
        (start, end),
    ).fetchone()
    income, expense = row["income"], row["expense"]

    saved_month = db.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM savings_deposits WHERE date >= ? AND date < ?",
        (start, end),
    ).fetchone()["total"]

    savings_total = get_total_savings(db)
    return {
        "income": income,
        "expense": expense,
        "saved_month": saved_month,
        "savings_total": savings_total,
        "balance": income - expense - saved_month,
    }


def get_total_savings(db):
    """Total seluruh tabungan = saldo awal semua target + semua setoran."""
    initial = db.execute("SELECT COALESCE(SUM(initial_amount), 0) AS t FROM savings_goals").fetchone()["t"]
    deposits = db.execute("SELECT COALESCE(SUM(amount), 0) AS t FROM savings_deposits").fetchone()["t"]
    return initial + deposits


def get_budget_percentages(db):
    rows = db.execute("SELECT group_key, percentage FROM budgets").fetchall()
    result = {"needs": 50, "wants": 30, "savings": 20}
    result.update({r["group_key"]: r["percentage"] for r in rows})
    return result


def budget_status(spent, allocated):
    """Hitung persentase pemakaian dan status: ok / warning / over."""
    if allocated <= 0:
        percent = 0 if spent <= 0 else 100
        status = "ok" if spent <= 0 else "over"
        return percent, status
    percent = round(spent / allocated * 100, 1)
    if spent > allocated:
        return percent, "over"
    if percent >= WARNING_THRESHOLD:
        return percent, "warning"
    return percent, "ok"


def get_budget_report(db, month, year):
    """Alokasi anggaran 50/30/20 (atau kustom) vs realisasi bulan terpilih."""
    start, end = period_bounds(month, year)
    percentages = get_budget_percentages(db)
    summary = get_summary(db, month, year)
    income = summary["income"]

    def spent_in(categories):
        marks = ",".join("?" for _ in categories)
        row = db.execute(
            f"""SELECT COALESCE(SUM(amount), 0) AS total FROM transactions
                WHERE type = 'expense' AND date >= ? AND date < ? AND category IN ({marks})""",
            (start, end, *categories),
        ).fetchone()
        return row["total"]

    groups = {
        "needs": {"label": "Kebutuhan", "icon": "bi-house-heart", "spent": spent_in(NEEDS_CATEGORIES),
                  "categories": NEEDS_CATEGORIES},
        "wants": {"label": "Keinginan", "icon": "bi-stars", "spent": spent_in(WANTS_CATEGORIES),
                  "categories": WANTS_CATEGORIES},
        # Untuk kelompok tabungan, realisasi = setoran ke target tabungan bulan ini
        "savings": {"label": "Tabungan", "icon": "bi-piggy-bank", "spent": summary["saved_month"],
                    "categories": []},
    }
    for key, group in groups.items():
        group["percentage"] = percentages[key]
        group["allocated"] = income * percentages[key] // 100
        group["remaining"] = group["allocated"] - group["spent"]
        group["used_percent"], group["status"] = budget_status(group["spent"], group["allocated"])
        group["key"] = key

    # Pemakaian anggaran gabungan (kebutuhan + keinginan) untuk kartu dashboard
    spend_alloc = groups["needs"]["allocated"] + groups["wants"]["allocated"]
    spend_used = groups["needs"]["spent"] + groups["wants"]["spent"]
    overall_percent, overall_status = budget_status(spend_used, spend_alloc)

    return {
        "income": income,
        "groups": groups,
        "percentages": percentages,
        "overall_percent": overall_percent,
        "overall_status": overall_status,
        "overall_spent": spend_used,
        "overall_allocated": spend_alloc,
    }


def get_chart_data(db, month, year):
    """Data grafik: tren 6 bulan terakhir dan pengeluaran per kategori."""
    labels, income_series, expense_series = [], [], []
    for offset in range(-5, 1):
        y, m = month_offset(year, month, offset)
        start, end = period_bounds(m, y)
        row = db.execute(
            """SELECT
                   COALESCE(SUM(CASE WHEN type = 'income'  THEN amount END), 0) AS income,
                   COALESCE(SUM(CASE WHEN type = 'expense' THEN amount END), 0) AS expense
               FROM transactions WHERE date >= ? AND date < ?""",
            (start, end),
        ).fetchone()
        labels.append(f"{MONTH_NAMES[m][:3]} {str(y)[2:]}")
        income_series.append(row["income"])
        expense_series.append(row["expense"])

    start, end = period_bounds(month, year)
    rows = db.execute(
        """SELECT category, SUM(amount) AS total FROM transactions
           WHERE type = 'expense' AND date >= ? AND date < ?
           GROUP BY category ORDER BY total DESC""",
        (start, end),
    ).fetchall()

    return {
        "trend": {"labels": labels, "income": income_series, "expense": expense_series},
        "categories": {"labels": [r["category"] for r in rows], "values": [r["total"] for r in rows]},
    }


def get_goals(db):
    """Daftar target tabungan lengkap dengan progres dan riwayat setoran."""
    goals = []
    for row in db.execute("SELECT * FROM savings_goals ORDER BY id DESC").fetchall():
        deposits = db.execute(
            "SELECT * FROM savings_deposits WHERE goal_id = ? ORDER BY date DESC, id DESC",
            (row["id"],),
        ).fetchall()
        deposited = sum(d["amount"] for d in deposits)
        current = row["initial_amount"] + deposited
        target = row["target_amount"]
        goals.append({
            "id": row["id"],
            "name": row["name"],
            "target": target,
            "initial": row["initial_amount"],
            "deposited": deposited,
            "current": current,
            "remaining": max(target - current, 0),
            "percent": min(round(current / target * 100, 1), 100),
            "done": current >= target,
            "deposits": deposits,
        })
    return goals


# ===========================================================================
# 5. KONTEKS TEMPLATE
# ===========================================================================
@app.context_processor
def inject_globals():
    today = date.today()
    db = get_db()
    row = db.execute("SELECT MIN(date) AS first FROM transactions").fetchone()
    first_year = today.year - 1
    if row and row["first"]:
        first_year = min(first_year, int(row["first"][:4]))
    years = list(range(first_year, today.year + 2))
    return {
        "months": MONTH_NAMES,
        "years": years,
        "today": today.isoformat(),
        "income_categories": INCOME_CATEGORIES,
        "expense_categories": EXPENSE_CATEGORIES,
        "category_icons": CATEGORY_ICONS,
    }


# ===========================================================================
# 6. HALAMAN: DASHBOARD
# ===========================================================================
@app.route("/")
def dashboard():
    db = get_db()
    month, year = get_period()
    summary = get_summary(db, month, year)
    budget = get_budget_report(db, month, year)
    start, end = period_bounds(month, year)

    recent = db.execute(
        "SELECT * FROM transactions WHERE date >= ? AND date < ? ORDER BY date DESC, id DESC LIMIT 6",
        (start, end),
    ).fetchall()
    top_goals = get_goals(db)[:3]

    return render_template(
        "dashboard.html",
        page="dashboard",
        month=month,
        year=year,
        label=period_label(month, year),
        summary=summary,
        budget=budget,
        recent=recent,
        goals=top_goals,
    )


@app.route("/api/dashboard")
def api_dashboard():
    """Sumber data grafik dan kartu ringkasan (dibaca JavaScript)."""
    db = get_db()
    month, year = get_period()
    return jsonify({
        "month": month,
        "year": year,
        "label": period_label(month, year),
        "summary": get_summary(db, month, year),
        "charts": get_chart_data(db, month, year),
    })


# ===========================================================================
# 7. HALAMAN: TRANSAKSI (tambah, ubah, hapus, cari, filter)
# ===========================================================================
def validate_transaction_form(form):
    """Validasi form transaksi; kembalikan dict siap simpan atau lempar ValidationError."""
    ttype = form.get("type", "")
    if ttype not in ("income", "expense"):
        raise ValidationError("Jenis transaksi harus pemasukan atau pengeluaran.")
    allowed = INCOME_CATEGORIES if ttype == "income" else EXPENSE_CATEGORIES
    category = form.get("category", "")
    if category not in allowed:
        raise ValidationError("Kategori tidak sesuai dengan jenis transaksi.")
    return {
        "name": parse_name(form.get("name"), "Nama transaksi"),
        "type": ttype,
        "category": category,
        "amount": parse_amount(form.get("amount")),
        "date": parse_date(form.get("date")),
        "note": parse_note(form.get("note")),
    }


@app.route("/transactions")
def transactions():
    db = get_db()
    month, year = get_period(default_all=True)
    query = request.args.get("q", "").strip()
    ttype = request.args.get("type", "")
    category = request.args.get("category", "")

    where, params = [], []
    if year:
        if month:
            start, end = period_bounds(month, year)
            where.append("date >= ? AND date < ?")
            params += [start, end]
        else:
            where.append("date >= ? AND date < ?")
            params += [f"{year}-01-01", f"{year + 1}-01-01"]
    elif month:
        where.append("substr(date, 6, 2) = ?")
        params.append(f"{month:02d}")
    if ttype in ("income", "expense"):
        where.append("type = ?")
        params.append(ttype)
    if category:
        where.append("category = ?")
        params.append(category)
    if query:
        like = f"%{query}%"
        where.append("(name LIKE ? OR note LIKE ? OR category LIKE ?)")
        params += [like, like, like]

    clause = ("WHERE " + " AND ".join(where)) if where else ""
    rows = db.execute(
        f"SELECT * FROM transactions {clause} ORDER BY date DESC, id DESC", params
    ).fetchall()

    total_income = sum(r["amount"] for r in rows if r["type"] == "income")
    total_expense = sum(r["amount"] for r in rows if r["type"] == "expense")

    return render_template(
        "transactions.html",
        page="transactions",
        rows=rows,
        month=month,
        year=year,
        q=query,
        ttype=ttype,
        category=category,
        total_income=total_income,
        total_expense=total_expense,
        label=period_label(month, year),
        all_categories=sorted(set(INCOME_CATEGORIES + EXPENSE_CATEGORIES)),
        current_url=request.full_path.rstrip("?"),
    )


@app.route("/transactions/add", methods=["POST"])
def add_transaction():
    target = safe_next(request.form.get("next"), url_for("transactions"))
    try:
        data = validate_transaction_form(request.form)
        db = get_db()
        db.execute(
            "INSERT INTO transactions (name, type, category, amount, date, note) VALUES (?, ?, ?, ?, ?, ?)",
            (data["name"], data["type"], data["category"], data["amount"], data["date"], data["note"]),
        )
        db.commit()
        flash("Transaksi berhasil ditambahkan.", "success")
    except ValidationError as error:
        flash(str(error), "error")
    return redirect(target)


@app.route("/transactions/<int:tx_id>/edit", methods=["POST"])
def edit_transaction(tx_id):
    target = safe_next(request.form.get("next"), url_for("transactions"))
    db = get_db()
    if not db.execute("SELECT 1 FROM transactions WHERE id = ?", (tx_id,)).fetchone():
        flash("Transaksi tidak ditemukan.", "error")
        return redirect(target)
    try:
        data = validate_transaction_form(request.form)
        db.execute(
            """UPDATE transactions
               SET name = ?, type = ?, category = ?, amount = ?, date = ?, note = ?
               WHERE id = ?""",
            (data["name"], data["type"], data["category"], data["amount"], data["date"], data["note"], tx_id),
        )
        db.commit()
        flash("Transaksi berhasil diperbarui.", "success")
    except ValidationError as error:
        flash(str(error), "error")
    return redirect(target)


@app.route("/transactions/<int:tx_id>/delete", methods=["POST"])
def delete_transaction(tx_id):
    target = safe_next(request.form.get("next"), url_for("transactions"))
    db = get_db()
    cur = db.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    db.commit()
    if cur.rowcount:
        flash("Transaksi berhasil dihapus.", "success")
    else:
        flash("Transaksi tidak ditemukan.", "error")
    return redirect(target)


# ===========================================================================
# 8. HALAMAN: ANGGARAN (BUDGET PLANNER)
# ===========================================================================
@app.route("/budget")
def budget():
    db = get_db()
    month, year = get_period()
    report = get_budget_report(db, month, year)
    return render_template(
        "budget.html",
        page="budget",
        month=month,
        year=year,
        label=period_label(month, year),
        report=report,
    )


@app.route("/budget/save", methods=["POST"])
def save_budget():
    month = request.form.get("month", "")
    year = request.form.get("year", "")
    target = url_for("budget", month=month, year=year) if month and year else url_for("budget")
    try:
        values = {}
        for key, label in (("needs", "Kebutuhan"), ("wants", "Keinginan"), ("savings", "Tabungan")):
            raw = (request.form.get(key) or "").strip()
            if not re.fullmatch(r"\d{1,3}", raw) or int(raw) > 100:
                raise ValidationError(f"Persentase {label} harus angka bulat 0-100.")
            values[key] = int(raw)
        total = sum(values.values())
        if total != 100:
            raise ValidationError(f"Total persentase harus tepat 100% (saat ini {total}%).")
        db = get_db()
        for key, pct in values.items():
            db.execute("UPDATE budgets SET percentage = ? WHERE group_key = ?", (pct, key))
        db.commit()
        flash("Pengaturan anggaran berhasil disimpan.", "success")
    except ValidationError as error:
        flash(str(error), "error")
    return redirect(target)


# ===========================================================================
# 9. HALAMAN: TARGET TABUNGAN
# ===========================================================================
@app.route("/savings")
def savings():
    db = get_db()
    return render_template(
        "savings.html",
        page="savings",
        goals=get_goals(db),
        total_savings=get_total_savings(db),
    )


@app.route("/savings/add", methods=["POST"])
def add_goal():
    try:
        name = parse_name(request.form.get("name"), "Nama target", 60)
        target = parse_amount(request.form.get("target"), "Nominal target")
        initial = parse_amount(request.form.get("initial") or "0", "Saldo awal", allow_zero=True)
        db = get_db()
        db.execute(
            "INSERT INTO savings_goals (name, target_amount, initial_amount) VALUES (?, ?, ?)",
            (name, target, initial),
        )
        db.commit()
        flash("Target tabungan berhasil dibuat.", "success")
    except ValidationError as error:
        flash(str(error), "error")
    return redirect(url_for("savings"))


@app.route("/savings/<int:goal_id>/deposit", methods=["POST"])
def add_deposit(goal_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM savings_goals WHERE id = ?", (goal_id,)).fetchone():
        flash("Target tabungan tidak ditemukan.", "error")
        return redirect(url_for("savings"))
    try:
        amount = parse_amount(request.form.get("amount"), "Nominal setoran")
        dep_date = parse_date(request.form.get("date") or date.today().isoformat())
        note = parse_note(request.form.get("note"))
        db.execute(
            "INSERT INTO savings_deposits (goal_id, amount, date, note) VALUES (?, ?, ?, ?)",
            (goal_id, amount, dep_date, note),
        )
        db.commit()
        flash("Dana tabungan berhasil ditambahkan.", "success")
    except ValidationError as error:
        flash(str(error), "error")
    return redirect(url_for("savings"))


@app.route("/savings/<int:goal_id>/delete", methods=["POST"])
def delete_goal(goal_id):
    db = get_db()
    cur = db.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
    db.commit()
    flash("Target tabungan dihapus." if cur.rowcount else "Target tabungan tidak ditemukan.",
          "success" if cur.rowcount else "error")
    return redirect(url_for("savings"))


@app.route("/savings/deposit/<int:deposit_id>/delete", methods=["POST"])
def delete_deposit(deposit_id):
    db = get_db()
    cur = db.execute("DELETE FROM savings_deposits WHERE id = ?", (deposit_id,))
    db.commit()
    flash("Setoran dihapus." if cur.rowcount else "Setoran tidak ditemukan.",
          "success" if cur.rowcount else "error")
    return redirect(url_for("savings"))


# ===========================================================================
# 10. HALAMAN: PANDUAN KEUANGAN
# ===========================================================================
def get_guide_state(db):
    rows = db.execute("SELECT * FROM guide_progress").fetchall()
    state = {}
    for row in rows:
        try:
            checked = json.loads(row["checklist"])
        except (TypeError, ValueError):
            checked = []
        state[row["step"]] = {"completed": bool(row["completed"]), "checked": checked}
    return state


@app.route("/guide")
def guide():
    db = get_db()
    state = get_guide_state(db)
    done = sum(1 for s in state.values() if s["completed"])
    return render_template(
        "guide.html",
        page="guide",
        steps=GUIDE_STEPS,
        state=state,
        done=done,
        total=len(GUIDE_STEPS),
    )


def valid_step(step):
    return any(item["step"] == step for item in GUIDE_STEPS)


@app.route("/api/guide/<int:step>/check", methods=["POST"])
def api_guide_check(step):
    """Simpan status centang satu item checklist."""
    if not valid_step(step):
        return jsonify({"ok": False, "error": "Langkah tidak ditemukan."}), 404
    payload = request.get_json(silent=True) or {}
    index = payload.get("index")
    checked = bool(payload.get("checked"))
    items = next(i for i in GUIDE_STEPS if i["step"] == step)["checklist"]
    if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(items):
        return jsonify({"ok": False, "error": "Item checklist tidak valid."}), 400

    db = get_db()
    row = db.execute("SELECT checklist FROM guide_progress WHERE step = ?", (step,)).fetchone()
    current = set(json.loads(row["checklist"])) if row else set()
    if checked:
        current.add(index)
    else:
        current.discard(index)
    db.execute("UPDATE guide_progress SET checklist = ? WHERE step = ?", (json.dumps(sorted(current)), step))
    db.commit()
    return jsonify({"ok": True, "checked": sorted(current)})


@app.route("/api/guide/<int:step>/complete", methods=["POST"])
def api_guide_complete(step):
    """Tandai langkah selesai atau batalkan penandaan."""
    if not valid_step(step):
        return jsonify({"ok": False, "error": "Langkah tidak ditemukan."}), 404
    payload = request.get_json(silent=True) or {}
    completed = bool(payload.get("completed"))
    db = get_db()
    db.execute(
        "UPDATE guide_progress SET completed = ?, completed_at = ? WHERE step = ?",
        (1 if completed else 0, datetime.now().isoformat(timespec="seconds") if completed else None, step),
    )
    db.commit()
    state = get_guide_state(db)
    done = sum(1 for s in state.values() if s["completed"])
    return jsonify({"ok": True, "completed": completed, "done": done, "total": len(GUIDE_STEPS)})


# ===========================================================================
# 11. HALAMAN: EDUKASI & KALKULATOR
# ===========================================================================
@app.route("/education")
def education():
    return render_template("education.html", page="education", articles=ARTICLES)


@app.route("/calculator")
def calculator():
    return render_template("calculator.html", page="calculator")


def calc_budget_split(data):
    income = parse_amount(data.get("income"), "Pemasukan")
    needs = int(data.get("needs", 50))
    wants = int(data.get("wants", 30))
    savings_pct = int(data.get("savings", 20))
    if min(needs, wants, savings_pct) < 0 or needs + wants + savings_pct != 100:
        raise ValidationError("Total persentase harus tepat 100%.")
    needs_amount = income * needs // 100
    wants_amount = income * wants // 100
    savings_amount = income - needs_amount - wants_amount  # sisa pembulatan masuk tabungan
    return {
        "needs": needs_amount, "wants": wants_amount, "savings": savings_amount,
        "needs_pct": needs, "wants_pct": wants, "savings_pct": savings_pct,
    }


def calc_saving_goal(data):
    target = parse_amount(data.get("target"), "Target tabungan")
    current = parse_amount(data.get("current") or "0", "Tabungan saat ini", allow_zero=True)
    months = parse_amount(data.get("months"), "Jangka waktu (bulan)")
    if months > 1200:
        raise ValidationError("Jangka waktu maksimal 1200 bulan.")
    remaining = max(target - current, 0)
    per_month = -(-remaining // months)  # pembulatan ke atas supaya target pasti tercapai
    return {
        "remaining": remaining,
        "per_month": per_month,
        "per_week": -(-remaining // (months * 52 // 12 or 1)),
        "per_day": -(-remaining // (months * 30)),
        "reached": current >= target,
        "percent": min(round(current / target * 100, 1), 100),
    }


def calc_leftover(data):
    income = parse_amount(data.get("income"), "Pemasukan")
    fixed = parse_amount(data.get("fixed") or "0", "Pengeluaran wajib", allow_zero=True)
    variable = parse_amount(data.get("variable") or "0", "Pengeluaran lainnya", allow_zero=True)
    savings_amount = parse_amount(data.get("savings") or "0", "Tabungan", allow_zero=True)
    leftover = income - fixed - variable - savings_amount
    return {
        "leftover": leftover,
        "total_out": fixed + variable + savings_amount,
        "negative": leftover < 0,
    }


def calc_daily_limit(data):
    available = parse_amount(data.get("available"), "Uang tersedia")
    fixed = parse_amount(data.get("fixed") or "0", "Kebutuhan wajib tersisa", allow_zero=True)
    savings_amount = parse_amount(data.get("savings") or "0", "Tabungan", allow_zero=True)
    days = parse_amount(data.get("days"), "Jumlah hari")
    if days > 366:
        raise ValidationError("Jumlah hari maksimal 366.")
    free_money = available - fixed - savings_amount
    return {
        "free_money": free_money,
        "daily": max(free_money, 0) // days,
        "weekly": max(free_money, 0) // days * 7,
        "negative": free_money < 0,
    }


CALCULATORS = {
    "budget": calc_budget_split,
    "saving": calc_saving_goal,
    "leftover": calc_leftover,
    "daily": calc_daily_limit,
}


@app.route("/api/calc/<kind>", methods=["POST"])
def api_calc(kind):
    handler = CALCULATORS.get(kind)
    if handler is None:
        return jsonify({"ok": False, "error": "Jenis kalkulator tidak dikenal."}), 404
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"ok": False, "error": "Data tidak valid."}), 400
    # Ubah semua nilai menjadi string agar parser nominal konsisten
    clean = {k: (str(v) if not isinstance(v, str) else v) for k, v in data.items()}
    try:
        return jsonify({"ok": True, "result": handler(clean)})
    except ValidationError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Masukkan angka yang valid."}), 400


# ===========================================================================
# 12. PENANGANAN ERROR
# ===========================================================================
@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "Tidak ditemukan."}), 404
    return render_template("error.html", page="", code=404,
                           message="Halaman yang kamu cari tidak ditemukan."), 404


@app.errorhandler(405)
def method_not_allowed(_error):
    return render_template("error.html", page="", code=405,
                           message="Metode permintaan tidak diizinkan."), 405


@app.errorhandler(500)
def server_error(_error):
    return render_template("error.html", page="", code=500,
                           message="Terjadi kesalahan pada server. Coba muat ulang halaman."), 500


# Pastikan database ada setiap kali modul dimuat (python app.py maupun flask run)
init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
