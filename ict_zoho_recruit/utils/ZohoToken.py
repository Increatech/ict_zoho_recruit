import frappe
from .ZohoRequest import BaseRequest

class ZoHoTokenService(BaseRequest):
    __slots__ = ("settings",)

    def __init__(self):
        self.settings = frappe.get_single("Zoho Recruit Settings")
        
        if not self.settings.enable_zoho_recruit_job_posting:
            frappe.throw("Zoho Recruit integration is disabled.")
        if not self.settings.client_id:
            frappe.throw("Zoho Recruit Client ID is missing.")
        if not self.settings.client_secret:
            frappe.throw("Zoho Recruit Client Secret is missing.")
        if not self.settings.app_code:
            frappe.throw("Zoho Recruit app code is missing.") 

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
            frappe.throw("Invalid response")
            
        access_token = response.get("access_token")
        refresh_token = response.get("refresh_token") 
        
        if access_token:
            self.settings.access_token = access_token
            self.settings.set("access_token", access_token)
        if refresh_token:
            self.settings.refresh_token = refresh_token
            self.settings.set("refresh_token", refresh_token)
            
        self.settings.save(ignore_permissions=True)
        frappe.db.commit()

    def get_tokens(self) -> None:
        res = self._post(query_params=self.get_query_params)
        self.save_tokens(res)

    def get_access_token(self) -> str | None:
        if not self.settings.access_token:
            self.get_tokens()
        return self.settings.get_password("access_token")

    def get_refresh_token(self) -> str | None:
        if not self.settings.refresh_token:
            self.get_tokens()
        return self.settings.get_password("refresh_token")

    @classmethod
    def refresh_access_token(cls):
        instance = cls.__new__(cls)
        instance.settings = frappe.get_single("Zoho Recruit Settings")
        
        if not instance.settings.refresh_token:
            frappe.throw("Zoho Recruit Refresh Token is missing.")

        query_params = {
            "client_id": instance.settings.client_id,
            "client_secret": instance.settings.get_password("client_secret"),
            "refresh_token": instance.settings.get_password("refresh_token"),
            "grant_type": "refresh_token"
        }

        super(ZoHoTokenService, instance).__init__(is_auth_request=True)
        res = instance._post(query_params=query_params)
        instance.save_tokens(res)
        
        return instance.get_access_token()
    