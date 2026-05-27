frappe.pages["ba-notifications"].on_page_load = function(wrapper) {
    frappe.ui.make_app_page({
        parent: wrapper,
        title: "BizAxl Notifications",
        single_column: true,
    });
    const page = wrapper.page;
    page.main.html(`
        <div style="padding:20px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;flex-wrap:wrap;gap:12px;">
                <input id="notif-search" type="text" class="form-control" placeholder="Search notifications..."
                    style="max-width:320px;" oninput="ba_notifs.filter(this.value)">
                <div style="display:flex;gap:8px;align-items:center;">
                    <span id="notif-count" style="color:var(--text-muted);font-size:13px;"></span>
                    <button class="btn btn-xs btn-default" onclick="ba_notifs.filter_status('all')">All</button>
                    <button class="btn btn-xs btn-success" onclick="ba_notifs.filter_status('enabled')">Enabled</button>
                    <button class="btn btn-xs btn-default" onclick="ba_notifs.filter_status('disabled')">Disabled</button>
                    <button class="btn btn-xs btn-danger" onclick="ba_notifs.filter_status('broken')">Broken</button>
                </div>
            </div>
            <div id="notifs-container"></div>
        </div>
    `);
    ba_notifs.load();
};

window.ba_notifs = {
    all: [],
    current_filter: "all",
    current_search: "",

    load() {
        frappe.call({
            method: "bizaxl_core.bizaxl_core.page.ba_notifications.ba_notifications.get_all_notifications",
            callback: (r) => {
                this.all = r.message || [];
                this.render();
            }
        });
    },

    filter(query) {
        this.current_search = query.toLowerCase();
        this.render();
    },

    filter_status(status) {
        this.current_filter = status;
        this.render();
    },

    get_filtered() {
        return this.all.filter(n => {
            const matchSearch = !this.current_search ||
                n.name.toLowerCase().includes(this.current_search) ||
                n.document_type.toLowerCase().includes(this.current_search) ||
                n.module.toLowerCase().includes(this.current_search);

            const matchStatus =
                this.current_filter === "all" ? true :
                this.current_filter === "enabled" ? n.enabled && n.doctype_exists :
                this.current_filter === "disabled" ? !n.enabled :
                this.current_filter === "broken" ? !n.doctype_exists : true;

            return matchSearch && matchStatus;
        });
    },

    toggle(name, current) {
        const newVal = current ? 0 : 1;
        frappe.call({
            method: "bizaxl_core.bizaxl_core.page.ba_notifications.ba_notifications.toggle_notification",
            args: { name, enabled: newVal },
            callback: () => {
                const n = this.all.find(x => x.name === name);
                if (n) n.enabled = newVal;
                this.render();
                frappe.show_alert({
                    message: `${name} ${newVal ? "enabled" : "disabled"}`,
                    indicator: newVal ? "green" : "gray"
                }, 3);
            }
        });
    },

    render() {
        const filtered = this.get_filtered();
        const container = document.getElementById("notifs-container");
        const countEl = document.getElementById("notif-count");

        const enabled = this.all.filter(n => n.enabled && n.doctype_exists).length;
        const broken = this.all.filter(n => !n.doctype_exists).length;
        const disabled = this.all.filter(n => !n.enabled).length;
        countEl.textContent = `${this.all.length} total | ${enabled} active | ${broken} broken | ${disabled} disabled`;

        // Group by module
        const grouped = {};
        for (const n of filtered) {
            const mod = n.module || "Unknown";
            if (!grouped[mod]) grouped[mod] = [];
            grouped[mod].push(n);
        }

        if (!filtered.length) {
            container.innerHTML = `<div style="text-align:center;color:var(--text-muted);padding:40px;">No notifications found</div>`;
            return;
        }

        container.innerHTML = Object.entries(grouped).sort().map(([module, notifs]) => `
            <div style="margin-bottom:24px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border-color);">
                    <span style="font-weight:600;font-size:15px;">${module}</span>
                    <span style="font-size:12px;color:var(--text-muted);background:var(--bg-color);padding:2px 8px;border-radius:10px;">${notifs.length}</span>
                </div>
                <div style="display:flex;flex-direction:column;gap:6px;">
                    ${notifs.map(n => `
                        <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;
                            border:1px solid ${!n.doctype_exists ? 'var(--red)' : 'var(--border-color)'};
                            border-radius:8px;background:var(--card-bg);">
                            <div style="flex:1;min-width:0;">
                                <div style="font-size:13px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                                    ${n.name}
                                    ${!n.doctype_exists ? '<span style="color:var(--red);font-size:11px;margin-left:6px;">⚠ DocType missing</span>' : ""}
                                </div>
                                <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">
                                    ${n.document_type} ${n.channel ? "· " + n.channel : ""}
                                </div>
                            </div>
                            <div style="display:flex;align-items:center;gap:8px;">
                                <span style="font-size:11px;padding:2px 8px;border-radius:10px;
                                    background:${n.enabled && n.doctype_exists ? 'var(--bg-green)' : 'var(--bg-color)'};
                                    color:${n.enabled && n.doctype_exists ? 'var(--green)' : 'var(--text-muted)'};">
                                    ${n.enabled ? "enabled" : "disabled"}
                                </span>
                                <label style="cursor:pointer;display:flex;align-items:center;">
                                    <input type="checkbox" ${n.enabled ? "checked" : ""}
                                        onchange="ba_notifs.toggle('${n.name}', ${n.enabled})"
                                        style="cursor:pointer;width:16px;height:16px;">
                                </label>
                                <button class="btn btn-xs btn-default"
                                    onclick="frappe.set_route('Form', 'Notification', '${n.name}')">
                                    Edit
                                </button>
                            </div>
                        </div>
                    `).join("")}
                </div>
            </div>
        `).join("");
    }
};
