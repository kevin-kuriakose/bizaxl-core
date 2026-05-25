import frappe
import json
import os


# Modules that are ALWAYS visible — cannot be hidden
CORE_MODULES = {
    "Core",
    "Custom",
    "Desk",
    "Email",
    "Integrations",
    "Printing",
    "Setup",
    "Workflow",
    "BizAxl Core",
}

# ERPNext module → display label mapping
ERPNEXT_MODULES = {
    "Accounts":          {"label": "Accounting & Finance",    "icon": "💰", "core": True},
    "Buying":            {"label": "Buying & Procurement",    "icon": "🛒", "core": True},
    "Selling":           {"label": "Sales & CRM",             "icon": "💼", "core": True},
    "Contacts":          {"label": "Contacts",                "icon": "👥", "core": True},
    "HR":                {"label": "HR & Payroll",            "icon": "👤", "core": False},
    "Payroll":           {"label": "Payroll",                 "icon": "💵", "core": False},
    "Stock":             {"label": "Stock & Inventory",       "icon": "📦", "core": False},
    "Manufacturing":     {"label": "Manufacturing",           "icon": "🏭", "core": False},
    "Projects":          {"label": "Projects & Timesheets",   "icon": "📋", "core": False},
    "CRM":               {"label": "CRM & Leads",             "icon": "🤝", "core": False},
    "Assets":            {"label": "Asset Management",        "icon": "🏗️",  "core": False},
    "Quality":           {"label": "Quality Management",      "icon": "✅", "core": False},
    "Support":           {"label": "Support & Helpdesk",      "icon": "🎧", "core": False},
    "Website":           {"label": "Website & CMS",           "icon": "🌐", "core": False},
    "E-commerce":        {"label": "E-Commerce",              "icon": "🛍️",  "core": False},
    "Agriculture":       {"label": "Agriculture",             "icon": "🌾", "core": False},
    "Healthcare":        {"label": "Healthcare",              "icon": "🏥", "core": False},
    "Education":         {"label": "Education",               "icon": "🎓", "core": False},
    "Hospitality":       {"label": "Hospitality",             "icon": "🏨", "core": False},
    "Non Profit":        {"label": "Non-Profit",              "icon": "❤️",  "core": False},
    "Loan Management":   {"label": "Loan Management",         "icon": "🏦", "core": False},
    "Utilities":         {"label": "Utilities",               "icon": "⚡", "core": False},
}


def get_installed_app_profiles():
    """
    Scan all installed apps for bizaxl.json files.
    Returns list of app profiles.
    """
    profiles = []
    installed_apps = frappe.get_installed_apps()

    for app in installed_apps:
        try:
            app_path = frappe.get_app_path(app)
            bizaxl_json = os.path.join(app_path, "..", "bizaxl.json")
            bizaxl_json = os.path.normpath(bizaxl_json)

            if os.path.exists(bizaxl_json):
                with open(bizaxl_json) as f:
                    profile = json.load(f)
                profile["_app"] = app
                profiles.append(profile)
        except Exception:
            continue

    return profiles


@frappe.whitelist()
def get_module_config():
    """
    Return current module visibility config for the setup wizard.
    """
    profiles = get_installed_app_profiles()

    # Get all optional modules from installed app profiles
    optional_modules = {}
    for profile in profiles:
        for opt in profile.get("optional_modules", []):
            module = opt["module"] if isinstance(opt, dict) else opt
            label_info = opt if isinstance(opt, dict) else {"module": opt}
            if module not in optional_modules:
                optional_modules[module] = {
                    "module": module,
                    "label": label_info.get("label", ERPNEXT_MODULES.get(module, {}).get("label", module)),
                    "description": label_info.get("description", ""),
                    "icon": ERPNEXT_MODULES.get(module, {}).get("icon", "📦"),
                    "checked": False,
                }

    # Get modules that should be hidden by default
    hidden_by_default = set()
    for profile in profiles:
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
    """
    Apply module visibility based on user selection from setup wizard.
    selected_modules: JSON list of module names to SHOW
    """
    if isinstance(selected_modules, str):
        selected_modules = json.loads(selected_modules)

    selected_set = set(selected_modules)

    # Always include core modules
    for module, info in ERPNEXT_MODULES.items():
        if info["core"]:
            selected_set.add(module)

    # Also keep non-ERPNext modules (custom app modules)
    selected_set.update(CORE_MODULES)

    # Apply to Module Def
    all_modules = frappe.get_all("Module Def", fields=["name", "app_name"])

    hidden_count = 0
    shown_count = 0

    for module in all_modules:
        module_name = module.name

        # Never hide core system modules
        if module_name in CORE_MODULES:
            continue

        # Never hide custom app modules (retail_erp, organ_donation_erp etc)
        app = module.get("app_name", "")
        if app and app not in ("erpnext", "frappe", "hrms"):
            continue

        # Determine if this module should be hidden
        should_hide = module_name not in selected_set

        try:
            frappe.db.set_value("Module Def", module_name, "custom", 0)
            # Use workspace hiding instead of Module Def deletion
            _set_workspace_visibility(module_name, not should_hide)
            if should_hide:
                hidden_count += 1
            else:
                shown_count += 1
        except Exception:
            continue

    frappe.db.commit()
    frappe.clear_cache()

    # Save the selection to site config for future reference
    frappe.conf["bizaxl_selected_modules"] = list(selected_set)

    return {
        "status": "success",
        "hidden": hidden_count,
        "shown": shown_count,
        "message": f"Module configuration applied. {shown_count} modules visible, {hidden_count} hidden.",
    }


def _set_workspace_visibility(module_name, visible):
    """Show or hide a workspace by module name."""
    try:
        workspaces = frappe.get_all(
            "Workspace",
            filters={"module": module_name},
            fields=["name"]
        )
        for ws in workspaces:
            frappe.db.set_value("Workspace", ws.name, "is_hidden", 0 if visible else 1)
    except Exception:
        pass


@frappe.whitelist()
def apply_profile(app_name):
    """Apply a specific app's profile (show/hide defaults)."""
    profiles = get_installed_app_profiles()
    profile = next((p for p in profiles if p.get("app_name") == app_name), None)

    if not profile:
        frappe.throw(f"No bizaxl.json found for app: {app_name}")

    # Build selected modules list
    show = set(profile.get("show_modules", []))
    # Add core modules always
    for m, info in ERPNEXT_MODULES.items():
        if info["core"]:
            show.add(m)

    return apply_module_selection(list(show), app_name)


@frappe.whitelist()
def get_current_visibility():
    """Return current module visibility status."""
    workspaces = frappe.get_all(
        "Workspace",
        filters={"public": 1},
        fields=["name", "module", "is_hidden", "title"]
    )
    return workspaces
