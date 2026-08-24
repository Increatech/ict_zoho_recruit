import frappe

@frappe.whitelist(allow_guest=True)
def get_warehouse_address(department_name):
    if not department_name:
        return ""

    warehouse_name = frappe.db.get_value("Department", department_name, "custom_warehouse")
    if not warehouse_name:
        return ""

    address_name = frappe.db.get_value(
        "Dynamic Link",
        {
            "link_doctype": "Warehouse",
            "link_name": warehouse_name,
            "parenttype": "Address"
        },
        "parent"
    )

    if not address_name:
        return ""

    address = frappe.db.get_value(
        "Address",
        address_name,
        ["name", "city", "state", "country", "pincode"],
        as_dict=True
    )

    if not address:
        return ""

    return {
        "address": address.name,
        "city": address.get("city"),
        "state": address.get("state"),
        "country": address.get("country"),
        "postal_code": address.get("pincode"),
    }