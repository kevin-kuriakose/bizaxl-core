import frappe

def get_context(context):
    context.no_cache = 1

@frappe.whitelist()
def get_all_reports():
    skip_modules = {"Core", "Custom", "Desk", "Email", "Integrations",
                    "Printing", "Setup", "Workflow", "Contacts", "Website"}
    reports = frappe.get_all("Report",
        filters={"disabled": 0, "report_type": ["!=", ""]},
        fields=["name", "module", "report_type"],
        order_by="module, name"
    )
    return [r for r in reports if r.module not in skip_modules]
