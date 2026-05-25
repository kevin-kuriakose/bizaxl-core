import frappe


def after_install():
    """
    Runs after bizaxl_core is installed on a site.
    Scans all installed apps for bizaxl.json profiles.
    """
    frappe.db.commit()
    print("BizAxl Core installed. Run setup wizard to configure modules.")
    print("Or run: bench --site mysite execute bizaxl_core.api.module_manager.apply_profile --args '{\"app_name\": \"your_app\"}'")
