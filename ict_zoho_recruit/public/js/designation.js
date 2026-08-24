frappe.ui.form.on("Designation", {
    refresh(frm) {
        frm.add_custom_button("Create Zoho Job Opening", function () {
            const dialog = new frappe.ui.Dialog({
                title: "Create Zoho Job Opening",
                fields: [
                    {
                        label: "Posting Title",
                        fieldname: "posting_title",
                        fieldtype: "Data",
                        default: frm.doc.name,
                        read_only: 1
                    },
                    {
                        label: "Department Name",
                        fieldname: "department_name",
                        fieldtype: "Link",
                        options: "Department"
                    },
                    {
                        label: "Number of Positions",
                        fieldname: "number_of_positions",
                        fieldtype: "Int"
                    },
                    {
                        label: "Salary",
                        fieldname: "salary",
                        fieldtype: "Currency",
                        default: frm.doc.custom_salary
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
                            "Declined"
                        ].join("\n")
                    },
                    {
                        fieldtype: "Column Break"
                    },
                    {
                        label: "Date Opened",
                        fieldname: "date_opened",
                        fieldtype: "Date",
                        default: frappe.datetime.get_today()
                    },
                    {
                        label: "Target Date",
                        fieldname: "target_date",
                        fieldtype: "Date"
                    },
                    {
                        label: "Job Type",
                        fieldname: "job_type",
                        fieldtype: "Link",
                        options: "Employment Type"
                    },
                    {
                        label: "Industry Type",
                        fieldname: "industry_type",
                        fieldtype: "Link",
                        options: "Industry Type",
                        default: frm.doc.custom_industry_type
                    },
                    {
                        label: "Work Experience",
                        fieldname: "work_experience",
                        fieldtype: "Select",
                        default: frm.doc.custom_work_experience,
                        options: [
                            "Fresher",
                            "0-1 Year",
                            "1-3 Year",
                            "4-5 Year",
                            "5+ Year"
                        ].join("\n")
                    }
                ],
                primary_action_label: "Create",
                primary_action(values) {
                    if (!values.posting_title) {
                        frappe.msgprint({
                            title: "Missing Field",
                            message: "Please enter Posting Title.",
                            indicator: "orange"
                        });
                        return;
                    }

                    frappe.new_doc("Zoho Job Openings", {
                        title: values.posting_title,
                        posting_title: values.posting_title,
                        department_name: values.department_name,
                        number_of_positions: values.number_of_positions,
                        date_opened: values.date_opened,
                        target_date: values.target_date,
                        job_type: values.job_type,
                        industry_type: values.industry_type,
                        salary: values.salary,
                        work_experience: values.work_experience,
                        job_opening_status: values.job_opening_status
                    });

                    dialog.hide();

                    frappe.show_alert({
                        message: "Zoho Job Opening details filled. Please review and save.",
                        indicator: "green"
                    });
                }
            });

            dialog.show();
        });
    }
});
