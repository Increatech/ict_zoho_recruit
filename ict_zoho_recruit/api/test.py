import frappe
from ..utils.ZohoService import ZoHoRecruitService
from .zoho_recruit import get_designation_skills

@frappe.whitelist(allow_guest=True)
def test(designation):
    
    return get_designation_skills(designation, list_format=True)


from bs4 import BeautifulSoup

def clean_html(html):
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ", strip=True)