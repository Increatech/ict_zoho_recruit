import frappe
from frappe.utils import cint


def send_email(doc_id):
    settings = frappe.get_single("Zoho Recruit Settings")
    
    if not cint(settings.enable_notify_email) or not settings.contact_email:
        frappe.log_error(
                    title="Zoho Job Opening Email Notify",
                    message=(
                        f"Zoho Job Openig {doc_id} failed because Zoho Recruit Settings not configured "
                    ),
                )
        
    zoho_opening_doc = frappe.get_doc("Zoho Job Openings", doc_id)
    
    if not cint(zoho_opening_doc.is_complete) or cint(zoho_opening_doc.is_notified):
        return
    
    publish_mail = frappe.db.get_single_value("Zoho Recruit Settings", "contact_email")
    
    if not publish_mail:
        frappe.throw("Please enter the Zoho Job Publish Person Email.")

    template = frappe.get_cached_doc("Email Template","New Job Opening")
    
    message = frappe.render_template(template.response,{"doc": zoho_opening_doc})
    subject = frappe.render_template(template.subject,{"doc": zoho_opening_doc})

    frappe.sendmail(
        recipients=[publish_mail],
        subject=subject,
        message=message
    )
    
    zoho_opening_doc.is_notified = 1
    zoho_opening_doc.save(ignore_permissions=True)
    