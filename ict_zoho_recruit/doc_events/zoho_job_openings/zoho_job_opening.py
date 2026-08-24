import frappe
from frappe.utils import cint


def after_save(doc, method=None):
    
    if not cint(doc.is_complete) or cint(doc.is_notified):
        return
    
    publish_mail = frappe.db.get_single_value("Zoho Recruit Settings", "contact_email")
    
    if not publish_mail:
        frappe.throw("Please enter the Zoho Job Publish Person Email.")

    template = frappe.get_cached_doc("Email Template","New Job Opening")
    
    message = frappe.render_template(template.response,{"doc": doc})
    subject = frappe.render_template(template.subject,{"doc": doc})

    frappe.sendmail(
        recipients=[publish_mail],
        subject=subject,
        message=message
    )
    
    doc.is_notified = 1
    doc.save()
    