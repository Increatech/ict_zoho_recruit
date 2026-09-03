import frappe
from .ZohoRequest import BaseRequest, ZohoAPIError, ZohoAuthError

class ZoHoTokenService(BaseRequest):
    __slots__ = ("settings",)

    def __init__(self):
        try:
            self.settings = frappe.get_single("Zoho Recruit Settings")
        except Exception as e:
            frappe.logger("ict_zoho_recruit").error(f"Failed to get Zoho Recruit Settings: {e}")
            raise ZohoAuthError("Zoho Recruit Settings not found. Please configure the settings first.") from e
        
        if not self.settings.enable_zoho_recruit_job_posting:
            frappe.logger("ict_zoho_recruit").warning("Zoho Recruit integration is disabled in settings")
            raise ZohoAuthError("Zoho Recruit integration is disabled. Please enable it in settings.")
        if not self.settings.client_id:
            frappe.logger("ict_zoho_recruit").error("Zoho Recruit Client ID is missing")
            raise ZohoAuthError("Zoho Recruit Client ID is missing. Please configure it in settings.")
        if not self.settings.client_secret:
            frappe.logger("ict_zoho_recruit").error("Zoho Recruit Client Secret is missing")
            raise ZohoAuthError("Zoho Recruit Client Secret is missing. Please configure it in settings.")
        if not self.settings.app_code:
            frappe.logger("ict_zoho_recruit").error("Zoho Recruit app code is missing")
            raise ZohoAuthError("Zoho Recruit app code is missing. Please configure it in settings.") 

        super().__init__(is_auth_request=True)
    
    @property
    def get_query_params(self):
        return {
            "client_id": self.settings.client_id,
            "client_secret": self.settings.get_password("client_secret"),
            "code": self.settings.app_code,
            "grant_type": "authorization_code"
        }

    def save_tokens(self, response: dict) -> None:
        if not response:
            frappe.logger("ict_zoho_recruit").error("Empty token response received")
            raise ZohoAuthError("Invalid token response received from Zoho.")
            
        access_token = response.get("access_token")
        refresh_token = response.get("refresh_token") 
        
        if not access_token:
            frappe.logger("ict_zoho_recruit").error("Access token not found in response")
            raise ZohoAuthError("Access token not found in Zoho response.")
        
        try:
            self.settings.access_token = access_token
            self.settings.set("access_token", access_token)
            if refresh_token:
                self.settings.refresh_token = refresh_token
                self.settings.set("refresh_token", refresh_token)
                
            self.settings.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.logger("ict_zoho_recruit").info("Tokens saved successfully")
        except Exception as e:
            frappe.logger("ict_zoho_recruit").error(f"Failed to save tokens: {e}")
            frappe.log_error(title="Token Save Error", message=frappe.get_traceback())
            raise ZohoAuthError(f"Failed to save tokens: {str(e)}") from e

    def get_tokens(self) -> None:
        try:
            frappe.logger("ict_zoho_recruit").info("Fetching new tokens from Zoho")
            res = self._post(query_params=self.get_query_params)
            self.save_tokens(res)
        except ZohoAPIError:
            raise
        except Exception as e:
            frappe.logger("ict_zoho_recruit").error(f"Failed to get tokens: {e}")
            raise ZohoAuthError(f"Failed to fetch tokens from Zoho: {str(e)}") from e

    def get_access_token(self) -> str:
        if not self.settings.access_token:
            self.get_tokens()
        token = self.settings.get_password("access_token")
        if not token:
            raise ZohoAuthError("Access token is still missing after refresh attempt.")
        return token

    def get_refresh_token(self) -> str:
        if not self.settings.refresh_token:
            self.get_tokens()
        token = self.settings.get_password("refresh_token")
        if not token:
            raise ZohoAuthError("Refresh token is still missing after refresh attempt.")
        return token

    @classmethod
    def refresh_access_token(cls):
        try:
            instance = cls.__new__(cls)
            instance.settings = frappe.get_single("Zoho Recruit Settings")
            
            if not instance.settings.refresh_token:
                frappe.logger("ict_zoho_recruit").error("Refresh token is missing for token refresh")
                raise ZohoAuthError("Zoho Recruit Refresh Token is missing. Please re-authenticate.")

            query_params = {
                "client_id": instance.settings.client_id,
                "client_secret": instance.settings.get_password("client_secret"),
                "refresh_token": instance.settings.get_password("refresh_token"),
                "grant_type": "refresh_token"
            }

            frappe.logger("ict_zoho_recruit").info("Refreshing access token")
            super(ZoHoTokenService, instance).__init__(is_auth_request=True)
            res = instance._post(query_params=query_params)
            instance.save_tokens(res)
            
            return instance.get_access_token()
        except ZohoAPIError:
            raise
        except Exception as e:
            frappe.logger("ict_zoho_recruit").error(f"Failed to refresh access token: {e}")
            raise ZohoAuthError(f"Failed to refresh access token: {str(e)}") from e
    