
import frappe, json
from frappe.utils import today, cint
from ..utils.ZohoService import ZoHoRecruitService
from ..utils.Template import get_job_openings_tmplt
from .Address import get_warehouse_address
from ict_zoho_recruit.api.RoleProfile import get_role_profile_details

@frappe.whitelist(allow_guest=True)
def auto_job_posting(employee, vacancy=1):
    if not employee:
        frappe.throw("Employee ID is required.")

    employee_doc = frappe.get_doc("Employee", employee)

    if not employee_doc.custom_role_profile:
        frappe.log_error(
            title="Auto Job Post Failed",
            message=(
                f"Employee {employee_doc.name} is not configured with a "
                "Role Profile, so the auto job post failed."
            ),
        )
        return

    role_profile_doc = frappe.get_doc("Role Profile", employee_doc.custom_role_profile)
    role_profile_data = get_role_profile_details(employee_doc.custom_role_profile)
    
    address = get_warehouse_address(role_profile_doc.custom_department)
    job_opening = frappe.new_doc("Zoho Job Openings")

    job_opening.posting_title = role_profile_data.get("designation") or employee_doc.designation or ""
    job_opening.title = role_profile_data.get("designation") or  employee_doc.designation or ""

    job_opening.number_of_positions = vacancy
    job_opening.salary = role_profile_doc.custom_salary or 0
    job_opening.work_experience = role_profile_doc.custom_work_experience or ""

    job_opening.department_name = role_profile_doc.custom_department or ""
    job_opening.industry = role_profile_doc.custom_industry_type or ""
    job_opening.hiring_manager = "Elbrit Lifesciences Private Limited"
    job_opening.assigned_recruiters = "Elbrit Lifesciences Private Limited"
    
    job_opening.address = address.get("address")
    job_opening.city = address.get("city")
    job_opening.state = address.get("state")
    job_opening.country= address.get("country")
    job_opening.postal_code=address.get("pincode")
    
    job_opening.job_type = employee_doc.employment_type
    job_opening.job_description = role_profile_data.get("description") or ""
    job_opening.requirements = role_profile_data.get("custom_requirements") or ""
    job_opening.benefits = role_profile_data.get("custom_benefits") or ""

    for skill in role_profile_data.get("skills"):
        job_opening.append("skils", {
            "skill": skill
        })
        
    job_opening.date_opened = frappe.utils.today()
    job_opening.insert(ignore_permissions=True)

    frappe.db.commit()
    
    return sync_zoho_recruit(document_ids=[job_opening.name], operation="create")



@frappe.whitelist()
def sync_zoho_recruit(document_ids, operation="create"):
    if isinstance(document_ids, str):
        document_ids = json.loads(document_ids)

    if not isinstance(document_ids, list) or not document_ids:
        frappe.throw("document_ids must be a non-empty list")

    if operation not in {"create", "update"}:
        frappe.throw("Invalid operation")

    service = ZoHoRecruitService()
    results = []

    for doc_id in document_ids:
        try:
            job_post = frappe.get_doc("Zoho Job Openings", doc_id)

            if operation == "create" and cint(job_post.is_complete):
                results.append({
                    "document_id": doc_id,
                    "status": "skipped",
                    "message": "Already synced",
                })
                continue

            zoho_id = job_post.zoho_job_opening_id

            if operation == "update" and not zoho_id:
                results.append({
                    "document_id": doc_id,
                    "status": "failed",
                    "message": "Zoho Job Opening ID not found",
                })
                continue

            payload = get_job_openings_tmplt(**job_post.as_dict())
            payload['data'][0]["Required_Skills"] = get_designation_skills(doc_id)

            if operation == "create":
                response = service._create_Job_Openings(
                    request_payload=payload
                )
                
            else:
                response = service._update_Job_Openings(
                    request_payload=payload,
                    id=zoho_id,
                )

            data = response.get("data") or []
            result = data[0] if data else {}
            details = result.get("details") or {}

            if result.get("code") != "SUCCESS":
                results.append({
                    "document_id": doc_id,
                    "status": "failed",
                    "response": response,
                })
                continue

            if operation == "create":
                frappe.enqueue(
                        "ict_zoho_recruit.utils.EmailService.send_email",
                        queue="default",
                        timeout=300,
                        doc_id=doc_id,
                        enqueue_after_commit=True)
                
                zoho_id = details.get("id")

                if not zoho_id:
                    results.append({
                        "document_id": doc_id,
                        "status": "failed",
                        "message": "Zoho record ID not returned",
                        "response": response,
                    })
                    continue
                
                job_post.db_set(
                    {
                        "is_complete": 1,
                        "zoho_job_opening_id": zoho_id,
                    },
                    update_modified=True,
                )
                
            service._upload_attachment(job_post)
            
            results.append({
                "document_id": doc_id,
                "status": "success",
                "operation": operation,
                "zoho_job_opening_id": zoho_id,
            })

        except Exception as exc:
            frappe.log_error(
                frappe.get_traceback(),
                f"Zoho Recruit Sync: {doc_id}",
            )

            results.append({
                "document_id": doc_id,
                "status": "failed",
                "error": str(exc),
            })

    return {
        "success": True,
        "operation": operation,
        "results": results,
    }

@frappe.whitelist(allow_guest=True)
def get_designation_skills(designation, list_format=False):
    skills = frappe.db.sql(
        """
        SELECT skill
        FROM `tabDesignation Skill`
        WHERE parent = %s
        """,
        (designation,),
        as_list=True
    )

    if not list_format:
        return ", ".join(
            row[0].lower()
            for row in skills
            if row[0]
        )

    return [row[0] for row in skills if row[0]]


