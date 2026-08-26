import frappe, os
from .ZohoToken import ZoHoTokenService, BaseRequest
from urllib.parse import quote

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
        return {
            "Content-Type": "application/json",
            "Authorization" :f"Zoho-oauthtoken {self.tokenservice.refresh_access_token()}"
            }
        
    
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
                
                
    def _upload_attachment(self, doc):
            zoho_job_id = doc.zoho_job_opening_id

            if not zoho_job_id:
                frappe.throw("Zoho Job Opening ID is missing")

            attachment_fields = ["others", "job_summary"]
            results = []
            headers = self.get_request_headers.copy()

            for fieldname in attachment_fields:
                file_url = doc.get(fieldname)

                if not file_url:
                    continue

                if file_url.startswith("/"):
                    site_url = frappe.utils.get_url()
                    attachment_target_url = f"{site_url}{file_url}"
                else:
                    attachment_target_url = file_url

                params = {
                    "attachments_category": "Others",
                    "attachment_url": attachment_target_url
                }

                res_data = {}
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

                except Exception as e:
                    error_message = str(e)
                    if "DUPLICATE_DATA" in error_message or "Attachment link already exists" in error_message:
                        res_data = {
                            "status": "success", 
                            "message": "Attachment link already exists in Zoho"
                        }
                    else:
                        raise e

                results.append({
                    "field": fieldname,
                    "file_url": attachment_target_url,
                    "response": res_data
                })

            return results