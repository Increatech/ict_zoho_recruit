const update_address = async (frm) => {
    frappe.call({
        method: "ict_zoho_recruit.api.Address.get_warehouse_address",
        args: {
            department_name: frm.doc.department_name
        },
        callback: async function(r) {
            if (r.message) {
                await frm.set_value("address", r.message.address);
                await frm.set_value("city", r.message.city);
                await frm.set_value("state", r.message.state);
                await frm.set_value("country", r.message.country);
                await frm.set_value("postal_code", r.message.postal_code);
            }
        }
    });
};


const update_skills = (frm) => {
    if (!frm.doc.title) {
        frm.clear_table("skils");
        frm.refresh_field("skils");
        return;
    }

    frappe.call({
        method: "ict_zoho_recruit.api.ZohoRecruit.get_designation_skills",
        args: {
            designation: frm.doc.title,
            list_format: true
        },
        callback(r) {
            if (r.exc || r.session_expired) {
                frappe.msgprint({
                    title: __("Error"),
                    message: __("Unable to fetch designation skills."),
                    indicator: "red"
                });
                return;
            }

            const skills = r.message || [];

            frm.clear_table("skils");

            skills.forEach(row => {
                const skill = row?.[0];

                if (!skill) {
                    return;
                }

                frm.add_child("skils", {
                    skill: skill
                });
            });

            frm.refresh_field("skils");
        }
    });
};


frappe.ui.form.on("Zoho Job Openings", {
    refresh(frm) {
        frm.set_df_property("job_description", "read_only", 0);
        frm.set_df_property("requirements", "read_only", 0);
        frm.set_df_property("benefits", "read_only", 0);

        if (frm.doc.is_complete) {
            frm.add_custom_button(__("Update To Zoho Recruit"), () => {
                frappe.call({
                    method: "ict_zoho_recruit.api.ZohoRecruit.sync_zoho_recruit",
                    args: {
                        document_ids: [frm.doc.name],
                        operation: "update"
                    },
                    freeze: true,
                    freeze_message: __("updating with Zoho Recruit...")
                }).then(({ message }) => {
                    if (!message?.success) {
                        throw new Error("Sync failed");
                    }

                    const result = message.results?.[0];

                    if (result?.status === "success") {
                        frappe.show_alert({
                            message: __("Successfully updated with Zoho Recruit"),
                            indicator: "green"
                        });

                        frm.reload_doc();
                    } else if (result?.status === "skipped") {
                        frappe.show_alert({
                            message: __("This job opening is already synced"),
                            indicator: "orange"
                        });
                    } else {
                        throw new Error(result?.error || "Sync failed");
                    }
                }).catch(error => {
                    console.error("Zoho Recruit Sync Error:", error);

                    frappe.msgprint({
                        title: __("Zoho Recruit Sync"),
                        message: __("Failed to sync this job opening."),
                        indicator: "red"
                    });
                });
            });
        } else {
            frm.add_custom_button(__("Create Zoho Recruit"), () => {
                frappe.call({
                    method: "ict_zoho_recruit.api.ZohoRecruit.sync_zoho_recruit",
                    args: {
                        document_ids: [frm.doc.name],
                        operation: "create"
                    },
                    freeze: true,
                    freeze_message: __("creating with Zoho Recruit...")
                }).then(({ message }) => {
                    if (!message?.success) {
                        throw new Error("Sync failed");
                    }

                    const result = message.results?.[0];

                    if (result?.status === "success") {
                        frappe.show_alert({
                            message: __("Successfully created with Zoho Recruit"),
                            indicator: "green"
                        });

                        frm.reload_doc();
                    } else if (result?.status === "skipped") {
                        frappe.show_alert({
                            message: __("This job opening is already synced"),
                            indicator: "orange"
                        });
                    } else {
                        throw new Error(result?.error || "Sync failed");
                    }
                }).catch(error => {
                    console.error("Zoho Recruit Sync Error:", error);

                    frappe.msgprint({
                        title: __("Zoho Recruit Sync"),
                        message: __("Failed to sync this job opening."),
                        indicator: "red"
                    });
                });
            });
        }
    },

    title(frm) {
        if (!frm.doc.title) {
            frm.set_value("benefits", "");
            frm.set_value("job_description", "");
            frm.set_value("requirements", "");
            // frm.set_value("salary", "");
            // frm.set_value("work_experience", "");
            return;
        }

        update_skills(frm)

        frappe.db.get_value(
            "Designation",
            frm.doc.title,
            [
                "custom_benefits",
                "description",
                "custom_requirements",
                // "custom_salary",
                // "custom_work_experience"
            ]
        ).then(r => {
            const data = r.message || {};

            frm.set_value("benefits", data.custom_benefits || "");
            frm.set_value("job_description", data.description || "");
            frm.set_value("requirements", data.custom_requirements || "");
            // frm.set_value("salary", data.custom_salary || "");
            // frm.set_value("work_experience", data.custom_work_experience || "");
        });
    },

    department_name: update_address
});
