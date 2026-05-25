import frappe
from bizaxl_core.api.module_manager import apply_module_selection, apply_profile


def setup_modules(args):
    """Called by setup wizard to apply module selection."""
    selected = args.get("bizaxl_selected_modules", [])
    app_name = args.get("bizaxl_app_profile")

    if app_name:
        apply_profile(app_name)
    elif selected:
        if isinstance(selected, str):
            import json
            selected = json.loads(selected)
        apply_module_selection(selected)

    frappe.db.commit()
