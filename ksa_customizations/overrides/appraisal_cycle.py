import frappe
from frappe import _
from hrms.hr.doctype.appraisal_cycle.appraisal_cycle import AppraisalCycle

class CustomAppraisalCycle(AppraisalCycle):
    def get_employee_templates(self, employees):
        """
        Creates a dictionary mapping Employee names to their templates.
        Goal Template: Checks Employee first, falls back to Designation.
        Appraisal Template: Checks Designation only.
        """
        if not employees:
            return {}
            
        employee_names = [employee.name for employee in employees]

        employee_records = frappe.get_all(
            "Employee",
            filters={"name": ["in", employee_names]},
            fields=["name", "goal_template", "designation"]
        )

        designation_names = list(set([
            emp.designation for emp in employee_records if emp.designation
        ]))

        designation_data = {}
        if designation_names:
            designations = frappe.get_all(
                "Designation",
                filters={"name": ["in", designation_names]},
                fields=["name", "goal_template", "appraisal_template"] 
            )
            
            designation_data = {
                desig.name: desig for desig in designations
            }

        final_map = {}
        
        for emp in employee_records:
            desig_info = designation_data.get(emp.designation, {})
            
            goal_template = emp.goal_template or desig_info.get("goal_template")
            
            appraisal_template = desig_info.get("appraisal_template")

            final_map[emp.name] = {
                "goal_template": goal_template or None,
                "appraisal_template": appraisal_template or None
            }

        for emp_name in employee_names:
            if emp_name not in final_map:
                final_map[emp_name] = {
                    "goal_template": None,
                    "appraisal_template": None
                }

        return final_map

    @frappe.whitelist()
    def set_employees(self):
        """
        Overridden to append the additional goal_template configuration and
        only trigger a missing template message if BOTH templates are absent.
        """
        employees = self.get_employees_for_appraisal()
        template_maps = self.get_employee_templates(employees)

        if employees:
            self.set("appraisees", [])
            template_missing = False

            for data in employees:
                designation_templates = template_maps.get(data.name, {})
                appraisal_template = designation_templates.get("appraisal_template")
                goal_template = designation_templates.get("goal_template")

                # CHANGED: Mark as missing ONLY if both appraisal_template AND goal_template are empty
                if not appraisal_template and not goal_template:
                    template_missing = True

                self.append(
                    "appraisees",
                    {
                        "employee": data.name,
                        "employee_name": data.employee_name,
                        "branch": data.branch,
                        "designation": data.designation,
                        "department": data.department,
                        "appraisal_template": appraisal_template,
                        "goal_template": goal_template, # Ensure this custom field exists in your Appraisee child table
                    },
                )

            if template_missing:
                self.show_missing_template_message()
        else:
            self.set("appraisees", [])
            frappe.msgprint(_("No employees found for the selected criteria"))

        return self

    @frappe.whitelist()
    def create_appraisals(self):
        """
        Overridden to ensure strict backend check fails only when an appraisee 
        is missing BOTH the appraisal template and the goal template.
        """
        self.check_permission("write")
        if not self.appraisees:
            frappe.throw(
                _("Please select employees to create appraisals for"), title=_("No Employees Selected")
            )

        # CHANGED: Validation now allows progression if either template exists. 
        # It breaks only if an employee completely lacks both fields.
        for appraisee in self.appraisees:
            if not appraisee.appraisal_template and not appraisee.get("goal_template"):
                self.show_missing_template_message(raise_exception=True)

        if len(self.appraisees) > 30:
            frappe.enqueue(
                "hrms.hr.doctype.appraisal_cycle.appraisal_cycle.create_appraisals_for_cycle",
                queue="long",
                timeout=600,
                appraisal_cycle=self,
            )
            frappe.msgprint(
                _("Appraisal creation is queued. It may take a few minutes."),
                alert=True,
                indicator="blue",
            )
        else:
            from hrms.hr.doctype.appraisal_cycle.appraisal_cycle import create_appraisals_for_cycle
            create_appraisals_for_cycle(self, publish_progress=True)
            self.reload()

    def show_missing_template_message(self, raise_exception=False):
        """
        Overridden to adjust the message wording to reflect the new dynamic logic.
        """
        msg = _("Neither Appraisal Template nor Goal Template was found for some designations.")
        msg += "<br><br>"
        msg += _(
            "Please set at least one setup template for all the {0} or map them directly in the Employees table below."
        ).format(f"""<a href='{frappe.utils.get_url_to_list("Designation")}'>Designations</a>""")

        frappe.msgprint(
            msg, title=_("Templates Missing"), indicator="yellow", raise_exception=raise_exception
        )