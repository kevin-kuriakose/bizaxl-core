import frappe
from frappe.model.document import Document
from bizaxl_core.api.module_manager import (
    apply_profile, restore_module, apply_module_selection,
    _block_module_from_search, _set_workspace_visibility,
    _disable_domain, _restore_module_to_search, _enable_domain,
    _fix_home_workspace, ERPNEXT_MODULES
)


MODULE_FIELD_MAP = {
    "enable_stock":         "Stock",
    "enable_manufacturing": "Manufacturing",
    "enable_hr":            "HR",
    "enable_projects":      "Projects",
    "enable_crm":           "CRM",
    "enable_assets":        "Assets",
    "enable_quality":       "Quality",
    "enable_support":       "Support",
    "enable_website":       "Website",
    "enable_healthcare":    "Healthcare",
    "enable_education":     "Education",
    "enable_non_profit":    "Non Profit",
    "enable_agriculture":   "Agriculture",
}


class BizAxlSettings(Document):
    def validate(self):
        # Only System Manager can save
        if "System Manager" not in frappe.get_roles():
            frappe.throw("Only System Managers can change BizAxl Settings.")

    def on_update(self):
        """Apply module changes when settings are saved."""
        if self.app_profile and self.app_profile != "Custom":
            # Apply preset profile
            profile_map = {
                "RetailEdge":  "retail_erp",
                "EnergyEdge":  "energy_erp",
                "CivicEdge":   "civic_erp",
                "MuseumEdge":  "museum_erp",
                "ProEdge":     "proserv_erp",
                "LifeEdge":    "organ_donation_erp",
            }
            app_name = profile_map.get(self.app_profile)
            if app_name:
                apply_profile(app_name)
                self._sync_checkboxes_from_profile(app_name)
        else:
            # Apply manual checkbox selection
            self._apply_checkbox_selection()

        frappe.clear_cache()
        frappe.msgprint(
            "Module configuration applied successfully. "
            "Please refresh your browser.",
            alert=True
        )

    def _apply_checkbox_selection(self):
        """Apply module visibility based on checkboxes."""
        selected = set()
        # Always add core modules
        for mod, info in ERPNEXT_MODULES.items():
            if info["core"]:
                selected.add(mod)

        for field, module in MODULE_FIELD_MAP.items():
            if self.get(field):
                selected.add(module)
                _restore_module_to_search(module)
                _set_workspace_visibility(module, True)
                _enable_domain(module)
            else:
                _block_module_from_search(module)
                _set_workspace_visibility(module, False)
                _disable_domain(module)

        _fix_home_workspace(selected)
        frappe.db.commit()

    def _sync_checkboxes_from_profile(self, app_name):
        """Update checkboxes to match the selected profile."""
        import json
        import os
        try:
            app_path = frappe.get_app_path(app_name)
            bizaxl_json = os.path.normpath(
                os.path.join(app_path, "..", "bizaxl.json")
            )
            if os.path.exists(bizaxl_json):
                profile = json.load(open(bizaxl_json))
                show = set(profile.get("show_modules", []))
                for field, module in MODULE_FIELD_MAP.items():
                    frappe.db.set_value(
                        "BizAxl Settings", "BizAxl Settings",
                        field, 1 if module in show else 0
                    )
        except Exception:
            pass
