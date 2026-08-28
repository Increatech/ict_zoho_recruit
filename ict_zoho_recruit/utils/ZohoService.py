import frappe, os
from .ZohoToken import ZoHoTokenService, BaseRequest
from urllib.parse import quote
from frappe.utils import cint

class ZoHoRecruitService(BaseRequest):
    API_PATH = '/Job_Openings'

    
    def __init__(self):
        self.settings = frappe.get_single("Zoho Recruit Settings")
        self.tokenservice = ZoHoTokenService()
        self._validate_settings()
        super().__init__(is_auth_request=False)
        
    def _validate_settings(self):
        if not self.settings.enable_zoho_recruit_job_posting:
            frappe.throw("Zoho Recruit integration is disabled.")

        required_fields = {
                "client_id": "Zoho Recruit Client ID",
                "client_secret": "Zoho Recruit Client Secret",
                "app_code": "Zoho Recruit app code",
            }

        for fieldname, label in required_fields.items():
            if not getattr(self.settings, fieldname, None):
                frappe.throw(f"{label} is missing.")
    
    @property
    def job_opening_template(self):
        """Return the default Zoho Recruit job-opening payload."""
        return frappe._dict(
            {
                "Job_Opening_Name": "",
                "Client_Name": self.settings.client_id,
                "Number_of_Positions": "",
                "Assigned_Recruiter": "",
                "Target_Date": "",
                "Job_Opening_Status": "In-progress",
                "Job_Type": "Full time",
                "Required_Skills": "",
                "Remote_Job": False,
            }
        )
        
    @property
    def get_request_headers(self):
        cache_key = f"zoho_request_headers:{self.settings.client_id}"

        headers = frappe.cache().get_value(cache_key)

        if not headers:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Zoho-oauthtoken {self.tokenservice.refresh_access_token()}",
            }

            frappe.cache().set_value(
                cache_key,
                headers,
                expires_in_sec=300,
            )

        return headers

        
    
    def _create_Job_Openings(self, request_payload):
        if not request_payload:
            frappe.throw("Job opening payload is required.")
            
        try:
            response = self._post(
                url_suffix=self.API_PATH,
                payload=request_payload,
                headers=self.get_request_headers,
            )

            return response
        

        except Exception:
            frappe.log_error(
                title="Zoho Recruit: Failed to create job opening",
                message=frappe.get_traceback(),
            )
            frappe.throw(
                "Failed to create job opening in Zoho Recruit. "
                "Please check the error log for details."
            )
            
    def _update_Job_Openings(self, request_payload, id):
            if not request_payload or not id:
                frappe.throw(f"Job {'request_payload' if not request_payload else 'id'} is required.")
            
            print(self.get_request_headers)  
            try:
                response = self._put(
                    url_suffix=f"{self.API_PATH}/{id}",
                    payload=request_payload,
                    headers=self.get_request_headers,
                )
    
                return response
    
            except Exception:
                frappe.log_error(
                    title="Zoho Recruit: Failed to update job opening",
                    message=frappe.get_traceback(),
                )
                frappe.throw(
                    "Failed to update job opening in Zoho Recruit. "
                    "Please check the error log for details."
                )
    
    def _get_attachment_files(self, zoho_job):
        file_names = frappe.get_all(
            "File",
            filters=[["File", "attached_to_name", "in", [zoho_job.name]]],
            pluck="name"
        )
        return [frappe.get_doc("File", name) for name in file_names]
                
    def _upload_attachment(self, doc):
        zoho_job_id = doc.zoho_job_opening_id

        if not zoho_job_id:
            frappe.throw("Zoho Job Opening ID is missing")

        attachment_fields = self._get_attachment_files(doc)
        results = []
        headers = self.get_request_headers.copy()

        for file_doc in attachment_fields:
            if cint(file_doc.custom_uploaded_to_zoho_recruit):
                continue

            if file_doc.file_url.startswith("/"):
                site_url = frappe.utils.get_url()
                attachment_target_url = f"{site_url}{file_doc.file_url}"
                
            else:
                attachment_target_url = file_doc.file_url
            
            params = {
                "attachments_category": "Others" if file_doc.attached_to_field == "others" else "Job Summary",
                "attachment_url": attachment_target_url
            }

            res_data = {}
            upload_success = False

            try:
                response = self._post(
                    url_suffix=f"/Job_Openings/{zoho_job_id}/Attachments",
                    headers=headers,
                    query_params=params,
                )
                
                if hasattr(response, "json"):
                    try:
                        res_data = response.json()
                    except Exception:
                        res_data = {"text": response.text}
                else:
                    res_data = response
                
                upload_success = True

            except Exception as e:
                error_message = str(e)
                if "DUPLICATE_DATA" in error_message or "Attachment link already exists" in error_message:
                    res_data = {
                        "status": "success", 
                        "message": "Attachment link already exists in Zoho"
                    }
                    upload_success = True
                else:
                    raise e

            if upload_success:
                
                data_list = res_data.get("data")
                if data_list and isinstance(data_list, list) and len(data_list) > 0:
                    file_doc.custom_uploaded_to_zoho_recruit = 1
                    file_doc.custom_zoho_attachment_id = data_list[0].get("details", {}).get("id")
                
                file_doc.save(ignore_permissions=True)

            results.append({
                "file_name": file_doc.name,
                "file_url": attachment_target_url,
                "response": res_data
            })

        return results
    
    def _delete_attachment(self, file_doc):
        file_doc = frappe.get_cached_doc("File", file_doc)
        
        if not cint(file_doc.custom_uploaded_to_zoho_recruit):
            return
        
        zoho_job_id = getattr(file_doc, "attached_to_name", None)
        zoho_attachment_id = getattr(file_doc, "custom_zoho_attachment_id", None)
        
        if not zoho_job_id or not zoho_attachment_id:
            return {"status": "skipped", "message": "Missing Zoho Job ID or Attachment ID for deletion"}

        try:
            zoho_job_doc = frappe.get_cached_doc("Zoho Job Openings", zoho_job_id)
            zoho_job_opening_id = getattr(zoho_job_doc, "zoho_job_opening_id", None)
            
            response = self._delete(
                url_suffix=f"/Job_Openings/{zoho_job_opening_id}/Attachments/{zoho_attachment_id}",
                headers=self.get_request_headers,
            )

            file_doc.custom_uploaded_to_zoho_recruit = 0
            file_doc.custom_zoho_attachment_id = None
            file_doc.save(ignore_permissions=True)

            return response
            
        except Exception as e:
            error_message = str(e)
            if "NOT_FOUND" in error_message or "204" in error_message:
                return {"status": "success", "message": "Attachment already deleted in Zoho"}
            
            raise e