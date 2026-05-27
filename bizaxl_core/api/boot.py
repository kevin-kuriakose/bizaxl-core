import frappe


def filter_search_doctypes(bootinfo):
    """
    Filter can_read, can_search, can_create lists based on hidden BizAxl workspaces.
    Removes hidden module DocTypes from the awesomebar completely.
    """
    try:
        hidden_ws = frappe.get_all(
            "Workspace",
            filters={"is_hidden": 1, "public": 1},
            fields=["module", "title"]
        )

        if not hidden_ws:
            return

        hidden_modules = set()
        for ws in hidden_ws:
            if ws.module:
                hidden_modules.add(ws.module)
            if ws.title:
                hidden_modules.add(ws.title)

        # Build hidden doctypes dynamically from the database
        hidden_doctypes = set()
        for mod in hidden_modules:
            db_dts = frappe.get_all(
                "DocType",
                filters={"module": mod},
                fields=["name"],
                ignore_permissions=True
            )
            for dt in db_dts:
                hidden_doctypes.add(dt.name)

        if not hidden_doctypes:
            return

        # Filter page_info
        if hasattr(bootinfo, "page_info"):
            bootinfo.page_info = {
                k: v for k, v in (bootinfo.page_info or {}).items()
                if not any(mod.lower() in k.lower() for mod in hidden_modules)
            }

        # Filter allow_modules
        if bootinfo.get("user") and bootinfo.user.get("allow_modules"):
            bootinfo.user["allow_modules"] = [
                m for m in bootinfo.user["allow_modules"]
                if m not in hidden_modules
            ]

        # Filter all permission lists
        if bootinfo.get("user"):
            for attr in ["can_read", "can_write", "can_create",
                         "can_search", "can_delete", "can_import"]:
                original = bootinfo.user.get(attr) or []
                bootinfo.user[attr] = [d for d in original if d not in hidden_doctypes]

    except Exception as e:
        frappe.log_error(str(e), "BizAxl Boot Filter Error")

