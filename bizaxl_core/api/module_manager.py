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
}

VERTICAL_APPS = {
    "retail_erp", "energy_erp", "civic_erp",
    "museum_erp", "proserv_erp", "organ_donation_erp",
}


def get_installed_app_profiles():
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


@frappe.whitelist()
def get_module_config():
    optional = []
    for module, info in BIZAXL_OPTIONAL_MODULES.items():
        installed = info["app"] in frappe.get_installed_apps()
        optional.append({
            "module": module,
            "label": info["label"],
            "app": info["app"],
            "installed": installed,
            "checked": installed,
        })
    core = [{"module": m, "label": m.replace("BizAxl ", "")} for m in BIZAXL_CORE_MODULES]
    return {"core_modules": core, "optional_modules": optional}


@frappe.whitelist()
def apply_module_selection(selected_modules):
    if isinstance(selected_modules, str):
        selected_modules = json.loads(selected_modules)

    selected_set = set(selected_modules)
    selected_set.update(BIZAXL_CORE_MODULES)

    hidden_count = 0
    shown_count = 0

    for module_name, info in BIZAXL_OPTIONAL_MODULES.items():
        if info["app"] not in frappe.get_installed_apps():
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
    profiles = get_installed_app_profiles()
    profile = next((p for p in profiles if p.get("app_name") == app_name), None)
    if not profile:
        frappe.throw("No bizaxl.json found for app: " + app_name)
    show = set(profile.get("show_modules", []))
    return apply_module_selection(list(show))


@frappe.whitelist()
def restore_all_modules():
    all_modules = [m for m, info in BIZAXL_OPTIONAL_MODULES.items()
                   if info["app"] in frappe.get_installed_apps()]
    return apply_module_selection(all_modules)


@frappe.whitelist()
def get_current_visibility():
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
