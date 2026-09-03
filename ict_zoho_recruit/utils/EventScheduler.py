import frappe
from frappe.utils import today, cint
from frappe import _
from ict_zoho_recruit.api.ZohoRecruit import auto_job_posting

@frappe.whitelist(allow_guest=True)
def jobPostScheduler():
    frappe.logger("ict_zoho_recruit").info("Starting job post scheduler")
    
    try:
        settings = frappe.get_single("Zoho Recruit Settings")
    except Exception as e:
        frappe.logger("ict_zoho_recruit").error(f"Failed to get Zoho Recruit Settings: {e}")
        frappe.log_error(title="Scheduler Settings Error", message=frappe.get_traceback())
        return

    if not cint(settings.enable_zoho_recruit_job_posting):
        frappe.logger("ict_zoho_recruit").warning("Zoho Recruit job posting is disabled, skipping scheduler")
        return
    
    if not cint(settings.enable_auto_job_posting):
        frappe.logger("ict_zoho_recruit").warning("Auto job posting is disabled, skipping scheduler")
        return
    
    if not settings.default_job_post_company:
        frappe.logger("ict_zoho_recruit").error("Default job post company is not configured")
        return
    
    try:
        employees = get_employees_left_today(settings)
        frappe.logger("ict_zoho_recruit").info(f"Found {len(employees)} employees who left today")
        
        if not employees:
            frappe.logger("ict_zoho_recruit").info("No employees to process")
            return
        
        success_count = 0
        failed_count = 0
        
        for employee_data in employees:
            try:
                employee = employee_data.get("employee")
                vacancy = employee_data.get("vacancy", 1)
                
                frappe.logger("ict_zoho_recruit").info(f"Processing employee {employee} with vacancy {vacancy}")
                auto_job_posting(employee, vacancy)
                success_count += 1
                
            except Exception as e:
                frappe.logger("ict_zoho_recruit").error(f"Failed to process employee {employee_data.get('employee')}: {e}")
                frappe.log_error(
                    title="Scheduler Job Post Failed",
                    message=f"Employee: {employee_data.get('employee')}\nError: {str(e)}\n{frappe.get_traceback()}"
                )
                failed_count += 1
        
        frappe.logger("ict_zoho_recruit").info(
            f"Scheduler completed: {success_count} successful, {failed_count} failed"
        )
        
    except Exception as e:
        frappe.logger("ict_zoho_recruit").error(f"Scheduler failed: {e}")
        frappe.log_error(title="Job Post Scheduler Error", message=frappe.get_traceback())
    


def get_employees_left_today(settings):
    """Return vacancy count grouped by department and designation."""
    try:
        employees = frappe.get_all(
            "Employee",
            filters={
                "status": "Left",
                "relieving_date": today(),
                "company": settings.default_job_post_company,
            },
            fields=[
                "name",
                "department",
                "designation",
            ],
            order_by="department asc, designation asc, name asc",
        )
        
        if not employees:
            return []

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
        
    except Exception as e:
        frappe.logger("ict_zoho_recruit").error(f"Failed to get employees left today: {e}")
        return []

