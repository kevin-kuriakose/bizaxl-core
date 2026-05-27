import frappe
import json
import os
from frappe.model.document import Document
from bizaxl_core.api.module_manager import (
    apply_profile,
    apply_module_selection,
)

MODULE_FIELD_MAP = {
    "enable_stock":    "BizAxl Stock",
    "enable_hr":       "BizAxl HR",
    "enable_payroll":  "BizAxl Payroll",
    "enable_projects": "BizAxl Projects",
    "enable_crm":      "BizAxl CRM",
    "enable_assets":   "BizAxl Assets",
}

PROFILE_MAP = {
    "RetailEdge": "retail_erp",
    "EnergyEdge": "energy_erp",
    "CivicEdge":  "civic_erp",
    "MuseumEdge": "museum_erp",
    "ProEdge":    "proserv_erp",
    "LifeEdge":   "organ_donation_erp",
}


class BizAxlSettings(Document):
    def validate(self):
        if "System Manager" not in frappe.get_roles():
            frappe.throw("Only System Managers can change BizAxl Settings.")

    def on_update(self):
        if self.app_profile and self.app_profile != "Custom":
            app_name = PROFILE_MAP.get(self.app_profile)
            if app_name:
                apply_profile(app_name)
                self._sync_checkboxes_from_profile(app_name)
        else:
            self._apply_checkbox_selection()

        frappe.clear_cache()
        frappe.msgprint(
            "Module configuration applied. Please refresh your browser.",
            alert=True
        )

    def _apply_checkbox_selection(self):
        selected = []
        for field, module in MODULE_FIELD_MAP.items():
            if self.get(field):
                selected.append(module)
        apply_module_selection(selected)

    def _sync_checkboxes_from_profile(self, app_name):
        try:
            app_path = frappe.get_app_path(app_name)
            bizaxl_json = os.path.normpath(
                os.path.join(app_path, "..", "bizaxl.json")
            )
            if os.path.exists(bizaxl_json):
                with open(bizaxl_json) as f:
                    profile = json.load(f)
                show = set(profile.get("show_modules", []))
                for field, module in MODULE_FIELD_MAP.items():
                    frappe.db.set_value(
                        "BizAxl Settings", "BizAxl Settings",
                        field, 1 if module in show else 0
                    )
        except Exception:
            pass
