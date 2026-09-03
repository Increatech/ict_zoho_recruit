import frappe, os
from .ZohoToken import ZoHoTokenService, BaseRequest, ZohoAPIError, ZohoAuthError
from urllib.parse import quote
from frappe.utils import cint

class ZoHoRecruitService(BaseRequest):
    API_PATH = '/Job_Openings'

    
    def __init__(self):
        try:
            self.settings = frappe.get_single("Zoho Recruit Settings")
        except Exception as e:
            frappe.logger("ict_zoho_recruit").error(f"Failed to get Zoho Recruit Settings: {e}")
            raise ZohoAuthError("Zoho Recruit Settings not found. Please configure the settings first.") from e
        
        self._validate_settings()
        self.tokenservice = ZoHoTokenService()
        super().__init__(is_auth_request=False)
        
    def _validate_settings(self):
        if not self.settings.enable_zoho_recruit_job_posting:
            raise ZohoAuthError("Zoho Recruit integration is disabled. Please enable it in settings.")

        required_fields = {
                "client_id": "Zoho Recruit Client ID",
                "client_secret": "Zoho Recruit Client Secret",
                "app_code": "Zoho Recruit app code",
            }

        missing_fields = []
        for fieldname, label in required_fields.items():
            if not getattr(self.settings, fieldname, None):
                missing_fields.append(label)
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            frappe.logger("ict_zoho_recruit").error(error_msg)
            raise ZohoAuthError(error_msg)
    
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
            try:
                access_token = self.tokenservice.refresh_access_token()
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Zoho-oauthtoken {access_token}",
                }

                frappe.cache().set_value(
                    cache_key,
                    headers,
                    expires_in_sec=300,
                )
                frappe.logger("ict_zoho_recruit").debug("Request headers cached successfully")
            except ZohoAPIError:
                raise
            except Exception as e:
                frappe.logger("ict_zoho_recruit").error(f"Failed to get request headers: {e}")
                raise ZohoAPIError(f"Failed to generate request headers: {str(e)}") from e

        return headers

        
    
    def _create_Job_Openings(self, request_payload):
        if not request_payload:
            frappe.logger("ict_zoho_recruit").error("Job opening payload is empty")
            raise ZohoAPIError("Job opening payload is required.")
            
        try:
            frappe.logger("ict_zoho_recruit").info("Creating job opening in Zoho Recruit")
            response = self._post(
                url_suffix=self.API_PATH,
                payload=request_payload,
                headers=self.get_request_headers,
            )
            frappe.logger("ict_zoho_recruit").info("Job opening created successfully in Zoho Recruit")
            return response
        
        except ZohoAPIError:
            raise
        except Exception as e:
            frappe.logger("ict_zoho_recruit").error(f"Failed to create job opening: {e}")
            frappe.log_error(
                title="Zoho Recruit: Failed to create job opening",
                message=frappe.get_traceback(),
            )
            raise ZohoAPIError(
                "Failed to create job opening in Zoho Recruit. "
                "Please check the error log for details."
            ) from e
            
    def _update_Job_Openings(self, request_payload, id):
            if not request_payload or not id:
                missing = "request_payload" if not request_payload else "id"
                frappe.logger("ict_zoho_recruit").error(f"Job {missing} is required for update")
                raise ZohoAPIError(f"Job {missing} is required.")
            
            try:
                frappe.logger("ict_zoho_recruit").info(f"Updating job opening {id} in Zoho Recruit")
                response = self._put(
                    url_suffix=f"{self.API_PATH}/{id}",
                    payload=request_payload,
                    headers=self.get_request_headers,
                )
                frappe.logger("ict_zoho_recruit").info(f"Job opening {id} updated successfully")
                return response
    
            except ZohoAPIError:
                raise
            except Exception as e:
                frappe.logger("ict_zoho_recruit").error(f"Failed to update job opening {id}: {e}")
                frappe.log_error(
                    title="Zoho Recruit: Failed to update job opening",
                    message=frappe.get_traceback(),
                )
                raise ZohoAPIError(
                    "Failed to update job opening in Zoho Recruit. "
                    "Please check the error log for details."
                ) from e
    
    def _get_attachment_files(self, zoho_job):
        try:
            file_names = frappe.get_all(
                "File",
                filters={
                    "attached_to_name": zoho_job.name,
                    "attached_to_doctype": "Zoho Job Openings"
                },
                pluck="name"
            )
            if not file_names:
                frappe.logger("ict_zoho_recruit").debug(f"No attachments found for job {zoho_job.name}")
                return []
            
            frappe.logger("ict_zoho_recruit").debug(f"Found {len(file_names)} attachments for job {zoho_job.name}")
            return [frappe.get_doc("File", name) for name in file_names]
        except Exception as e:
            frappe.logger("ict_zoho_recruit").error(f"Failed to get attachment files: {e}")
            return []
                
    def _upload_attachment(self, doc):
        zoho_job_id = doc.zoho_job_opening_id

        if not zoho_job_id:
            frappe.logger("ict_zoho_recruit").error("Zoho Job Opening ID is missing for attachment upload")
            raise ZohoAPIError("Zoho Job Opening ID is missing")

        attachment_fields = self._get_attachment_files(doc)
        if not attachment_fields:
            frappe.logger("ict_zoho_recruit").debug(f"No attachments to upload for job {doc.name}")
            return []
        
        results = []
        headers = self.get_request_headers.copy()
        site_url = frappe.utils.get_url()

        for file_doc in attachment_fields:
            if cint(file_doc.custom_uploaded_to_zoho_recruit):
                frappe.logger("ict_zoho_recruit").debug(f"File {file_doc.name} already uploaded to Zoho, skipping")
                continue

            try:
                attachment_target_url = (
                    f"{site_url}{file_doc.file_url}" 
                    if file_doc.file_url.startswith("/") 
                    else file_doc.file_url
                )
                
                params = {
                    "attachments_category": "Others" if file_doc.attached_to_field == "others" else "Job Summary",
                    "attachment_url": attachment_target_url
                }

                frappe.logger("ict_zoho_recruit").info(f"Uploading attachment {file_doc.name} to Zoho")
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
                
                data_list = res_data.get("data")
                if data_list and isinstance(data_list, list) and len(data_list) > 0:
                    file_doc.custom_uploaded_to_zoho_recruit = 1
                    file_doc.custom_zoho_attachment_id = data_list[0].get("details", {}).get("id")
                    file_doc.save(ignore_permissions=True)
                    frappe.logger("ict_zoho_recruit").info(f"Attachment {file_doc.name} uploaded successfully")

                results.append({
                    "file_name": file_doc.name,
                    "file_url": attachment_target_url,
                    "response": res_data,
                    "status": "success"
                })

            except ZohoAPIError as e:
                error_message = str(e)
                if "DUPLICATE_DATA" in error_message or "Attachment link already exists" in error_message:
                    frappe.logger("ict_zoho_recruit").warning(f"Attachment {file_doc.name} already exists in Zoho")
                    results.append({
                        "file_name": file_doc.name,
                        "file_url": attachment_target_url,
                        "response": {"status": "success", "message": "Attachment link already exists in Zoho"},
                        "status": "skipped"
                    })
                else:
                    frappe.logger("ict_zoho_recruit").error(f"Failed to upload attachment {file_doc.name}: {e}")
                    results.append({
                        "file_name": file_doc.name,
                        "file_url": attachment_target_url,
                        "response": str(e),
                        "status": "failed"
                    })
            except Exception as e:
                frappe.logger("ict_zoho_recruit").error(f"Unexpected error uploading attachment {file_doc.name}: {e}")
                results.append({
                    "file_name": file_doc.name,
                    "file_url": attachment_target_url,
                    "response": str(e),
                    "status": "failed"
                })

        return results
    
    def _delete_attachment(self, file_doc):
        try:
            file_doc = frappe.get_cached_doc("File", file_doc)
        except Exception as e:
            frappe.logger("ict_zoho_recruit").error(f"Failed to get File document {file_doc}: {e}")
            return {"status": "failed", "message": f"File not found: {str(e)}"}
        
        if not cint(file_doc.custom_uploaded_to_zoho_recruit):
            frappe.logger("ict_zoho_recruit").debug(f"File {file_doc.name} not uploaded to Zoho, skipping deletion")
            return {"status": "skipped", "message": "File not uploaded to Zoho"}
        
        zoho_job_id = getattr(file_doc, "attached_to_name", None)
        zoho_attachment_id = getattr(file_doc, "custom_zoho_attachment_id", None)
        
        if not zoho_job_id or not zoho_attachment_id:
            frappe.logger("ict_zoho_recruit").warning(f"Missing Zoho Job ID or Attachment ID for file {file_doc.name}")
            return {"status": "skipped", "message": "Missing Zoho Job ID or Attachment ID for deletion"}

        try:
            zoho_job_doc = frappe.get_cached_doc("Zoho Job Openings", zoho_job_id)
            zoho_job_opening_id = getattr(zoho_job_doc, "zoho_job_opening_id", None)
            
            if not zoho_job_opening_id:
                frappe.logger("ict_zoho_recruit").warning(f"Zoho Job Opening ID not found for job {zoho_job_id}")
                return {"status": "skipped", "message": "Zoho Job Opening ID not found"}
            
            frappe.logger("ict_zoho_recruit").info(f"Deleting attachment {zoho_attachment_id} from Zoho")
            response = self._delete(
                url_suffix=f"/Job_Openings/{zoho_job_opening_id}/Attachments/{zoho_attachment_id}",
                headers=self.get_request_headers,
            )

            file_doc.custom_uploaded_to_zoho_recruit = 0
            file_doc.custom_zoho_attachment_id = None
            file_doc.save(ignore_permissions=True)
            frappe.logger("ict_zoho_recruit").info(f"Attachment {file_doc.name} deleted successfully from Zoho")

            return response
            
        except ZohoAPIError as e:
            error_message = str(e)
            if "NOT_FOUND" in error_message or "204" in error_message:
                frappe.logger("ict_zoho_recruit").warning(f"Attachment {zoho_attachment_id} already deleted in Zoho")
                file_doc.custom_uploaded_to_zoho_recruit = 0
                file_doc.custom_zoho_attachment_id = None
                file_doc.save(ignore_permissions=True)
                return {"status": "success", "message": "Attachment already deleted in Zoho"}
            raise e
        except Exception as e:
            frappe.logger("ict_zoho_recruit").error(f"Failed to delete attachment {file_doc.name}: {e}")
            raise ZohoAPIError(f"Failed to delete attachment: {str(e)}") from e