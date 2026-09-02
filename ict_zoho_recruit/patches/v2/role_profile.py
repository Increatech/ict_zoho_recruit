import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Role Profile": [
            dict(
                fieldname="designation_details",
                fieldtype="Section Break",
                label="Designation Details",
                insert_after="custom_warehouse",
            ),
            dict(
                fieldname="posting_title",
                fieldtype="Data",
                label="Job Posting Title",
                insert_after="designation_details",
            ),
            
            dict(
                fieldname="designation",
                fieldtype="Link",
                options="Designation",
                label="Designation",
                insert_after="posting_title",
            ),
            dict(
                fieldname="job_category",
                fieldtype="Select",
                options="\n".join(
                                    [
                                        
                                        "IT",
                                        "Admin",
                                        "Sales",
                                        "Design",
                                        "HR",
                                    ]
                                ),
                label="Job Category",
                insert_after="designation",
            ),
            
            dict(
                fieldname="custom_industry_type",
                fieldtype="Link",
                options="Industry Type",
                label="Industry Type",
                insert_after="job_category",
            ),
            dict(
                fieldname="custom_salary",
                fieldtype="Currency",
                label="Salary",
                insert_after="custom_industry_type",
            ),
            dict(
                fieldname="custom_work_experience",
                fieldtype="Select",
                label="Work Experience",
                options="\n".join(
                    [
                        "Fresher",
                        "0-1 Year",
                        "1-3 Year",
                        "4-5 Year",
                        "5+ Year",
                    ]
                ),
                insert_after="custom_salary",
            ),
            dict(
                fieldname="custom_column_break_rgjzc",
                fieldtype="Column Break",
                insert_after="custom_work_experience",
            ),
            dict(
                fieldname="skills",
                fieldtype="Table",
                label="Skills",
                options="Designation Skill",
                insert_after="custom_column_break_rgjzc",
            ),
            dict(
                fieldname="details_section",
                fieldtype="Section Break",
                insert_after="skills",
            ),
            dict(
                fieldname="description",
                fieldtype="Text Editor",
                label="Description",
                insert_after="details_section",
            ),
            dict(
                fieldname="custom_requirements",
                fieldtype="Text Editor",
                label="Requirements",
                insert_after="description",
            ),
            dict(
                fieldname="custom_benefits",
                fieldtype="Text Editor",
                label="Benefits",
                insert_after="custom_requirements",
            ),
        ]
    }

    create_custom_fields(custom_fields)
