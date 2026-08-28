import frappe

def is_empty_html(value):
    return not value or value.strip() in (
        '<div class="ql-editor read-mode"><p><br></p></div>',
        '<div class="ql-editor read-mode"><p></p></div>',
    )

@frappe.whitelist(allow_guest=True)
def get_role_profile_details(role_profile):
    description = None
    custom_requirements = None
    designation = None
    custom_benefits = None
    skills = []

    current_role_profile = role_profile

    while current_role_profile:
        role = frappe.db.get_value(
            "Role Profile",
            current_role_profile,
            [
                "description",
                "custom_requirements",
                "custom_benefits",
                "parent_role_profile",
                "designation",
            ],
            as_dict=True,
        )

        if not role:
            break

        if not description and not is_empty_html(role.description):
            description = role.description

        if not custom_requirements and not is_empty_html(role.custom_requirements):
            custom_requirements = role.custom_requirements

        custom_benefits = custom_benefits or role.custom_benefits
        designation = designation or role.designation

        if not skills:
            skills = frappe.get_all(
                "Designation Skill",
                filters={
                    "parent": current_role_profile,
                    "parenttype": "Role Profile",
                    "parentfield": "skills",
                },
                pluck="skill",
                order_by="idx asc",
            )

        if description and custom_requirements and designation and skills:
            break

        current_role_profile = role.parent_role_profile

    return {
        "designation": designation,
        "description": description ,
        "custom_requirements": custom_requirements,
        "custom_benefits":custom_benefits if  custom_benefits else frappe.db.get_single_value("Zoho Recruit Settings","default_job_post_benefits"),
        "skills": skills,
    }
