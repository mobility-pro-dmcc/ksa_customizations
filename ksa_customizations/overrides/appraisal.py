import frappe
from hrms.hr.doctype.appraisal.appraisal import Appraisal
from frappe.query_builder.functions import Count, Sum
from frappe.utils import flt


class CustomAppraisal(Appraisal):
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