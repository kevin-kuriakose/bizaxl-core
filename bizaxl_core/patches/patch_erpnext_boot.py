import frappe
import os


def execute():
    """Patch ERPNext boot.py to filter hidden modules from awesomebar."""
    try:
        boot_path = frappe.get_app_path("erpnext", "startup", "boot.py")
    except Exception:
        print("ERPNext not installed — skipping patch")
        return

    if not os.path.exists(boot_path):
        print("ERPNext boot.py not found — skipping")
        return

    content = open(boot_path).read()

    if "_filter_bootinfo_for_hidden_modules(bootinfo)" in content:
        print("BizAxl boot patch already applied")
        return

    lines = content.split('\n')

    helper = [
        '',
        'def _get_hidden_doctypes():',
        '    try:',
        '        hidden_ws = frappe.get_all("Workspace",',
        '            filters={"is_hidden": 1, "public": 0},',
        '            fields=["module", "title"], ignore_permissions=True)',
        '        hidden_modules = set()',
        '        for ws in hidden_ws:',
        '            if ws.module: hidden_modules.add(ws.module)',
        '            if ws.title: hidden_modules.add(ws.title)',
        '        hidden_modules.update(["Manufacturing","Stock","CRM","Projects",',
        '            "Support","Assets","Quality","HR","Payroll","Website",',
        '            "Agriculture","Healthcare","Education","Hospitality",',
        '            "Non Profit","Loan Management","Utilities","E-commerce","Maintenance"])',
        '        hidden_dts = set()',
        '        for mod in hidden_modules:',
        '            dts = frappe.get_all("DocType", filters={"module": mod},',
        '                fields=["name"], ignore_permissions=True)',
        '            for dt in dts: hidden_dts.add(dt.name)',
        '        hidden_dts.update(["Manufacturing Dashboard","CRM Dashboard",',
        '            "Maintenance Visit","Maintenance Schedule",',
        '            "Warranty Claim","Customer Complaint","Incoterm"])',
        '        return hidden_dts',
        '    except Exception: return set()',
        '',
        '',
        'def _filter_bootinfo_for_hidden_modules(bootinfo):',
        '    try:',
        '        hidden_dts = _get_hidden_doctypes()',
        '        hidden_ws = frappe.get_all("Workspace",',
        '            filters={"is_hidden": 1, "public": 0},',
        '            fields=["module", "title"], ignore_permissions=True)',
        '        hidden_modules = set()',
        '        for ws in hidden_ws:',
        '            if ws.module: hidden_modules.add(ws.module.lower())',
        '            if ws.title: hidden_modules.add(ws.title.lower())',
        '        if bootinfo.get("user"):',
        '            for key in ["can_read","can_write","can_create",',
        '                        "can_search","can_delete","can_import"]:',
        '                original = bootinfo.user.get(key) or []',
        '                bootinfo.user[key] = [d for d in original if d not in hidden_dts]',
        '        if bootinfo.get("page_info"):',
        '            filtered = {}',
        '            for name, data in (bootinfo.page_info or {}).items():',
        '                if not any(m in name.lower() for m in hidden_modules):',
        '                    filtered[name] = data',
        '            bootinfo.page_info = filtered',
        '        if bootinfo.get("dashboards"):',
        '            bootinfo["dashboards"] = [d for d in (bootinfo.dashboards or [])',
        '                if not any(m in (d.get("name") or "").lower() for m in hidden_modules)]',
        '    except Exception as e:',
        '        frappe.log_error(str(e), "BizAxl Boot Filter Error")',
        '',
        '',
    ]

    # Find boot_session and insert helpers before it
    insert_at = None
    for i, line in enumerate(lines):
        if line.startswith('def boot_session'):
            insert_at = i
            break

    if insert_at is None:
        print("boot_session not found")
        return

    lines = lines[:insert_at] + helper + lines[insert_at:]

    # Find end of boot_session and add filter call
    in_boot = False
    boot_end = None
    for i, line in enumerate(lines):
        if line.startswith('def boot_session'):
            in_boot = True
            continue
        if in_boot and line.startswith('def ') and 'boot_session' not in line:
            boot_end = i
            break

    if boot_end:
        lines.insert(boot_end, '')
        lines.insert(boot_end, '\t\t_filter_bootinfo_for_hidden_modules(bootinfo)')

    open(boot_path, 'w').write('\n'.join(lines))

    import subprocess
    r = subprocess.run(['python3', '-m', 'py_compile', boot_path],
                      capture_output=True, text=True)
    if r.returncode == 0:
        print("✅ BizAxl boot patch applied")
    else:
        open(boot_path, 'w').write(content)
        print("❌ Syntax error — restored original")
