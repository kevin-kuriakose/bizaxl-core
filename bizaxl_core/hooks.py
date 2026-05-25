app_name = "bizaxl_core"
app_title = "BizAxl Core"
app_publisher = "BizAxl"
app_description = "Module Manager for BizAxl Apps"
app_email = "dev@bizaxl.com"
app_license = "MIT"
app_version = "1.0.0"
required_apps = ["frappe"]

# Override boot info to filter search doctypes based on hidden modules
extend_bootinfo = ["bizaxl_core.api.boot.filter_search_doctypes"]

# Add BizAxl Settings to ERPNext Settings menu
fixtures = [
    {
        "doctype": "Workspace Link",
        "filters": [["parent", "=", "ERPNext Settings"]]
    }
]
