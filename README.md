# BizAxl Core

![BizAxl](https://img.shields.io/badge/BizAxl-Core-00e5a0?style=for-the-badge)
![Frappe](https://img.shields.io/badge/Frappe-v15-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

BizAxl Core is a module management app for Frappe/ERPNext. It lets you control which ERPNext modules are visible on your site — hiding unused features from the sidebar, search bar, and home page, while keeping the system clean and focused for your specific use case.

---

## What It Does

ERPNext ships with 20+ modules — Manufacturing, Agriculture, Healthcare, Education, and more. Most businesses only need a fraction of these. BizAxl Core lets you:

- **Hide unused modules** from the sidebar, search bar, and home page
- **Enable modules on demand** through a settings page (admin only)
- **Apply preset profiles** for common app types (RetailEdge, LifeEdge, etc.)
- **Run automatically** during the ERPNext setup wizard on new sites
- **Detect new apps** automatically via `bizaxl.json` files

---

## How It Works

BizAxl Core reads a `bizaxl.json` file from each installed app. This file defines which modules the app needs and which should be hidden. When you install BizAxl Core, it:

1. Scans all installed apps for `bizaxl.json` files
2. Builds a module selection UI in the ERPNext setup wizard
3. Hides unwanted modules from sidebar, search, and home page
4. Disables background jobs for hidden modules (saves CPU/RAM)
5. Patches ERPNext boot to exclude hidden DocTypes from the awesomebar

---

## Requirements

- Frappe **v15**
- ERPNext **v15**
- Python **3.10+**

---

## Installation

```bash
# Get the app
cd ~/frappe-bench
bench get-app https://github.com/kevin-kuriakose/bizaxl-core.git

# Install on your site
bench --site yoursite.local install-app bizaxl_core

# Migrate
bench --site yoursite.local migrate
bench restart
```

After installation, open `http://yoursite.local:8000` and complete the ERPNext setup wizard. A **BizAxl Module Setup** step will appear where you can select which modules to enable.

---

## Adding BizAxl Core to a New Site

```bash
# Full new site setup with BizAxl Core
bench new-site clientsite.local
bench --site clientsite.local install-app erpnext
bench --site clientsite.local install-app your_vertical_app
bench --site clientsite.local install-app bizaxl_core
bench --site clientsite.local migrate
bench restart
```

Open the site → complete setup wizard → select your modules → done.

---

## BizAxl Settings Page

After installation, admins can manage modules at any time:

**URL:** `http://yoursite.local:8000/app/bizaxl-settings`

**Or navigate to:** ERPNext Settings → BizAxl → BizAxl Settings

The settings page lets you:
- Select a preset app profile
- Toggle individual modules on/off
- Changes apply immediately on Save

**Access:** Only users with the **System Manager** role can view and edit this page.

---

## Module Profiles

BizAxl Core ships with preset profiles for BizAxl vertical apps:

| Profile | App | Hidden Modules |
|---------|-----|---------------|
| LifeEdge | organ_donation_erp | Manufacturing, Stock, CRM, Agriculture, etc. |
| RetailEdge | retail_erp | Manufacturing, Agriculture, Healthcare, etc. |
| EnergyEdge | energy_erp | Manufacturing, Agriculture, Education, etc. |
| CivicEdge | civic_erp | Manufacturing, Stock, Hospitality, etc. |
| MuseumEdge | museum_erp | Manufacturing, HR, Agriculture, etc. |
| ProEdge | proserv_erp | Manufacturing, Stock, Agriculture, etc. |

---

## Adding a New App

To make your app compatible with BizAxl Core, add a `bizaxl.json` file to your app's root directory:

```json
{
    "app_name": "my_new_erp",
    "display_name": "MyEdge",
    "description": "Brief description of your app",
    "show_modules": [
        "Accounts",
        "Buying",
        "Selling",
        "HR"
    ],
    "hide_modules": [
        "Manufacturing",
        "Agriculture",
        "Education",
        "Hospitality"
    ],
    "optional_modules": [
        {
            "module": "Stock",
            "label": "Stock & Inventory",
            "description": "Enable if you need inventory tracking"
        },
        {
            "module": "Projects",
            "label": "Projects & Timesheets",
            "description": "Enable for project management"
        },
        {
            "module": "CRM",
            "label": "CRM & Leads",
            "description": "Enable for lead and opportunity tracking"
        }
    ]
}
```

BizAxl Core automatically detects this file when the app is installed. No changes needed to BizAxl Core itself.

---

## Module Reference

### Core Modules (Always Enabled)
These modules are always visible and cannot be hidden:

| Module | Description |
|--------|-------------|
| Accounts | Accounting, invoices, payments, GL entries |
| Buying | Purchase orders, suppliers, procurement |
| Selling | Sales orders, customers, quotations |
| Contacts | Contact management |
| Users | User and role management |
| Setup | System configuration |

### Optional Modules
These can be enabled or disabled per site:

| Module | Description |
|--------|-------------|
| Stock | Inventory, warehouses, stock entries |
| Manufacturing | BOM, work orders, production planning |
| HR | Employees, leave, attendance |
| Payroll | Salary, payroll processing |
| Projects | Projects, tasks, timesheets |
| CRM | Leads, opportunities |
| Assets | Asset management and depreciation |
| Quality | Quality inspections and control |
| Support | Issues, helpdesk, service levels |
| Website | CMS, blog, web pages |
| Healthcare | Patients, clinical procedures |
| Education | Students, courses, programs |
| Agriculture | Crops, farm management |
| Hospitality | Hotel rooms, restaurant management |
| Non Profit | Members, donors, grants |
| Loan Management | Loans, disbursements |

---

## Manual Commands

### Apply a preset profile
```bash
cat > /tmp/apply.py << 'EOF'
from bizaxl_core.api.module_manager import apply_profile
result = apply_profile("organ_donation_erp")
print(result)
