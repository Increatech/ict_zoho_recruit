const set_custom_btns = (frm) => {
    frm.add_custom_button("Create Zoho Job Opening", async () => {
        try {
            const profileDetails = await frappe.xcall(
                "ict_zoho_recruit.api.RoleProfile.get_role_profile_details",
                {
                    role_profile: frm.doc.name
                }
            ) || {};

            const default_benefits = await frappe.db.get_single_value("Zoho Recruit Settings","default_job_post_benefits");
            const target_date_days = await frappe.db.get_single_value("Zoho Recruit Settings","default_target_date_range");

            const target_date = frappe.datetime.add_days(
                frappe.datetime.get_today(),
                target_date_days || 15
            );


            frappe.new_doc("Zoho Job Openings", {
                role_profile: frm.doc.name,
                posting_title: frm.doc.designation || profileDetails.designation || "",
                department_name: frm.doc.custom_department || "",
                number_of_positions: 1,
                date_opened: frappe.datetime.get_today(),
                target_date: target_date,
                job_type: frm.doc.custom_employment_type || "",
                industry: frm.doc.custom_industry_type || "",
                salary: frm.doc.custom_salary || 0,
                work_experience: frm.doc.custom_work_experience || "",
                job_opening_status: "In-progress",
                benefits: frm.doc.custom_benefits || default_benefits || "",
                job_description: frm.doc.description || profileDetails.description || "",
                requirements: frm.doc.custom_requirements || profileDetails.custom_requirements || "",
                title: profileDetails.designation || "",
                job_category: frm.doc.job_category || "",
                posting_title: frm.doc.posting_title || "",
                job_type: "Full-time",
                target_date: target_date,
                skills: (frm.doc.skills || []).map(row => ({
                        skill: row.skill
                    }))
            });

            frappe.show_alert({
                message: __("Zoho Job Opening created. Please review and save."),
                indicator: "green"
            }, 5);

        } catch (error) {
            console.error(
                "Failed to create Zoho Job Opening:",
                error
            );

            frappe.msgprint({
                title: __("Error"),
                indicator: "red",
                message: __(
                    "An unexpected error occurred. Check console for details."
                )
            });
        }
    });
};


frappe.ui.form.on("Role Profile", {
    refresh(frm) {
        set_custom_btns(frm);
    }
});
