
import frappe, json
from frappe.utils import today, cint
from ..utils.ZohoService import ZoHoRecruitService, ZohoAPIError, ZohoAuthError
from ..utils.Template import get_job_openings_tmplt
from .Address import get_warehouse_address
from ict_zoho_recruit.api.RoleProfile import get_role_profile_details

@frappe.whitelist(allow_guest=True)
def auto_job_posting(employee, vacancy=1):
    if not employee:
        frappe.throw("Employee ID is required.")

    try:
        employee_doc = frappe.get_doc("Employee", employee)
    except Exception as e:
        frappe.throw(f"Employee not found: {employee}")

    if not employee_doc.custom_role_profile:
        frappe.log_error(
            title="Auto Job Post Failed",
            message=(
                f"Employee {employee_doc.name} is not configured with a "
                "Role Profile, so the auto job post failed."
            ),
        )
        return

    try:
        role_profile_doc = frappe.get_doc("Role Profile", employee_doc.custom_role_profile)
        role_profile_data = get_role_profile_details(employee_doc.custom_role_profile)
        
        address = get_warehouse_address(role_profile_doc.custom_department)
        job_opening = frappe.new_doc("Zoho Job Openings")

        job_opening.posting_title = role_profile_doc.posting_title or employee_doc.designation or ""
        job_opening.title = role_profile_data.get("designation") or  employee_doc.designation or ""
        job_opening.job_category = role_profile_doc.job_category or ""

        job_opening.number_of_positions = vacancy
        job_opening.target_date = job_opening.get_target_date 
        job_opening.salary = role_profile_doc.custom_salary or 0
        job_opening.work_experience = role_profile_doc.custom_work_experience or ""

        job_opening.department_name = role_profile_doc.custom_department or ""
        job_opening.industry = role_profile_doc.custom_industry_type or ""
        job_opening.hiring_manager = "Elbrit Lifesciences Private Limited"
        job_opening.assigned_recruiters = "Elbrit Lifesciences Private Limited"
        
        job_opening.address = address.get("address") if address else ""
        job_opening.city = address.get("city") if address else ""
        job_opening.state = address.get("state") if address else ""
        job_opening.country= address.get("country") if address else ""
        job_opening.postal_code=address.get("pincode") if address else ""
        
        job_opening.job_type = employee_doc.employment_type
        job_opening.job_description = role_profile_data.get("description") or ""
        job_opening.requirements = role_profile_data.get("custom_requirements") or ""
        job_opening.benefits = role_profile_data.get("custom_benefits") or ""
        job_opening.role_profile = role_profile_doc.name or ""
        
        skillset = get_designation_skills(role_profile_doc.name, list_format=True)

        for skill in skillset:
            job_opening.append("skills", {
                "skill": skill
            })
            
        job_opening.date_opened = frappe.utils.today()
        job_opening.insert(ignore_permissions=True)

        frappe.db.commit()
        return sync_zoho_recruit(document_ids=[job_opening.name], operation="create")
        
    except Exception as e:
        frappe.log_error(
            title="Auto Job Post Creation Failed",
            message=frappe.get_traceback(),
        )
        raise
    



@frappe.whitelist()
def sync_zoho_recruit(document_ids, operation="create"):
    if isinstance(document_ids, str):
        try:
            document_ids = json.loads(document_ids)
        except json.JSONDecodeError as e:
            frappe.throw("Invalid document_ids format. Must be valid JSON array.")

    if not isinstance(document_ids, list) or not document_ids:
        frappe.throw("document_ids must be a non-empty list")

    if operation not in {"create", "update"}:
        frappe.throw("Invalid operation. Must be 'create' or 'update'.")

    try:
        service = ZoHoRecruitService()
    except (ZohoAPIError, ZohoAuthError) as e:
        return {
            "success": False,
            "operation": operation,
            "error": str(e),
            "results": []
        }
    
    results = []
    success_count = 0
    failed_count = 0

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
                failed_count += 1
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
                failed_count += 1
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
                    failed_count += 1
                    continue
                
                job_post.db_set(
                    {
                        "is_complete": 1,
                        "zoho_job_opening_id": zoho_id,
                    },
                    update_modified=True,
                )
                
            attachment_results = service._upload_attachment(job_post)
            
            results.append({
                "document_id": doc_id,
                "status": "success",
                "operation": operation,
                "zoho_job_opening_id": zoho_id,
                "attachments": attachment_results,
            })
            success_count += 1

        except ZohoAPIError as e:
            frappe.log_error(
                frappe.get_traceback(),
                f"Zoho Recruit Sync API Error: {doc_id}",
            )
            results.append({
                "document_id": doc_id,
                "status": "failed",
                "error": str(e),
            })
            failed_count += 1
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
            failed_count += 1


    return {
        "success": failed_count == 0,
        "operation": operation,
        "results": results,
        "summary": {
            "total": len(results),
            "success": success_count,
            "failed": failed_count,
            "skipped": len(results) - success_count - failed_count
        }
    }

@frappe.whitelist(allow_guest=True)
def get_designation_skills(designation, list_format=False):
    if not designation:
        return [] if list_format else ""
    
    try:
        cache_key = f"designation_skills:{designation}:{list_format}"
        cached_result = frappe.cache().get_value(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        skills = frappe.db.sql(
            """
            SELECT skill
            FROM `tabDesignation Skill`
            WHERE parent = %s
            ORDER BY idx ASC
            """,
            (designation,),
            pluck="skill",
            as_list=True
        )

        if not list_format:
            result = ", ".join(row.lower() for row in skills) if skills else ""
        else:
            result = skills
        
        frappe.cache().set_value(cache_key, result, expires_in_sec=3600)
        return result
        
    except Exception as e:
        return [] if list_format else ""


