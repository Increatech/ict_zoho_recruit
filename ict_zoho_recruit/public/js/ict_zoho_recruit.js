frappe.listview_settings["Zoho Job Openings"] = {
    onload(listview) {
        listview.page.add_inner_button("Zoho Recruit Sync", () => {
            const document_ids = listview
                .get_checked_items()
                .map(({ name }) => name);

            if (!document_ids.length) {
                frappe.msgprint({
                    title: __("No Documents Selected"),
                    message: __("Please select at least one document."),
                    indicator: "orange"
                });
                return;
            }

            frappe.call({
                method: "ict_zoho_recruit.api.ZohoRecruit.sync_zoho_recruit",
                args: { document_ids },
                freeze: true,
                freeze_message: __("Syncing selected documents...")
            })
            .then(({ message }) => {
                if (!message?.success) {
                    throw new Error("Sync failed");
                }

                const results = message.results || [];
                const success = results.filter(
                    result => result.status === "success"
                ).length;
                const skipped = results.filter(
                    result => result.status === "skipped"
                ).length;
                const failed = results.filter(
                    result => result.status === "failed"
                ).length;

                frappe.msgprint({
                    title: __("Zoho Recruit Sync"),
                    message: __(
                        "Sync completed.<br><br>" +
                        "Success: {0}<br>" +
                        "Skipped: {1}<br>" +
                        "Failed: {2}"
                    ).format(success, skipped, failed),
                    indicator: failed ? "orange" : "green"
                });

                listview.refresh();
            })
            .catch(error => {
                console.error("Zoho Recruit Sync Error:", error);

                frappe.msgprint({
                    title: __("Zoho Recruit Sync"),
                    message: __("Failed to sync selected documents."),
                    indicator: "red"
                });
            });
        });
    }
};
