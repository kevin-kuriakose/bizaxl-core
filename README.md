# BizAxl Core

Module Manager for BizAxl Apps on Frappe/ERPNext.

## What it does

- Integrates with the ERPNext Setup Wizard to let you choose which modules to enable
- Reads `bizaxl.json` from every installed app to know its module requirements
- Shows only relevant ERPNext modules — hides everything else
- Can be extended by any new app just by adding a `bizaxl.json` file

## Installation

```bash
bench get-app https://github.com/kevin-kuriakose/bizaxl_core.git
bench --site yoursite install-app bizaxl_core
```

After installation, run the ERPNext Setup Wizard — a new step will appear to select your modules.

## Adding a new app

Create a `bizaxl.json` in your app's root directory:

```json
{
    "app_name": "my_new_erp",
    "display_name": "MyEdge",
    "description": "Brief description of your app",
    "show_modules": ["Accounts", "Buying", "Selling"],
    "hide_modules": ["Manufacturing", "Agriculture"],
    "optional_modules": [
        {
            "module": "HR",
            "label": "HR & Payroll",
            "description": "Enable if you need HR features"
        }
    ]
}
```

That's all. BizAxl Core automatically detects it on install.

## Applying a profile manually

```bash
bench --site yoursite execute \
    bizaxl_core.api.module_manager.apply_profile \
    --args '{"app_name": "organ_donation_erp"}'
```

## Module categories

### Always enabled (Core)
- Accounting & Finance
- Buying & Procurement
- Sales
- Contacts

### Optional (enable per app)
- HR & Payroll
- Stock & Inventory
- Manufacturing
- Projects & Timesheets
- CRM & Leads
- Quality Management
- Website & CMS
- Asset Management
- Support & Helpdesk
- And more...

## License

MIT
