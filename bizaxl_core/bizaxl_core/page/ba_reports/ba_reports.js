frappe.pages["ba-reports"].on_page_load = function(wrapper) {
    frappe.ui.make_app_page({
        parent: wrapper,
        title: "BizAxl Reports",
        single_column: true,
    });
    const page = wrapper.page;
    page.main.html(`
        <div style="padding:20px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
                <input id="report-search" type="text" class="form-control" placeholder="Search reports..."
                    style="max-width:320px;" oninput="ba_reports.filter(this.value)">
                <span id="report-count" style="color:var(--text-muted);font-size:13px;"></span>
            </div>
            <div id="reports-container"></div>
        </div>
    `);
    ba_reports.load();
};

window.ba_reports = {
    all_reports: [],

    load() {
        frappe.call({
            method: "bizaxl_core.bizaxl_core.page.ba_reports.ba_reports.get_all_reports",
            callback: (r) => {
                this.all_reports = r.message || [];
                this.render(this.all_reports);
            }
        });
    },

    filter(query) {
        const q = query.toLowerCase();
        const filtered = q
            ? this.all_reports.filter(r =>
                r.name.toLowerCase().includes(q) ||
                r.module.toLowerCase().includes(q))
            : this.all_reports;
        this.render(filtered);
    },

    render(reports) {
        const container = document.getElementById("reports-container");
        const countEl = document.getElementById("report-count");
        countEl.textContent = `${reports.length} reports`;

        // Group by module
        const grouped = {};
        for (const r of reports) {
            if (!grouped[r.module]) grouped[r.module] = [];
            grouped[r.module].push(r);
        }

        const MODULE_ICONS = {
            "BizAxl Accounts": "💰", "BizAxl Selling": "💼", "BizAxl Buying": "🛒",
            "BizAxl Stock": "📦", "BizAxl HR": "👤", "BizAxl Payroll": "💵",
            "BizAxl Projects": "📋", "BizAxl CRM": "🤝", "BizAxl Assets": "🏗️",
            "BizAxl POS": "🏪", "Civic Operations": "🏛️", "Museum Operations": "🏛",
            "Professional Services": "💼", "Organ Donation": "❤️",
            "Retail Operations": "🛍️", "Energy Utilization": "⚡",
            "Logistics Transportation": "🚛",
        };

        container.innerHTML = Object.entries(grouped).map(([module, reps]) => `
            <div style="margin-bottom:24px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border-color);">
                    <span style="font-size:18px;">${MODULE_ICONS[module] || "📊"}</span>
                    <span style="font-weight:600;font-size:15px;">${module}</span>
                    <span style="font-size:12px;color:var(--text-muted);background:var(--bg-color);padding:2px 8px;border-radius:10px;">${reps.length}</span>
                </div>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px;">
                    ${reps.map(r => `
                        <div onclick="frappe.set_route('query-report', '${r.name}')"
                            style="padding:10px 14px;border:1px solid var(--border-color);border-radius:8px;
                                   cursor:pointer;display:flex;align-items:center;justify-content:space-between;
                                   transition:all 0.15s;background:var(--card-bg);"
                            onmouseover="this.style.borderColor='var(--primary)';this.style.background='var(--bg-blue)'"
                            onmouseout="this.style.borderColor='var(--border-color)';this.style.background='var(--card-bg)'">
                            <span style="font-size:13px;font-weight:500;">${r.name}</span>
                            <span style="font-size:11px;color:var(--text-muted);">↗</span>
                        </div>
                    `).join("")}
                </div>
            </div>
        `).join("");
    }
};
