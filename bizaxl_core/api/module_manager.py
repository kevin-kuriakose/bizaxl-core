import frappe
import json
import os

SYSTEM_MODULES = {
    "Core", "Custom", "Desk", "Email", "Integrations",
    "Printing", "Setup", "Workflow", "BizAxl Core",
    "Automation", "Social", "Contacts", "Geo", "Website",
}

BIZAXL_CORE_MODULES = {
    "BizAxl Accounts", "BizAxl Buying", "BizAxl Selling",
    "BizAxl Contacts", "BizAxl Setup",
}

BIZAXL_OPTIONAL_MODULES = {
    "BizAxl Stock":    {"label": "Stock & Inventory",     "app": "bizaxl_stock"},
    "BizAxl HR":       {"label": "HR & People",           "app": "bizaxl_hr"},
    "BizAxl Payroll":  {"label": "Payroll",               "app": "bizaxl_payroll"},
    "BizAxl Projects": {"label": "Projects & Timesheets", "app": "bizaxl_projects"},
    "BizAxl CRM":      {"label": "CRM & Leads",           "app": "bizaxl_crm"},
    "BizAxl Assets":   {"label": "Asset Management",      "app": "bizaxl_assets"},
    "BizAxl POS":      {"label": "Point of Sale",         "app": "bizaxl_pos"},
}

VERTICAL_APPS = {
    "retail_erp", "energy_erp", "civic_erp",
    "museum_erp", "proserv_erp", "organ_donation_erp",
    "logistics_transport_erp",
}


def get_installed_app_profiles():
    """Scan all installed apps for bizaxl.json profile files."""
    profiles = []
    for app in frappe.get_installed_apps():
        try:
            app_path = frappe.get_app_path(app)
            bizaxl_json = os.path.normpath(os.path.join(app_path, "..", "bizaxl.json"))
            if os.path.exists(bizaxl_json):
                with open(bizaxl_json) as f:
                    profile = json.load(f)
                profile["_app"] = app
                profiles.append(profile)
        except Exception:
            continue
    return profiles


def get_active_profile():
    """
    Get the bizaxl.json profile for the active vertical app.
    Returns None if no vertical app is installed.
    """
    installed = frappe.get_installed_apps()
    for app in installed:
        if app in VERTICAL_APPS:
            try:
                app_path = frappe.get_app_path(app)
                bizaxl_json = os.path.normpath(os.path.join(app_path, "..", "bizaxl.json"))
                if os.path.exists(bizaxl_json):
                    with open(bizaxl_json) as f:
                        profile = json.load(f)
                    profile["_app"] = app
                    return profile
            except Exception:
                continue
    return None


@frappe.whitelist()
def get_module_config():
    """
    Return module visibility config.
    If a vertical app is installed with a bizaxl.json, only show
    optional modules that the vertical app explicitly lists.
    Otherwise show all installed optional packs.
    """
    installed_apps = frappe.get_installed_apps()
    profile = get_active_profile()

    # Get modules the vertical app allows (if any)
    profile_optional = None
    if profile:
        raw = profile.get("optional_modules", [])
        if raw:
            profile_optional = set()
            for item in raw:
                mod = item["module"] if isinstance(item, dict) else item
                profile_optional.add(mod)

    optional = []
    for module, info in BIZAXL_OPTIONAL_MODULES.items():
        installed = info["app"] in installed_apps

        # If vertical app defines optional_modules, only include those
        if profile_optional is not None and module not in profile_optional:
            continue

        # Only show if the backing app is installed
        if not installed:
            continue

        optional.append({
            "module": module,
            "label": info["label"],
            "app": info["app"],
            "installed": installed,
            "checked": installed,
        })

    core = [{"module": m, "label": m.replace("BizAxl ", "")} for m in BIZAXL_CORE_MODULES]

    return {
        "core_modules": core,
        "optional_modules": optional,
        "profile": profile.get("display_name") if profile else None,
        "profile_app": profile.get("_app") if profile else None,
    }


@frappe.whitelist()
def apply_module_selection(selected_modules):
    """
    Show/hide BizAxl optional modules based on user selection.
    Core modules and vertical app modules are never touched.
    """
    if isinstance(selected_modules, str):
        selected_modules = json.loads(selected_modules)

    selected_set = set(selected_modules)
    selected_set.update(BIZAXL_CORE_MODULES)

    installed_apps = frappe.get_installed_apps()
    hidden_count = 0
    shown_count = 0

    for module_name, info in BIZAXL_OPTIONAL_MODULES.items():
        if info["app"] not in installed_apps:
            continue
        should_show = module_name in selected_set
        _set_workspace_visibility(module_name, should_show)
        _set_module_search_visibility(module_name, should_show)
        if should_show:
            shown_count += 1
        else:
            hidden_count += 1

    frappe.db.commit()
    frappe.clear_cache()
    return {"status": "success", "shown": shown_count, "hidden": hidden_count}


@frappe.whitelist()
def apply_profile(app_name):
    """Apply a vertical app's bizaxl.json profile."""
    profiles = get_installed_app_profiles()
    profile = next((p for p in profiles if p.get("app_name") == app_name), None)
    if not profile:
        frappe.throw("No bizaxl.json found for app: " + app_name)
    show = set(profile.get("show_modules", []))
    return apply_module_selection(list(show))


@frappe.whitelist()
def activate_module(module_name):
    """
    Activate a single optional module — used when client upgrades subscription.
    Installs nothing — just makes the already-installed app visible.
    """
    if module_name not in BIZAXL_OPTIONAL_MODULES:
        frappe.throw(f"{module_name} is not a valid BizAxl optional module.")

    info = BIZAXL_OPTIONAL_MODULES[module_name]
    if info["app"] not in frappe.get_installed_apps():
        frappe.throw(
            f"{module_name} requires {info['app']} to be installed first. "
            f"Run: bench --site {frappe.local.site} install-app {info['app']}"
        )

    _set_workspace_visibility(module_name, True)
    _set_module_search_visibility(module_name, True)
    frappe.db.commit()
    frappe.clear_cache()
    return {"status": "success", "message": f"{module_name} activated successfully."}


@frappe.whitelist()
def deactivate_module(module_name):
    """
    Deactivate a single optional module — used when client downgrades subscription.
    Does not uninstall the app — just hides it.
    """
    if module_name not in BIZAXL_OPTIONAL_MODULES:
        frappe.throw(f"{module_name} is not a valid BizAxl optional module.")

    _set_workspace_visibility(module_name, False)
    _set_module_search_visibility(module_name, False)
    frappe.db.commit()
    frappe.clear_cache()
    return {"status": "success", "message": f"{module_name} deactivated successfully."}


@frappe.whitelist()
def restore_all_modules():
    """Make all installed BizAxl optional modules visible."""
    all_modules = [
        m for m, info in BIZAXL_OPTIONAL_MODULES.items()
        if info["app"] in frappe.get_installed_apps()
    ]
    return apply_module_selection(all_modules)


@frappe.whitelist()
def get_current_visibility():
    """Return current workspace visibility for BizAxl modules."""
    results = []
    for module_name in list(BIZAXL_CORE_MODULES) + list(BIZAXL_OPTIONAL_MODULES.keys()):
        ws = frappe.get_all("Workspace",
            filters={"module": module_name, "public": 1},
            fields=["name", "module", "is_hidden", "title"])
        results.extend(ws)
    return results


def _set_workspace_visibility(module_name, visible):
    try:
        frappe.db.sql(
            "UPDATE `tabWorkspace` SET is_hidden = %s WHERE module = %s AND public = 1",
            (0 if visible else 1, module_name)
        )
    except Exception as e:
        frappe.log_error(str(e), "BizAxl workspace visibility error")


def _set_module_search_visibility(module_name, visible):
    try:
        frappe.db.sql(
            "UPDATE `tabDocType` SET hide_toolbar = %s WHERE module = %s AND issingle = 0",
            (0 if visible else 1, module_name)
        )
        frappe.db.sql(
            "UPDATE `tabReport` SET disabled = %s WHERE module = %s",
            (0 if visible else 1, module_name)
        )
    except Exception as e:
        frappe.log_error(str(e), "BizAxl search visibility error")
