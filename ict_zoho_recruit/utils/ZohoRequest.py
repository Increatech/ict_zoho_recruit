import json
import requests
from requests.exceptions import RequestException
import frappe

class BaseRequest:

    def __init__(self,is_auth_request: bool = False):
        self.base_url = "https://accounts.zoho.com/oauth/v2/token" if is_auth_request else "https://recruit.zoho.com/recruit/v2"

    def _request(self, method: str, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:

        try:
            response = requests.request(
                method=method,
                url=self.base_url+ url_suffix if url_suffix else self.base_url,
                data=json.dumps(payload) if method in {"POST", "PUT", "PATCH"} else None,
                params=query_params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            if "error" in response_data:
                frappe.throw(response_data.get("error"))
                
            return response_data
        
        except ValueError:
            return {"text": response.text}
        except RequestException as e:
            msg = f"Zoho API Request Failed [{method} {self.base_url}]: {e}"
            frappe.log_error(title="Zoho BaseRequest Error", message=msg)
            raise Exception(msg)

    def _post(self, url_suffix: str | None = None,  payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:
        return self._request("POST", url_suffix, payload, query_params, headers)

    def _get(self, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:
        return self._request("GET", url_suffix, payload, query_params, headers)
    
    def _patch(self, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:
        return self._request("PATCH", url_suffix, payload, query_params, headers)
    
    def _put(self, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:
        return self._request("PUT", url_suffix, payload, query_params, headers)