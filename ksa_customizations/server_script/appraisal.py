import frappe

def fill_appraisal_from_goal_template(doc, method):
    if doc.fill_from_goal_template and not doc.appraisal_kra:
        designation = frappe.get_doc("Designation", doc.designation)
        if not designation.goal_template:
            frappe.throw("Please set Goal Template in Designation: {}".format(doc.designation))
        goal_template = frappe.get_doc("Goal Template", designation.goal_template)
        for kra in goal_template.kra:
            doc.append("appraisal_kra", {
                "kra": kra.kra,
                "per_weightage": kra.weight
            })

def create_goals(doc, method):
    designation = frappe.get_doc("Designation", doc.designation)
    if not designation.goal_template:
        frappe.throw("Please set Goal Template in Designation: {}".format(doc.designation))
    goal_template = frappe.get_doc("Goal Template", designation.goal_template)
    kra_weightage_map = {kra.kra: kra.weight for kra in goal_template.kra}
    for row in goal_template.goals:
        # 1. Check if the Parent KRA Group Goal already exists
        parent_goal_name = frappe.db.get_value("Goal", {
            "employee": doc.employee,
            "appraisal_cycle": doc.appraisal_cycle,
            "kra": row.kra_group,  # Group field from your child table
            "is_group": 1
        }, "name")

        # If parent group doesn't exist, create it
        if not parent_goal_name:
            parent_title = f"{row.kra_group} ({doc.appraisal_cycle})"
            
            parent_goal = frappe.get_doc({
                "doctype": "Goal",
                "goal_name": parent_title,
                "employee": doc.employee,
                "kra": row.kra_group,
                "appraisal_cycle": doc.appraisal_cycle,
                "is_group": 1,  # Critical: Mark as group container
                "start_date": doc.start_date,
                "end_date": doc.end_date,
            })
            parent_goal.insert(ignore_permissions=True)
            parent_goal_name = parent_goal.name

        # 2. Check if the specific Child Goal already exists under this parent
        child_exists = frappe.db.exists("Goal", {
            "employee": doc.employee,
            "appraisal_cycle": doc.appraisal_cycle,
            "goal_name": row.goal,  # Actual specific goal name from the row
            "parent_goal": parent_goal_name,
            "is_group": 0
        })

        # If the child leaf node doesn't exist, create it linked to the parent
        if not child_exists:
            child_goal = frappe.get_doc({
                "doctype": "Goal",
                "goal_name": row.goal,
                "employee": doc.employee,
                "kra": row.kra_group,
                "appraisal_cycle": doc.appraisal_cycle,
                "parent_goal": parent_goal_name,  # Link to the group goal above
                "is_group": 0,  # Leaf node
                "start_date": doc.start_date,
                "end_date": doc.end_date,
            })
            child_goal.insert(ignore_permissions=True)