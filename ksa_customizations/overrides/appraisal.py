import frappe
from hrms.hr.doctype.appraisal.appraisal import Appraisal
from frappe import _
from frappe.query_builder.functions import Count, Sum
from frappe.utils import flt


class CustomAppraisal(Appraisal):
    def validate(self):
        self.fill_appraisal_from_goal_template()
        super().validate()

    def after_insert(self):
        self.create_goals()

    def get_goal_template(self):
        """Fetches the goal template from the Employee, falling back to the Designation."""
        template = frappe.db.get_value("Employee", self.employee, "goal_template")
        if not template:
            template = frappe.db.get_value("Designation", self.designation, "goal_template")
            if not template:
                frappe.throw(_("Please set Goal Template in Designation: {0}").format(self.designation))
        return frappe.get_doc("Goal Template", template)

    def fill_appraisal_from_goal_template(self):
        if self.fill_from_goal_template and not self.appraisal_kra:
            self.set_kras_from_goal_template()

    def set_kras_from_goal_template(self):
        goal_template = self.get_goal_template()
        self.set("appraisal_kra", [])
        for kra in goal_template.kra:
            self.append("appraisal_kra", {
                "kra": kra.kra,
                "per_weightage": kra.weight
            })

    def create_goals(self):
        goal_template = self.get_goal_template()
        for row in goal_template.goals:
            # 1. Check if the Parent KRA Group Goal already exists
            parent_goal_name = frappe.db.get_value("Goal", {
                "employee": self.employee,
                "appraisal_cycle": self.appraisal_cycle,
                "kra": row.kra_group,  # Group field from your child table
                "is_group": 1
            }, "name")

            # If parent group doesn't exist, create it
            if not parent_goal_name:
                parent_title = f"{row.kra_group} ({self.appraisal_cycle})"

                parent_goal = frappe.get_doc({
                    "doctype": "Goal",
                    "goal_name": parent_title,
                    "employee": self.employee,
                    "kra": row.kra_group,
                    "appraisal_cycle": self.appraisal_cycle,
                    "goal_name_ar": row.kra_name_ar,
                    "is_group": 1,  # Critical: Mark as group container
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                })
                parent_goal.insert(ignore_permissions=True)
                parent_goal_name = parent_goal.name

            # 2. Check if the specific Child Goal already exists under this parent
            child_exists = frappe.db.exists("Goal", {
                "employee": self.employee,
                "appraisal_cycle": self.appraisal_cycle,
                "goal_name": row.goal,  # Actual specific goal name from the row
                "parent_goal": parent_goal_name,
                "is_group": 0
            })

            # If the child leaf node doesn't exist, create it linked to the parent
            if not child_exists:
                child_goal = frappe.get_doc({
                    "doctype": "Goal",
                    "goal_name": row.goal,
                    "employee": self.employee,
                    "kra": row.kra_group,
                    "appraisal_cycle": self.appraisal_cycle,
                    "goal_name_ar": row.goal_name_ar,
                    "expected_target_amount": row.target,
                    "parent_goal": parent_goal_name,  # Link to the group goal above
                    "is_group": 0,  # Leaf node
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                })
                child_goal.insert(ignore_permissions=True)

    @frappe.whitelist()
    def reset_goals_and_kras(self):
        """Deletes the employee's goals for this cycle and rebuilds KRAs and goals from the goal template."""
        if "HR Manager" not in frappe.get_roles():
            frappe.throw(_("Only HR Manager can reset goals and KRAs"), frappe.PermissionError)
        if self.docstatus != 0:
            frappe.throw(_("Goals and KRAs can only be reset for a draft Appraisal"))

        # Validate the template exists before deleting anything
        self.get_goal_template()

        # Delete deepest nodes first so groups have no children when removed
        goals = frappe.get_all(
            "Goal",
            filters={"employee": self.employee, "appraisal_cycle": self.appraisal_cycle},
            pluck="name",
            order_by="lft desc",
        )
        for goal in goals:
            frappe.delete_doc("Goal", goal, ignore_permissions=True, force=True)

        # Goal deletion updates this appraisal in the DB, so reload before editing
        self.reload()
        self.set_kras_from_goal_template()
        self.save()
        self.create_goals()

        # Recompute scores against the newly created goals
        self.set_goal_score(update=True)
        return self

    def set_goal_score_with_goal_template(self, update=False):
        # Initialize DocTypes outside the loop for better performance
        Goal = frappe.qb.DocType("Goal")
        GoalTemplateKRA = frappe.qb.DocType("Goal Template KRA")
        GoalTemplateDetail = frappe.qb.DocType("Goal Template Detail")
        GoalTemplate = frappe.qb.DocType("Goal Template")

        for kra in self.appraisal_kra:
            # 1. Subquery to find parent goal names
            parent_goal_names = (
                frappe.qb.from_(Goal)
                .select(Goal.name)
                .where(
                    Goal.goal_name.like(f"%{kra.kra}%")
                    & (Goal.appraisal_cycle == self.appraisal_cycle)
                )
            )
            
            # 2. Main query incorporating grouping and your math formula
            query_result = (
                frappe.qb.from_(Goal)
                .left_join(GoalTemplate)
                .on(GoalTemplate.designation == self.designation)
                .left_join(GoalTemplateKRA)
                .on((GoalTemplateKRA.kra == Goal.kra) & (GoalTemplateKRA.parent == GoalTemplate.name))
                .left_join(GoalTemplateDetail)
                .on((GoalTemplateDetail.parent == GoalTemplate.name) & (GoalTemplateDetail.goal == Goal.goal_name))
                .select(
                    Count(Goal.name).as_("total_goals"),
                    Sum(Goal.progress * GoalTemplateDetail.weight * GoalTemplateKRA.weight / 10000).as_("total_weighted_progress"),
                    Sum(Goal.progress * GoalTemplateDetail.weight/ 100).as_("total_goal_waighted_progress")
                )
                .where(
                    (Goal.kra == kra.kra)
                    & (Goal.employee == self.employee)
                    & (Goal.status != "Archived")
                    & (Goal.parent_goal.isin(parent_goal_names))
                    & (Goal.appraisal_cycle == self.appraisal_cycle)
                )
                .groupby(Goal.kra)
            ).run(as_dict=True)
            print(query_result)
            if query_result:
                total_goal_completion = query_result[0].get("total_goal_waighted_progress") or 0
                total_weighted_progress = query_result[0].get("total_weighted_progress") or 0

            else:
                total_goal_completion = 0
                total_weighted_progress = 0

            # 4. Update KRA values
            kra.goal_completion = flt(total_goal_completion, kra.precision("goal_completion"))
            kra.goal_score = flt(total_weighted_progress, kra.precision("goal_score"))

            if update:
                kra.db_update()

        self.calculate_total_score()

        if update:
            self.calculate_final_score()
            self.db_update()

        return self

    def set_goal_score(self, update=False):
        if self.fill_from_goal_template:
            self.set_goal_score_with_goal_template(update=update)
        else:
            super().set_goal_score(update=update)