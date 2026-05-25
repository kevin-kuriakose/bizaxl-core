import frappe


HIDDEN_MODULE_DOCTYPES = {
    "Manufacturing": ["BOM", "Work Order", "Job Card", "Production Plan",
                      "Workstation", "Operation", "Routing", "BOM Update Tool",
                      "BOM Creator", "Manufacturing Settings", "BOM Update Log"],
    "Stock": ["Warehouse", "Stock Entry", "Material Request", "Delivery Note",
              "Purchase Receipt", "Pick List", "Delivery Trip", "Stock Ledger Entry",
              "Serial No", "Batch", "Item Price", "Stock Reconciliation",
              "Landed Cost Voucher", "Stock Settings", "Putaway Rule",
              "Shipment", "Stock Reposting Settings"],
    "Assets": ["Asset", "Asset Movement", "Asset Maintenance", "Asset Repair",
               "Asset Category", "Asset Settings", "Asset Capitalization"],
    "CRM": ["Lead", "Opportunity", "CRM Settings", "Prospect"],
    "Projects": ["Project", "Task", "Timesheet", "Activity Type",
                 "Activity Cost", "Timesheet Detail"],
    "Support": ["Issue", "Warranty Claim", "Maintenance Schedule",
                "Maintenance Visit", "Service Level Agreement"],
    "Quality": ["Quality Inspection", "Quality Action", "Quality Meeting",
                "Quality Goal", "Quality Procedure", "Quality Review",
                "Quality Feedback", "Quality Settings"],
    "HR": ["Employee", "Branch", "Department", "Designation",
           "Leave Application", "Attendance", "Salary Slip",
           "Employee Transfer", "Employee Promotion", "Appraisal",
           "Training Program", "HR Settings"],
    "Payroll": ["Payroll Entry", "Salary Structure", "Salary Component",
                "Income Tax Slab", "Employee Tax Exemption Declaration"],
    "Website": ["Web Page", "Blog Post", "Website Settings", "Web Form",
                "Web Template", "Website Theme", "Homepage"],
    "Agriculture": ["Crop", "Land Unit", "Soil Analysis", "Plant Analysis",
                    "Fertilizer", "Crop Cycle", "Agriculture Settings"],
    "Healthcare": ["Patient", "Clinical Procedure", "Lab Test",
                   "Inpatient Record", "Healthcare Settings"],
    "Education": ["Student", "Course", "Program", "Student Group",
                  "Assessment Plan", "Education Settings"],
    "Hospitality": ["Hotel Room", "Restaurant Menu", "Restaurant Order Entry"],
    "Non Profit": ["Member", "Donor", "Grant Application",
                   "Membership", "Chapter", "Non Profit Settings"],
    "Loan Management": ["Loan", "Loan Application", "Loan Disbursement",
                        "Loan Repayment", "Loan Settings"],
    "Utilities": ["Dunning", "Process Deferred Accounting"],
    "E-commerce": ["Website Item", "E Commerce Settings", "Item Review",
                   "Wishlist", "Shopping Cart Settings"],
}


def filter_search_doctypes(bootinfo):
    """
    Filter can_read, can_search, can_create lists based on hidden modules.
    This removes hidden doctypes from the awesomebar completely.
    """
    try:
        # Get hidden modules from workspace
        hidden_ws = frappe.get_all(
            "Workspace",
            filters={"is_hidden": 1, "public": 1},
            fields=["module", "title"]
        )

        hidden_modules = set()
        for ws in hidden_ws:
            if ws.module:
                hidden_modules.add(ws.module)
            if ws.title:
                hidden_modules.add(ws.title)

        if not hidden_modules:
            return

        # Build set of doctypes to remove from search
        hidden_doctypes = set()
        for mod in hidden_modules:
            # From our mapping
            for dt in HIDDEN_MODULE_DOCTYPES.get(mod, []):
                hidden_doctypes.add(dt)
            # From database
            db_dts = frappe.get_all(
                "DocType",
                filters={"module": mod},
                fields=["name"],
                ignore_permissions=True
            )
            for dt in db_dts:
                hidden_doctypes.add(dt.name)

        # Filter workspace pages from boot
        if hasattr(bootinfo, "page_info"):
            bootinfo.page_info = {
                k: v for k, v in (bootinfo.page_info or {}).items()
                if not any(mod.lower() in k.lower() for mod in hidden_modules)
            }

        # Filter allowed pages
        if hasattr(bootinfo, "user") and hasattr(bootinfo.user, "allow_modules"):
            bootinfo.user.allow_modules = [
                m for m in (bootinfo.user.allow_modules or [])
                if m not in hidden_modules
            ]

        # Filter all boot user lists — bootinfo.user is a _dict
        if bootinfo.get("user"):
            for attr in ["can_read", "can_write", "can_create",
                         "can_search", "can_delete", "can_import"]:
                original = bootinfo.user.get(attr) or []
                filtered = [d for d in original if d not in hidden_doctypes]
                bootinfo.user[attr] = filtered

    except Exception as e:
        frappe.log_error(str(e), "BizAxl Boot Filter Error")
