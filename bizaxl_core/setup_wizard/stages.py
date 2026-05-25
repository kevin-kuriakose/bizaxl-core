import frappe


def get_setup_stages(args=None):
    """
    Add BizAxl module selection step to ERPNext setup wizard.
    This is called by Frappe's setup wizard framework.
    """
    return [
        {
            "stage_name": "BizAxl Module Setup",
            "step_short_desc": "Choose your modules",
            "step_desc": "Select which ERPNext modules you need for your application",
            "idx": 3,  # Insert after basic ERPNext setup steps
            "steps": [
                {
                    "method": "bizaxl_core.setup_wizard.operations.setup_modules",
                    "args": args,
                }
            ],
        }
    ]
