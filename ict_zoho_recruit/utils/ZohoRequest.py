import json
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
import frappe
from frappe import _

class ZohoAPIError(Exception):
    """Custom exception for Zoho API errors"""
    def __init__(self, message, status_code=None, response_body=None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)

class ZohoAuthError(ZohoAPIError):
    """Exception for authentication/authorization errors"""
    pass

class ZohoRateLimitError(ZohoAPIError):
    """Exception for rate limiting errors"""
    pass

class BaseRequest:

    def __init__(self, is_auth_request: bool = False):
        self.base_url = "https://accounts.zoho.com/oauth/v2/token" if is_auth_request else "https://recruit.zoho.com/recruit/v2"

    def _request(self, method: str, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None, files=None) -> dict | requests.Response | None:
        req_headers = dict(headers) if headers else {}
        response = None
        
        try:
            if files is not None:
                req_headers.pop("Content-Type", None)
                req_headers.pop("content-type", None)
                request_data = None
            else:
                request_data = json.dumps(payload) if method in {"POST", "PUT", "PATCH"} else None

            url = self.base_url + url_suffix if url_suffix else self.base_url
            
            response = requests.request(
                method=method,
                url=url,
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
                error_msg = response_data.get("error", {}).get("message", str(response_data.get("error")))
                raise ZohoAPIError(error_msg, status_code=response.status_code, response_body=response_data)
                
            return response_data
        
        except ValueError as e:
            if files:
                return response
            return {"text": response.text if response else str(e)}
            
        except Timeout as e:
            msg = f"Zoho API Request Timeout [{method} {url_suffix}]: {e}"
            frappe.log_error(title="Zoho API Timeout", message=msg)
            raise ZohoAPIError(msg, status_code=408) from e
            
        except ConnectionError as e:
            msg = f"Zoho API Connection Error [{method} {url_suffix}]: {e}"
            frappe.log_error(title="Zoho API Connection Error", message=msg)
            raise ZohoAPIError(msg) from e
            
        except RequestException as e:
            error_details = ""
            status_code = None
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_details = e.response.text
                    status_code = e.response.status_code
            except Exception:
                pass
            
            msg = f"Zoho API Request Failed [{method} {url_suffix}]: {str(e)} | Status: {status_code} | Response: {error_details[:500] if error_details else 'N/A'}"
            frappe.log_error(title="Zoho API Request Error", message=msg)
            raise ZohoAPIError(msg, status_code=status_code, response_body=error_details) from e
        
        except ZohoAPIError:
            raise
            
        except Exception as e:
            msg = f"Unexpected error in Zoho API request [{method} {url_suffix}]: {str(e)}"
            frappe.log_error(title="Zoho API Unexpected Error", message=frappe.get_traceback())
            raise ZohoAPIError(msg) from e
                    
    def _post(self, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None, files=None) -> dict | None:
        return self._request("POST", url_suffix, payload, query_params, headers, files)

    def _get(self, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:
        return self._request("GET", url_suffix, payload, query_params, headers)
    
    def _patch(self, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:
        return self._request("PATCH", url_suffix, payload, query_params, headers)
    
    def _put(self, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:
        return self._request("PUT", url_suffix, payload, query_params, headers)
    
    def _delete(self, url_suffix: str | None = None, payload: dict | None = None, query_params: dict | None = None, headers: dict | None = None) -> dict | None:
        return self._request("DELETE", url_suffix=url_suffix, payload=payload, query_params=query_params, headers=headers)