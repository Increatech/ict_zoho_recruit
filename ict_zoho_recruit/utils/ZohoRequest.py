import json
import requests
from requests.exceptions import RequestException
import frappe

class BaseRequest:

    def __init__(self,is_auth_request: bool = False):
        self.base_url = "https://accounts.zoho.com/oauth/v2/token" if is_auth_request else "https://recruit.zoho.com/recruit/v2"

    def _request(self, method: str, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None, files=None) -> dict | requests.Response | None:
        try:
            req_headers = dict(headers) if headers else {}

            if files is not None:
                req_headers.pop("Content-Type", None)
                req_headers.pop("content-type", None)
                request_data = None
            else:
                request_data = json.dumps(payload) if method in {"POST", "PUT", "PATCH"} else None

            response = requests.request(
                method=method,
                url=self.base_url + url_suffix if url_suffix else self.base_url,
                data=request_data,
                params=query_params,
                headers=req_headers,
                files=files,
                timeout=30
            )
            
            response.raise_for_status() 
            if files:
                return response

            if not response.text or not response.text.strip():
                return {}

            response_data = response.json()
            
            if "error" in response_data:
                frappe.throw(str(response_data.get("error")))        
            return response_data
        
        except ValueError as e:
            print(f"JSON Decode Warning: {e}")
            if files:
                return response
            return {"text": response.text if 'response' in locals() else str(e)}
            
        except RequestException as e:
            error_details = ""
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_details = e.response.text
            except Exception:
                pass
            
            msg = f"Zoho API Request Failed [{method}]: {e} | Response Body: {error_details}"
            print(msg)
            frappe.log_error(title="Zoho BaseRequest Error", message=msg)
            raise Exception(msg)
                    
    def _post(self, url_suffix: str | None = None,  payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None, files=None) -> dict | None:
        return self._request("POST", url_suffix, payload, query_params, headers, files)

    def _get(self, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:
        return self._request("GET", url_suffix, payload, query_params, headers)
    
    def _patch(self, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:
        return self._request("PATCH", url_suffix, payload, query_params, headers)
    
    def _put(self, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:
        return self._request("PUT", url_suffix, payload, query_params, headers)
    
    def _delete(self, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:
        return self._request("DELETE", url_suffix=url_suffix, payload=payload, query_params=query_params, headers=headers)