import frappe

DOCTYPES = ("Appraisal", "Goal")


def sync_appraisal_permissions():
    # Gives each user Employee permissions on Appraisal and Goal for:
    # their own employee record, and every employee where they are the
    # direct manager (reports_to_email) or functional manager (custom_functional_manager).
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "user_id", "reports_to_email", "custom_functional_manager"],
    )

    created = 0
    for emp in employees:
        users = {emp.user_id, emp.reports_to_email, emp.custom_functional_manager}
        for user in filter(None, users):
            if not frappe.db.exists("User", user):
                continue
            for doctype in DOCTYPES:
                created += add_user_permission(user, emp.name, doctype)

    frappe.db.commit()
    print(f"Created {created} user permissions for {len(employees)} employees")


def add_user_permission(user, employee, doctype):
    already_allowed = frappe.db.exists(
        "User Permission",
        {"user": user, "allow": "Employee", "for_value": employee, "applicable_for": doctype},
    ) or frappe.db.exists(
        "User Permission",
        {"user": user, "allow": "Employee", "for_value": employee, "apply_to_all_doctypes": 1},
    )
    if already_allowed:
        return 0

    frappe.get_doc(
        {
            "doctype": "User Permission",
            "user": user,
            "allow": "Employee",
            "for_value": employee,
            "apply_to_all_doctypes": 0,
            "applicable_for": doctype,
        }
    ).insert(ignore_permissions=True)
    return 1
