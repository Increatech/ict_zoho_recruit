
import frappe, json
from frappe.utils import today, cint
from ..utils.ZohoService import ZoHoRecruitService
from ..utils.Template import get_job_openings_tmplt
from .Address import get_warehouse_address

@frappe.whitelist(allow_guest=True)
def auto_job_posting(employee, vacancy=1):
    if not employee:
        frappe.throw("Employee ID is required.")

    employee_doc = frappe.get_doc("Employee", employee)

    designation_description = ""
    required_skills = []

    if employee_doc.designation:
        designation_doc = frappe.get_doc(
            "Designation",
            employee_doc.designation
        )

        designation_description = designation_doc.description or ""

        for skill_row in designation_doc.skills:
            if skill_row.skill:
                required_skills.append(skill_row.skill)

    address = get_warehouse_address(employee_doc.department)
    job_opening = frappe.new_doc("Zoho Job Openings")

    job_opening.posting_title = employee_doc.designation or ""
    job_opening.title = employee_doc.designation or ""

    job_opening.number_of_positions = vacancy
    job_opening.salary = designation_doc.custom_salary or 0
    job_opening.work_experience = designation_doc.custom_work_experience or ""

    job_opening.department_name = employee_doc.department or ""
    job_opening.industry = designation_doc.custom_industry_type or ""
    job_opening.hiring_manager = "Elbrit Lifesciences Private Limited"
    job_opening.assigned_recruiters = "Elbrit Lifesciences Private Limited"
    
    job_opening.address = address.get("address")
    job_opening.city = address.get("city")
    job_opening.state = address.get("state")
    job_opening.country= address.get("country")
    job_opening.postal_code=address.get("pincode")
    
    job_opening.job_type = (
        employee_doc.employment_type.replace("-time", " time")
        if employee_doc.employment_type
        else ""
    )
    
    job_opening.job_description = designation_description

    for skill in required_skills:
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
        designation,
        as_list=True
    )
    
    if not list_format:
        return ", ".join(row[0].lower() for row in skills)
    
    return skills

