import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "File": [
            dict(
                fieldname = "custom_uploaded_to_zoho_recruit",
                fieldtype = "Check",
                label = " Uploaded To Zoho Recruit",
                read_only = 1,
                insert_after = "uploaded_to_google_drive"
            ),
            dict(
                fieldname = "custom_zoho_attachment_id",
                fieldtype = "Data",
                label = "Zoho Attachment ID",
                read_only = 1,
                insert_after = "custom_uploaded_to_zoho_recruit"
            ),       
        ]
    }

    create_custom_fields(custom_fields)