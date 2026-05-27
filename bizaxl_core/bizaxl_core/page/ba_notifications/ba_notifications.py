import frappe


def get_context(context):
    context.no_cache = 1


@frappe.whitelist()
def get_all_notifications():
    notifications = frappe.get_all("Notification",
        fields=["name", "document_type", "subject", "enabled", "channel"],
        order_by="document_type, name"
    )
    result = []
    for n in notifications:
        exists = bool(frappe.db.exists("DocType", n.document_type))
        n["doctype_exists"] = exists
        # Get module from DocType
        if exists:
            n["module"] = frappe.db.get_value("DocType", n.document_type, "module") or "Unknown"
        else:
            n["module"] = "Unknown"
        result.append(n)
    return result


@frappe.whitelist()
def toggle_notification(name, enabled):
    frappe.db.set_value("Notification", name, "enabled", int(enabled))
    frappe.db.commit()
    return {"status": "success"}
