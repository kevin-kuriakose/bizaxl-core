import frappe
import json
import os


CORE_MODULES = {
    "Core", "Custom", "Desk", "Email", "Integrations",
    "Printing", "Setup", "Workflow", "BizAxl Core",
}

ERPNEXT_MODULES = {
    "Accounts":        {"label": "Accounting & Finance",   "icon": "💰", "core": True},
    "Buying":          {"label": "Buying & Procurement",   "icon": "🛒", "core": True},
    "Selling":         {"label": "Sales",                  "icon": "💼", "core": True},
    "Contacts":        {"label": "Contacts",               "icon": "👥", "core": True},
    "HR":              {"label": "HR & Payroll",           "icon": "👤", "core": False},
    "Payroll":         {"label": "Payroll",                "icon": "💵", "core": False},
    "Stock":           {"label": "Stock & Inventory",      "icon": "📦", "core": False},
    "Manufacturing":   {"label": "Manufacturing",          "icon": "🏭", "core": False},
    "Projects":        {"label": "Projects & Timesheets",  "icon": "📋", "core": False},
    "CRM":             {"label": "CRM & Leads",            "icon": "🤝", "core": False},
    "Assets":          {"label": "Asset Management",       "icon": "🏗️",  "core": False},
    "Quality":         {"label": "Quality Management",     "icon": "✅", "core": False},
    "Support":         {"label": "Support & Helpdesk",     "icon": "🎧", "core": False},
    "Website":         {"label": "Website & CMS",          "icon": "🌐", "core": False},
    "E-commerce":      {"label": "E-Commerce",             "icon": "🛍️",  "core": False},
    "Agriculture":     {"label": "Agriculture",            "icon": "🌾", "core": False},
    "Healthcare":      {"label": "Healthcare",             "icon": "🏥", "core": False},
    "Education":       {"label": "Education",              "icon": "🎓", "core": False},
    "Hospitality":     {"label": "Hospitality",            "icon": "🏨", "core": False},
    "Non Profit":      {"label": "Non-Profit",             "icon": "❤️",  "core": False},
    "Loan Management": {"label": "Loan Management",        "icon": "🏦", "core": False},
    "Utilities":       {"label": "Utilities",              "icon": "⚡", "core": False},
    "Maintenance":     {"label": "Maintenance",            "icon": "🔧", "core": False},
}

MODULE_TO_DOMAIN = {
    "Manufacturing": "manufacturing",
    "Stock":         "stock",
    "HR":            "hr",
    "Payroll":       "payroll",
    "Projects":      "projects",
    "CRM":           "crm",
    "Assets":        "asset",
    "Quality":       "quality",
    "Support":       "support",
    "Website":       "website",
    "E-commerce":    "e_commerce",
    "Agriculture":   "agriculture",
    "Healthcare":    "healthcare",
    "Education":     "education",
    "Hospitality":   "hospitality",
    "Non Profit":    "non_profit",
    "Loan Management": "loan_management",
    "Utilities":     "utilities",
    "Maintenance":   "maintenance",
}

HOME_LINKS_TO_HIDE = {
    "Lead", "Opportunity", "Warehouse", "Item Price",
    "Stock Reconciliation", "Work Order", "BOM",
    "Production Plan", "Project", "Task", "Issue",
    "Asset", "Customer Complaint", "Incoterm",
    "Brand", "Territory", "Customer Group",
    "Unit of Measure",
}

HOME_CARD_BREAKS_TO_HIDE = {
    "Stock", "CRM", "Manufacturing", "Projects",
    "Support", "Assets", "Quality", "HR", "Website",
    "Maintenance",
}


def get_installed_app_profiles():
    profiles = []
    for app in frappe.get_installed_apps():
        try:
            app_path = frappe.get_app_path(app)
            bizaxl_json = os.path.normpath(
                os.path.join(app_path, "..", "bizaxl.json")
            )
            if os.path.exists(bizaxl_json):
                profile = json.load(open(bizaxl_json))
                profile["_app"] = app
                profiles.append(profile)
        except Exception:
            continue
    return profiles


@frappe.whitelist()
def get_module_config():
    profiles = get_installed_app_profiles()
    optional_modules = {}
    hidden_by_default = set()

    for profile in profiles:
        for opt in profile.get("optional_modules", []):
            mod = opt["module"] if isinstance(opt, dict) else opt
            label_info = opt if isinstance(opt, dict) else {"module": opt}
            if mod not in optional_modules:
                optional_modules[mod] = {
                    "module": mod,
                    "label": label_info.get("label", ERPNEXT_MODULES.get(mod, {}).get("label", mod)),
                    "description": label_info.get("description", ""),
                    "icon": ERPNEXT_MODULES.get(mod, {}).get("icon", "📦"),
                    "checked": False,
                }
        for m in profile.get("hide_modules", []):
            hidden_by_default.add(m)

    return {
        "profiles": profiles,
        "optional_modules": list(optional_modules.values()),
        "hidden_by_default": list(hidden_by_default),
        "core_modules": [
            {"module": k, "label": v["label"], "icon": v["icon"]}
            for k, v in ERPNEXT_MODULES.items() if v["core"]
        ],
    }


@frappe.whitelist()
def apply_module_selection(selected_modules, app_name=None):
    if isinstance(selected_modules, str):
        selected_modules = json.loads(selected_modules)

    selected_set = set(selected_modules)
    for module, info in ERPNEXT_MODULES.items():
        if info["core"]:
            selected_set.add(module)
    selected_set.update(CORE_MODULES)

    all_modules = frappe.get_all("Module Def", fields=["name", "app_name"])

    for module in all_modules:
        mod_name = module.name
        if mod_name in CORE_MODULES:
            continue
        app = module.get("app_name", "")
        if app and app not in ("erpnext", "frappe", "hrms"):
            continue

        should_hide = mod_name not in selected_set
        _set_workspace_visibility(mod_name, not should_hide)

        if should_hide:
            _block_module_from_search(mod_name)
            _disable_domain(mod_name)
        else:
            _restore_module_to_search(mod_name)
            _enable_domain(mod_name)

    # Fix home workspace
    _fix_home_workspace(selected_set)

    frappe.db.commit()
    frappe.clear_cache()

    hidden = len([m for m in all_modules
                  if m.name not in selected_set and m.name not in CORE_MODULES])
    return {
        "status": "success",
        "hidden": hidden,
        "shown": len(selected_set),
        "message": f"Applied. {len(selected_set)} modules visible, {hidden} hidden.",
    }


@frappe.whitelist()
def apply_profile(app_name):
    profiles = get_installed_app_profiles()
    profile = next((p for p in profiles if p.get("app_name") == app_name), None)
    if not profile:
        frappe.throw(f"No bizaxl.json found for app: {app_name}")

    show = set(profile.get("show_modules", []))
    for m, info in ERPNEXT_MODULES.items():
        if info["core"]:
            show.add(m)
    return apply_module_selection(list(show), app_name)


@frappe.whitelist()
def restore_module(module_name):
    _restore_module_to_search(module_name)
    _set_workspace_visibility(module_name, True)
    _enable_domain(module_name)
    frappe.db.commit()
    frappe.clear_cache()
    return {"status": "success", "message": str(module_name) + " restored successfully."}


@frappe.whitelist()
def restore_all_modules():
    for mod in ERPNEXT_MODULES:
        _restore_module_to_search(mod)
        _set_workspace_visibility(mod, True)
        _enable_domain(mod)
    frappe.db.commit()
    frappe.clear_cache()
    return {"status": "success", "message": "All modules restored."}


def _fix_home_workspace(selected_set):
    """Hide irrelevant links from the Home workspace."""
    try:
        if not frappe.db.exists("Workspace", "Home"):
            return
        home = frappe.get_doc("Workspace", "Home")
        changed = False
        for link in home.links:
            should_hide = (
                link.link_to in HOME_LINKS_TO_HIDE or
                (link.type == "Card Break" and link.label in HOME_CARD_BREAKS_TO_HIDE)
            )
            if should_hide and not link.hidden:
                link.hidden = 1
                changed = True
            elif not should_hide and link.hidden:
                link.hidden = 0
                changed = True
        if changed:
            home.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(str(e), "BizAxl Home Workspace Error")


def _set_workspace_visibility(module_name, visible):
    try:
        frappe.db.sql("""
            UPDATE `tabWorkspace`
            SET is_hidden = %s, public = %s
            WHERE module = %s OR title = %s
        """, (0 if visible else 1, 1 if visible else 0, module_name, module_name))
    except Exception:
        pass


def _block_module_from_search(module_name):
    """Hide all DocTypes, Reports, Dashboards in a module from search."""
    try:
        # Block doctypes
        frappe.db.sql("""
            UPDATE `tabDocType`
            SET hide_toolbar = 1, in_create = 0
            WHERE module = %s AND issingle = 0
        """, module_name)

        # Disable reports
        frappe.db.sql("""
            UPDATE `tabReport` SET disabled = 1
            WHERE module = %s
        """, module_name)

        # Hide dashboards
        frappe.db.sql("""
            UPDATE `tabDashboard` SET is_standard = 0
            WHERE module = %s
        """, module_name)
    except Exception:
        pass


def _restore_module_to_search(module_name):
    """Re-enable all DocTypes, Reports, Dashboards in a module."""
    try:
        frappe.db.sql("""
            UPDATE `tabDocType`
            SET hide_toolbar = 0
            WHERE module = %s
        """, module_name)

        frappe.db.sql("""
            UPDATE `tabReport` SET disabled = 0
            WHERE module = %s
        """, module_name)

        frappe.db.sql("""
            UPDATE `tabDashboard` SET is_standard = 1
            WHERE module = %s
        """, module_name)

        frappe.db.sql("""
            UPDATE `tabWorkspace`
            SET is_hidden = 0, public = 1
            WHERE module = %s OR title = %s
        """, (module_name, module_name))
    except Exception:
        pass


def _disable_domain(module_name):
    domain = MODULE_TO_DOMAIN.get(module_name)
    if not domain:
        return
    try:
        disabled = frappe.conf.get("disabled_domains") or []
        if isinstance(disabled, str):
            disabled = json.loads(disabled)
        if domain not in disabled:
            disabled.append(domain)
            from frappe.utils.site_config import update_site_config
            update_site_config("disabled_domains", disabled)
    except Exception:
        pass


def _enable_domain(module_name):
    domain = MODULE_TO_DOMAIN.get(module_name)
    if not domain:
        return
    try:
        disabled = frappe.conf.get("disabled_domains") or []
        if isinstance(disabled, str):
            disabled = json.loads(disabled)
        if domain in disabled:
            disabled.remove(domain)
            from frappe.utils.site_config import update_site_config
            update_site_config("disabled_domains", disabled)
    except Exception:
        pass


@frappe.whitelist()
def get_current_visibility():
    return frappe.get_all(
        "Workspace",
        filters={"public": 1},
        fields=["name", "module", "is_hidden", "title"]
    )
