import frappe
from frappe.utils import cint

def delete_attachment(doc, method=None):
    settings = frappe.get_single("Zoho Recruit Settings")
    
    if not cint(settings.attachment_remover):
        return
    
    frappe.enqueue(
        "ict_zoho_recruit.doc_events.file.file.delete_zoho_attachment",
        file_name=doc.name,
        queue="long",
        timeout=300,
    )
    


def delete_zoho_attachment(file_name):
    from ict_zoho_recruit.utils.ZohoService import ZoHoRecruitService
    service = ZoHoRecruitService()
    return service._delete_attachment(file_name)