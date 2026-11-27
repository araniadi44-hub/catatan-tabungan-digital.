/* FinStart – interaksi halaman (JavaScript biasa, tanpa framework). */
const FinStart = (function () {
    "use strict";

    // ------------------------------------------------------------------
    // Utilitas
    // ------------------------------------------------------------------
    function rupiah(value) {
        const n = Math.round(Number(value) || 0);
        const text = Math.abs(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
        return (n < 0 ? "-Rp " : "Rp ") + text;
    }

    function postJSON(url, payload) {
        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        }).then(function (res) {
            return res.json().then(function (data) { return { status: res.status, data: data }; });
        });
    }

    // ------------------------------------------------------------------
    // Navigasi sidebar (mobile) & pesan flash
    // ------------------------------------------------------------------
    function initChrome() {
        const sidebar = document.getElementById("sidebar");
        const backdrop = document.getElementById("backdrop");
        const toggle = document.getElementById("menuToggle");

        function setMenu(open) {
            sidebar.classList.toggle("open", open);
            backdrop.classList.toggle("show", open);
        }
        if (toggle) toggle.addEventListener("click", function () { setMenu(!sidebar.classList.contains("open")); });
        if (backdrop) backdrop.addEventListener("click", function () { setMenu(false); });

        document.querySelectorAll(".flash-close").forEach(function (btn) {
            btn.addEventListener("click", function () { btn.closest(".flash").remove(); });
        });
        document.querySelectorAll(".flash-success").forEach(function (el) {
            setTimeout(function () { el.remove(); }, 5000);
        });

        document.querySelectorAll("[data-autosubmit]").forEach(function (el) {
            el.addEventListener("change", function () { el.form.submit(); });
        });

        document.querySelectorAll("form[data-confirm]").forEach(function (form) {
            form.addEventListener("submit", function (event) {
                if (!window.confirm(form.dataset.confirm)) event.preventDefault();
            });
        });
    }

    // ------------------------------------------------------------------
    // Modal transaksi (tambah & ubah)
    // ------------------------------------------------------------------
    function initTransactionModal() {
        const modal = document.getElementById("txModal");
        if (!modal) return;
        const form = document.getElementById("txForm");
        const title = document.getElementById("txModalTitle");
        const categorySelect = document.getElementById("txCategory");
        const categories = {
            income: JSON.parse(form.dataset.income),
            expense: JSON.parse(form.dataset.expense),
        };

        function fillCategories(type, selected) {
            categorySelect.innerHTML = "";
            categories[type].forEach(function (name) {
                const option = document.createElement("option");
                option.value = name;
                option.textContent = name;
                if (name === selected) option.selected = true;
                categorySelect.appendChild(option);
            });
        }
        function currentType() {
            return form.querySelector('input[name="type"]:checked').value;
        }
        function open() {
            modal.hidden = false;
            document.body.style.overflow = "hidden";
            document.getElementById("txName").focus();
        }
        function close() {
            modal.hidden = true;
            document.body.style.overflow = "";
        }

        function openAdd() {
            form.reset();
            form.action = form.dataset.addAction;
            title.textContent = "Tambah Transaksi";
            form.querySelector('input[name="type"][value="expense"]').checked = true;
            fillCategories("expense");
            open();
        }
        function openEdit(data) {
            form.reset();
            form.action = form.dataset.editAction.replace("/0/", "/" + data.id + "/");
            title.textContent = "Ubah Transaksi";
            form.querySelector('input[name="type"][value="' + data.type + '"]').checked = true;
            fillCategories(data.type, data.category);
            document.getElementById("txName").value = data.name;
            document.getElementById("txDate").value = data.date;
            document.getElementById("txAmount").value = data.amount;
            document.getElementById("txNote").value = data.note || "";
            open();
        }

        form.querySelectorAll('input[name="type"]').forEach(function (radio) {
            radio.addEventListener("change", function () { fillCategories(currentType()); });
        });
        document.querySelectorAll("[data-open-tx]").forEach(function (btn) {
            btn.addEventListener("click", openAdd);
        });
        document.querySelectorAll("[data-edit-tx]").forEach(function (btn) {
            btn.addEventListener("click", function () { openEdit(btn.dataset); });
        });
        modal.querySelectorAll("[data-close-modal]").forEach(function (btn) {
            btn.addEventListener("click", close);
        });
        modal.addEventListener("click", function (event) { if (event.target === modal) close(); });
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && !modal.hidden) close();
        });

        fillCategories("expense");
    }

    // ------------------------------------------------------------------
    // Dashboard: ambil data dari API lalu gambar grafik Chart.js
    // ------------------------------------------------------------------
    function initDashboardCharts(month, year) {
        const trendCanvas = document.getElementById("trendChart");
        const categoryCanvas = document.getElementById("categoryChart");
        if (!trendCanvas || typeof Chart === "undefined") return;

        const GREEN = "#15a05a";
        const NAVY = "#0f2a47";
        const PALETTE = ["#0f2a47", "#15a05a", "#2f6fa8", "#6cc49a", "#0d7c85", "#8aa4c0", "#d98a0b", "#9b6bd6"];

        fetch("/api/dashboard?month=" + month + "&year=" + year)
            .then(function (res) { return res.json(); })
            .then(function (data) {
                // Sinkronkan kartu ringkasan dengan angka terbaru dari database
                const s = data.summary;
                setText("statIncome", rupiah(s.income));
                setText("statExpense", rupiah(s.expense));
                setText("statSavings", rupiah(s.savings_total));
                setText("statBalance", rupiah(s.balance));

                const trend = data.charts.trend;
                new Chart(trendCanvas, {
                    type: "bar",
                    data: {
                        labels: trend.labels,
                        datasets: [
                            { label: "Pemasukan", data: trend.income, backgroundColor: GREEN, borderRadius: 6 },
                            { label: "Pengeluaran", data: trend.expense, backgroundColor: NAVY, borderRadius: 6 },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: "bottom" },
                            tooltip: { callbacks: { label: function (c) { return c.dataset.label + ": " + rupiah(c.parsed.y); } } },
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { callback: function (v) { return v >= 1000000 ? (v / 1000000) + " jt" : v >= 1000 ? (v / 1000) + " rb" : v; } },
                            },
                            x: { grid: { display: false } },
                        },
                    },
                });

                const cat = data.charts.categories;
                if (!cat.values.length) {
                    categoryCanvas.parentElement.hidden = true;
                    document.getElementById("categoryEmpty").hidden = false;
                    return;
                }
                new Chart(categoryCanvas, {
                    type: "doughnut",
                    data: {
                        labels: cat.labels,
                        datasets: [{ data: cat.values, backgroundColor: PALETTE.slice(0, cat.values.length), borderWidth: 2, borderColor: "#fff" }],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: "62%",
                        plugins: {
                            legend: { position: "right" },
                            tooltip: { callbacks: { label: function (c) { return c.label + ": " + rupiah(c.parsed); } } },
                        },
                    },
                });
            })
            .catch(function () {
                trendCanvas.parentElement.innerHTML = '<p class="empty-note">Grafik gagal dimuat. Muat ulang halaman.</p>';
            });
    }

    function setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    // ------------------------------------------------------------------
    // Budget planner: total persentase langsung & tombol reset
    // ------------------------------------------------------------------
    function initBudgetForm() {
        const form = document.getElementById("budgetForm");
        if (!form) return;
        const fields = ["pctNeeds", "pctWants", "pctSavings"].map(function (id) { return document.getElementById(id); });
        const totalEl = document.getElementById("pctTotal");
        const box = document.getElementById("pctTotalBox");

        function update() {
            const total = fields.reduce(function (sum, f) { return sum + (parseInt(f.value, 10) || 0); }, 0);
            totalEl.textContent = total + "%";
            box.classList.toggle("invalid", total !== 100);
        }
        fields.forEach(function (f) { f.addEventListener("input", update); });
        document.getElementById("resetBudget").addEventListener("click", function () {
            fields[0].value = 50; fields[1].value = 30; fields[2].value = 20;
            update();
        });
        form.addEventListener("submit", function (event) {
            const total = fields.reduce(function (sum, f) { return sum + (parseInt(f.value, 10) || 0); }, 0);
            if (total !== 100) {
                event.preventDefault();
                window.alert("Total persentase harus tepat 100% (saat ini " + total + "%).");
            }
        });
        update();
    }

    // ------------------------------------------------------------------
    // Panduan keuangan: checklist & tombol tandai selesai (disimpan ke DB)
    // ------------------------------------------------------------------
    function initGuide() {
        const steps = document.querySelector(".steps");
        if (!steps) return;

        steps.querySelectorAll('input[type="checkbox"]').forEach(function (box) {
            box.addEventListener("change", function () {
                postJSON("/api/guide/" + box.dataset.step + "/check", {
                    index: parseInt(box.dataset.index, 10),
                    checked: box.checked,
                }).then(function (res) {
                    if (!res.data.ok) {
                        box.checked = !box.checked;
                        window.alert(res.data.error || "Gagal menyimpan checklist.");
                    }
                }).catch(function () {
                    box.checked = !box.checked;
                    window.alert("Gagal menyimpan checklist. Periksa koneksi ke server.");
                });
            });
        });

        steps.querySelectorAll(".complete-btn").forEach(function (btn) {
            btn.addEventListener("click", function () {
                const wantCompleted = btn.dataset.completed !== "true";
                postJSON("/api/guide/" + btn.dataset.step + "/complete", { completed: wantCompleted })
                    .then(function (res) {
                        if (!res.data.ok) { window.alert(res.data.error || "Gagal menyimpan."); return; }
                        applyStepState(btn, res.data.completed);
                        setText("guideDone", res.data.done);
                        document.getElementById("guideBar").style.width = Math.round(res.data.done / res.data.total * 100) + "%";
                    })
                    .catch(function () { window.alert("Gagal menyimpan. Periksa koneksi ke server."); });
            });
        });
    }

    function applyStepState(btn, completed) {
        const card = btn.closest(".step");
        card.classList.toggle("is-done", completed);
        card.querySelector(".step-badge").hidden = !completed;
        btn.dataset.completed = completed ? "true" : "false";
        btn.classList.toggle("btn-primary", !completed);
        btn.classList.toggle("btn-ghost", completed);
        btn.innerHTML = completed
            ? '<i class="bi bi-arrow-counterclockwise"></i> Batalkan tanda selesai'
            : '<i class="bi bi-check2-circle"></i> Tandai selesai';
    }

    // ------------------------------------------------------------------
    // Edukasi: buka/tutup artikel
    // ------------------------------------------------------------------
    function initArticles() {
        document.querySelectorAll(".toggle-article").forEach(function (btn) {
            btn.addEventListener("click", function () {
                const more = btn.closest(".article-card").querySelector(".article-more");
                const open = more.hidden;
                more.hidden = !open;
                btn.setAttribute("aria-expanded", String(open));
                btn.querySelector("span").textContent = open ? "Tutup" : "Baca selengkapnya";
                btn.querySelector("i").className = open ? "bi bi-chevron-up" : "bi bi-chevron-down";
            });
        });
    }

    // ------------------------------------------------------------------
    // Kalkulator: kirim ke /api/calc/<jenis> lalu tampilkan hasil
    // ------------------------------------------------------------------
    function row(label, value) {
        return "<div><dt>" + label + "</dt><dd>" + value + "</dd></div>";
    }

    const RENDERERS = {
        budget: function (r) {
            return {
                html: "<dl>" +
                    row("Kebutuhan (" + r.needs_pct + "%)", rupiah(r.needs)) +
                    row("Keinginan (" + r.wants_pct + "%)", rupiah(r.wants)) +
                    row("Tabungan (" + r.savings_pct + "%)", rupiah(r.savings)) + "</dl>",
            };
        },
        saving: function (r) {
            if (r.reached) {
                return { html: '<strong class="big">Target sudah tercapai 🎉</strong>' };
            }
            return {
                html: '<p>Kamu perlu menabung</p><strong class="big">' + rupiah(r.per_month) + " / bulan</strong><dl style=\"margin-top:10px\">" +
                    row("Sisa target", rupiah(r.remaining)) +
                    row("Setara per minggu", "± " + rupiah(r.per_week)) +
                    row("Setara per hari", "± " + rupiah(r.per_day)) +
                    row("Pencapaian saat ini", r.percent + "%") + "</dl>",
            };
        },
        leftover: function (r) {
            return {
                warn: r.negative,
                html: '<p>Sisa uang bulananmu</p><strong class="big">' + rupiah(r.leftover) + "</strong><dl style=\"margin-top:10px\">" +
                    row("Total keluar + tabungan", rupiah(r.total_out)) + "</dl>" +
                    (r.negative ? '<p class="calc-note status-text-over">Pengeluaranmu melebihi pemasukan. Kurangi pengeluaran atau tabungan.</p>' : ""),
            };
        },
        daily: function (r) {
            return {
                warn: r.negative,
                html: '<p>Batas pengeluaran harian</p><strong class="big">' + rupiah(r.daily) + " / hari</strong><dl style=\"margin-top:10px\">" +
                    row("Uang bebas dibelanjakan", rupiah(r.free_money)) +
                    row("Batas per minggu", rupiah(r.weekly)) + "</dl>" +
                    (r.negative ? '<p class="calc-note status-text-over">Uang tersedia tidak cukup untuk kebutuhan wajib dan tabungan.</p>' : ""),
            };
        },
    };

    function initCalculators() {
        const forms = document.querySelectorAll(".calc-form");
        if (!forms.length) return;

        // Isi default "sisa hari" dengan sisa hari bulan ini (termasuk hari ini)
        const daysInput = document.getElementById("daysLeft");
        if (daysInput) {
            const now = new Date();
            const last = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
            daysInput.value = last - now.getDate() + 1;
        }

        forms.forEach(function (form) {
            form.addEventListener("submit", function (event) {
                event.preventDefault();
                const out = form.querySelector(".calc-result");
                const payload = {};
                new FormData(form).forEach(function (value, key) { payload[key] = value; });

                postJSON("/api/calc/" + form.dataset.calc, payload)
                    .then(function (res) {
                        out.hidden = false;
                        out.className = "calc-result";
                        if (!res.data.ok) {
                            out.classList.add("is-error");
                            out.textContent = res.data.error || "Perhitungan gagal.";
                            return;
                        }
                        const view = RENDERERS[form.dataset.calc](res.data.result);
                        if (view.warn) out.classList.add("is-warn");
                        out.innerHTML = view.html;
                    })
                    .catch(function () {
                        out.hidden = false;
                        out.className = "calc-result is-error";
                        out.textContent = "Tidak dapat terhubung ke server.";
                    });
            });
        });
    }

    // ------------------------------------------------------------------
    document.addEventListener("DOMContentLoaded", function () {
        initChrome();
        initTransactionModal();
        initBudgetForm();
        initGuide();
        initArticles();
        initCalculators();
    });

    return { initDashboardCharts: initDashboardCharts, rupiah: rupiah };
})();
