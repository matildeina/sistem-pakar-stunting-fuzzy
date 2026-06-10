document.addEventListener("DOMContentLoaded", () => {
    const STATUS_LABEL = {
        gizi_buruk: { label: "Gizi Buruk", cls: "buruk" },
        gizi_kurang: { label: "Gizi Kurang", cls: "buruk" },
        gizi_baik: { label: "Gizi Baik", cls: "normal" },
        berisiko_lebih: { label: "Berisiko Lebih", cls: "risiko" },
        gizi_lebih: { label: "Gizi Lebih", cls: "risiko" },
        obesitas: { label: "Obesitas", cls: "buruk" },
    };

    const BBTB_LABEL = {
        gizi_buruk: "Gizi Buruk (Severely Wasted)",
        gizi_kurang: "Gizi Kurang (Wasted)",
        gizi_baik: "Gizi Baik (Normal)",
        berisiko_lebih: "Berisiko Gizi Lebih",
        gizi_lebih: "Gizi Lebih (Overweight)",
        obesitas: "Obesitas",
    };

    const REKOM_ICONS = {
        tindakan: { icon: "!", cls: "rekom-icon-tindakan" },
        makan: { icon: "✓", cls: "rekom-icon-makan" },
        pantau: { icon: "◉", cls: "rekom-icon-pantau" },
        dokter: { icon: "✚", cls: "rekom-icon-dokter" },
    };

    // Auto-calculating listener untuk form input dinamis
    ['usia', 'tb_cm', 'bb_kg'].forEach(id => {
        document.getElementById(id).addEventListener("input", autoInterceptForm);
    });

    document.getElementById("status_bbtb").addEventListener("change", () => updateStatusBadge('bbtb'));
    document.getElementById("status_imtu").addEventListener("change", () => updateStatusBadge('imtu'));
    document.getElementById("btn-check").addEventListener("click", cekStuntingExecution);

    // Bind event tabs tanpa inline handler
    document.querySelectorAll(".rekom-tab").forEach(tab => {
        tab.addEventListener("click", (e) => {
            switchTab(e.target.getAttribute("data-tab"));
        });
    });

    function updateStatusBadge(type) {
        const val = document.getElementById("status_" + type).value;
        const badge = document.getElementById("badge-" + type);
        if (val && STATUS_LABEL[val]) {
            badge.textContent = STATUS_LABEL[val].label;
            badge.className = "status-badge-preview show " + STATUS_LABEL[val].cls;
        } else {
            badge.className = "status-badge-preview";
        }
    }

    function autoInterceptForm() {
        const tempTb = parseFloat(document.getElementById("tb_cm").value);
        const tempBb = parseFloat(document.getElementById("bb_kg").value);

        if (!isNaN(tempTb) && !isNaN(tempBb) && tempTb > 0) {
            const rasioBBTB = tempBb / (tempTb / 10);
            let autoBBTB = "gizi_baik";
            if (rasioBBTB < 1.1) autoBBTB = "gizi_buruk";
            else if (rasioBBTB < 1.3) autoBBTB = "gizi_kurang";
            else if (rasioBBTB > 1.8) autoBBTB = "obesitas";
            else if (rasioBBTB > 1.6) autoBBTB = "gizi_lebih";
            else if (rasioBBTB > 1.5) autoBBTB = "berisiko_lebih";

            document.getElementById("status_bbtb").value = autoBBTB;
            updateStatusBadge('bbtb');

            const tbMeter = tempTb / 100;
            const imtSkor = tempBb / (tbMeter * tbMeter);
            let autoIMTU = "gizi_baik";
            if (imtSkor < 13) autoIMTU = "gizi_buruk";
            else if (imtSkor < 14) autoIMTU = "gizi_kurang";
            else if (imtSkor > 21) autoIMTU = "obesitas";
            else if (imtSkor > 19) autoIMTU = "gizi_lebih";
            else if (imtSkor > 18) autoIMTU = "berisiko_lebih";

            document.getElementById("status_imtu").value = autoIMTU;
            updateStatusBadge('imtu');
        }
    }

    function switchTab(name) {
        document.querySelectorAll(".rekom-tab").forEach(t => t.classList.remove("active"));
        document.querySelectorAll(".rekom-content").forEach(c => c.classList.remove("active"));
        document.querySelector(`[data-tab="${name}"]`).classList.add("active");
        document.getElementById("tab-" + name).classList.add("active");
    }

    function renderList(listId, items, type) {
        const ul = document.getElementById(listId);
        ul.innerHTML = "";
        const { icon, cls } = REKOM_ICONS[type];
        items.forEach(item => {
            const li = document.createElement("li");
            li.innerHTML = `<div class="rekom-list-icon ${cls}">${icon}</div><span>${item}</span>`;
            ul.appendChild(li);
        });
    }

    async function cekStuntingExecution() {
        const usia = parseInt(document.getElementById("usia").value);
        const jk = document.getElementById("jk").value;
        const tbCm = parseFloat(document.getElementById("tb_cm").value);
        const bbKg = parseFloat(document.getElementById("bb_kg").value);
        const statusBbtb = document.getElementById("status_bbtb").value;
        const statusImtu = document.getElementById("status_imtu").value;

        const panel = document.getElementById("result");
        const badge = document.getElementById("result-badge");
        const title = document.getElementById("result-title");
        const desc = document.getElementById("result-desc");
        const btn = document.getElementById("btn-check");

        if (isNaN(usia) || !jk || isNaN(tbCm) || isNaN(bbKg)) {
            panel.className = "result-panel risiko show";
            badge.className = "result-badge risiko";
            badge.textContent = "⚠ Perhatian";
            title.textContent = "Data belum lengkap";
            desc.textContent = "Mohon isi semua kolom wajib.";
            return;
        }

        btn.disabled = true;
        btn.textContent = "Sedang memeriksa…";

        try {
            const resp = await fetch("/cek", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ usia, jk, tb_cm: tbCm, bb_kg: bbKg }),
            });

            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || "Gagal memproses data");

            const { z_tb, z_bb, status_gizi, fuzzy, rekomendasi, catatan_tambahan } = data;

            const cls = fuzzy.status === "Stunting" ? "stunting" : fuzzy.status === "Risiko Stunting" ? "risiko" : "normal";
            panel.className = `result-panel ${cls} show`;
            badge.className = `result-badge ${cls}`;
            badge.textContent = fuzzy.status;
            title.textContent = `Hasil: ${fuzzy.status}`;
            desc.innerHTML = `Z-Score TB/U: ${z_tb} SD (${status_gizi.tbu})<br>Z-Score BB/U: ${z_bb} SD (${status_gizi.bbu})`;

            document.getElementById("sgi-tbu").textContent = status_gizi.tbu;
            document.getElementById("sgi-bbu").textContent = status_gizi.bbu;
            document.getElementById("status-gizi-grid").style.display = "grid";

            renderList("list-tindakan", rekomendasi.tindakan_segera, "tindakan");
            renderList("list-makan", rekomendasi.pola_makan, "makan");
            renderList("list-pantau", rekomendasi.pemantauan, "pantau");
            renderList("list-dokter", rekomendasi.kapan_ke_dokter, "dokter");
            document.getElementById("rekom-panel").className = "rekom-panel show";

            if (data.analisis_ai) {
                document.getElementById("ai-kondisi").innerHTML = data.analisis_ai;
                document.getElementById("ai-loading").style.display = "none";
                document.getElementById("ai-content").style.display = "block";
                document.getElementById("ai-panel").style.display = "block";
            }
            switchTab("tindakan");
        } catch (err) {
            desc.textContent = err.message;
        } finally {
            btn.disabled = false;
            btn.textContent = "Periksa Sekarang";
        }
    }
});