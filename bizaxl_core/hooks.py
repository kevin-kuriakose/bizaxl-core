app_name = "bizaxl_core"
app_title = "BizAxl Core"
app_publisher = "BizAxl"
app_description = "Module Manager for BizAxl Apps"
app_email = "dev@bizaxl.com"
app_license = "MIT"
app_version = "1.0.0"
required_apps = ["frappe"]

extend_bootinfo = ["bizaxl_core.api.boot.filter_search_doctypes"]

fixtures = [
    {"doctype": "Workspace", "filters": [["name", "in", ["Home"]]]},
]
