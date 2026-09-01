/**
 * Helper utility to sync document state with Zoho Recruit
 */
const syncWithZoho = (frm, operation) => {
    const isUpdate = operation === "update";
    
    frappe.call({
        method: "ict_zoho_recruit.api.ZohoRecruit.sync_zoho_recruit",
        args: {
            document_ids: [frm.doc.name],
            operation: operation
        },
        freeze: true,
        freeze_message: __(isUpdate ? "Updating with Zoho Recruit..." : "Creating with Zoho Recruit...")
    }).then(({ message }) => {
        if (!message?.success) {
            throw new Error("Sync failed");
        }

        const result = message.results?.[0];

        if (result?.status === "success") {
            frappe.show_alert({
                message: __(`Successfully ${isUpdate ? "updated" : "created"} with Zoho Recruit`),
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
};

const update_address = async (frm) => {
    if (!frm.doc.department_name) {
        reset_address_value(frm);
        return;
    }

    try {
        const r = await frappe.call({
            method: "ict_zoho_recruit.api.Address.get_warehouse_address",
            args: { department_name: frm.doc.department_name }
        });

        const data = r?.message;
        if (data) {
            await frm.set_value({
                address: data.address || "",
                city: data.city || "",
                state: data.state || "",
                country: data.country || "",
                postal_code: data.postal_code || ""
            });
        }
    } catch (error) {
        console.error("Failed to fetch warehouse address:", error);
    }
};

const update_skills = async (frm) => {
    if (!frm.doc.role_profile) {
        frm.clear_table("skills");
        frm.refresh_field("skills");
        return;
    }

    try {
        const response = await frappe.xcall(
            "ict_zoho_recruit.api.RoleProfile.get_role_profile_details",
            { role_profile: frm.doc.role_profile}
        );

        if (response) {
            // frm.clear_table("skills");
            
            // if (Array.isArray(response.skills)) {
            //     response.skills.forEach(skillName => {
            //         if (skillName) {
            //             frm.add_child("skills", { skill: skillName });
            //         }
            //     });
            // }
            // frm.refresh_field("skills");

            await frm.set_value({
                "job_description": response.description || "",
                "requirements": response.custom_requirements || "",
                "benefits": response.custom_benefits || "",
                "title": response.designation || "",
            });
        }
    } catch (error) {
        console.error("Failed to fetch role profile details:", error);
    }
};

const reset_address_value = (frm) => {
    frm.set_value({
        address: "",
        city: "",
        state: "",
        country: "",
        postal_code: ""
    });
};

frappe.ui.form.on("Zoho Job Openings", {
    refresh(frm) {
        if (frm.doc.is_complete) {
            frm.add_custom_button(__("Update To Zoho Recruit"), () => syncWithZoho(frm, "update"));
        } else {
            frm.add_custom_button(__("Create Zoho Recruit"), () => syncWithZoho(frm, "create"));
        }
    },

    role_profile: update_skills,
    department_name: update_address,
    remote_job: reset_address_value
});