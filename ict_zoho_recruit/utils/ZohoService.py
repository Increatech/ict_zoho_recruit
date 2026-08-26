import frappe
from .ZohoToken import ZoHoTokenService, BaseRequest


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