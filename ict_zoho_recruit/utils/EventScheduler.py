import frappe
from frappe.utils import today, cint
from frappe import _
from ..api.zoho_recruit import auto_job_posting

@frappe.whitelist(allow_guest=True)
def jobPostScheduler():
    settings = frappe.get_single("Zoho Recruit Settings")
    
    if not cint(settings.enable_zoho_recruit_job_posting) or cint(settings.enable_auto_job_posting):
            frappe.throw("Zoho Recruit integration or Auto Job Posting is disabled.")
    
    employees = get_employees_left_today()
    
    for employee in employees:
        auto_job_posting(employee.get("employee"), employee.get("vacancy"))
    


def get_employees_left_today():
    """Return vacancy count grouped by department and designation."""

    employees = frappe.get_all(
        "Employee",
        filters={
            "status": "Left",
            "relieving_date": today(),
            "company": "Elbrit Lifesciences Private Limited",
        },
        fields=[
            "name",
            "department",
            "designation",
        ],
        order_by="department asc, designation asc, name asc",
    )

    grouped = {}

    for employee in employees:
        key = (
            employee.department or "",
            employee.designation or "",
        )

        if key not in grouped:
            grouped[key] = {
                "employee": employee.name,
                "department": employee.department or "",
                "designation": employee.designation or "",
                "vacancy": 0,
            }

        grouped[key]["vacancy"] += 1

    return list(grouped.values())

