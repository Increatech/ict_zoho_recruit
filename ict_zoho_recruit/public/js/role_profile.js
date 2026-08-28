const set_custom_btns = (frm) => {
    frm.add_custom_button("Create Zoho Job Opening", () => {
        const dialog = new frappe.ui.Dialog({
            title: "Create Zoho Job Opening",
            size: "large",
            fields: [
                {
                    label: "Posting Title",
                    fieldname: "posting_title",
                    fieldtype: "Data",
                    reqd: 1,
                },
                {
                    label: "Department Name",
                    fieldname: "department_name",
                    fieldtype: "Link",
                    options: "Department",
                    default: frm.doc.custom_department,
                },
                {
                    label: "Number of Positions",
                    fieldname: "number_of_positions",
                    fieldtype: "Int",
                    default: 1,
                },
                {
                    label: "Salary",
                    fieldname: "salary",
                    fieldtype: "Currency",
                    default: frm.doc.custom_salary,
                },
                {
                    label: "Job Opening Status",
                    fieldname: "job_opening_status",
                    fieldtype: "Select",
                    options: [
                        "In-progress",
                        "Waiting for approval",
                        "On-Hold",
                        "Filled",
                        "Cancelled",
                        "Declined",
                    ].join("\n"),
                    default: "In-progress",
                },
                {
                    fieldtype: "Column Break",
                },
                {
                    label: "Date Opened",
                    fieldname: "date_opened",
                    fieldtype: "Date",
                    default: frappe.datetime.get_today(),
                },
                {
                    label: "Target Date",
                    fieldname: "target_date",
                    fieldtype: "Date",
                },
                {
                    label: "Job Type",
                    fieldname: "job_type",
                    fieldtype: "Link",
                    options: "Employment Type",
                },
                {
                    label: "Industry Type",
                    fieldname: "industry_type",
                    fieldtype: "Link",
                    options: "Industry Type",
                    default: frm.doc.custom_industry_type,
                },
                {
                    label: "Work Experience",
                    fieldname: "work_experience",
                    fieldtype: "Select",
                    options: [
                        "Fresher",
                        "0-1 Year",
                        "1-3 Year",
                        "4-5 Year",
                        "5+ Year",
                    ].join("\n"),
                    default: frm.doc.custom_work_experience,
                },
            ],
            primary_action_label: "Create",
            primary_action: async (values) => {
                try {
                    // 1. Validations
                    if (!values.posting_title?.trim()) {
                        frappe.throw(__("Please enter Posting Title."));
                    }

                    if (values.target_date && values.date_opened && values.target_date < values.date_opened) {
                        frappe.throw(__("Target Date cannot be earlier than Date Opened."));
                    }

                    // 2. Fetch role profile details using cleaner async `frappe.xcall`
                    const profileDetails = await frappe.xcall(
                        "ict_zoho_recruit.api.RoleProfile.get_role_profile_details",
                        { role_profile: frm.doc.name }
                    ) || {};

                    // 3. Fetch single value settings asynchronously
                    const settings = await frappe.db.get_single_value(
                        "Zoho Recruit Settings",
                        "default_job_post_benefits"
                    );

                    // 4. Create new target document
                    frappe.new_doc("Zoho Job Openings", {
                        role_profile: frm.doc.name,
                        posting_title: values.posting_title.trim(),
                        department_name: values.department_name,
                        number_of_positions: values.number_of_positions,
                        date_opened: values.date_opened,
                        target_date: values.target_date,
                        job_type: values.job_type,
                        industry: values.industry_type,
                        salary: values.salary,
                        work_experience: values.work_experience,
                        job_opening_status: values.job_opening_status,
                        benefits: frm.doc.custom_benefits || settings || "",
                        job_description:frm.doc.description || profileDetails.description || "",
                        requirements: frm.doc.custom_requirements|| profileDetails.custom_requirements || "",
                        title: profileDetails.designation || "",

                    });

                    dialog.hide();

                    frappe.show_alert({
                        message: __("Zoho Job Opening details filled. Please review and save."),
                        indicator: "green",
                    }, 5);

                } catch (error) {
                    console.error("Failed to create Zoho Job Opening:", error);
                    frappe.msgprint({
                        title: __("Error"),
                        indicator: "red",
                        message: __("An unexpected error occurred. Check console for details.")
                    });
                }
            },
        });

        dialog.show();
    });
};


frappe.ui.form.on("Role Profile", {
    refresh(frm) {
        set_custom_btns(frm)
    }
});
