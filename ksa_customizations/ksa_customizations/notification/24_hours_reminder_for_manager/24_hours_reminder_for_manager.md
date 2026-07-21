<p>Dear</p>

<p>{{ doc.employee }} has not submitted their {{ doc.appraisal_cycle }} self-assessment.</p>

<p>Deadline passed: {{ frappe.utils.formatdate(frappe.db.get_value("Appraisal Cycle", doc.appraisal_cycle, "end_date")) }} 23:59</p>

<p>Required action:<br>
· Direct manager: Contact the employee now. If needed, enter their scores directly. Your overall review deadline remains {{ frappe.utils.formatdate(frappe.db.get_value("Appraisal Cycle", doc.appraisal_cycle, "end_date")) }}.<br>
· HR: Log this escalation. If unresolved before the manager deadline, the employee will be recorded as non-compliant for this cycle.</p>

<hr>

<p>── النسخة العربية ──</p>

<p>عزيزي ,</p>

<p>نُحيطكم علماً بأن {{ doc.employee }} — لم يُرسل تقييمه الذاتي للربع {{ doc.appraisal_cycle }} حتى الآن.</p>

<p>الموعد النهائي الذي انقضى: {{ frappe.utils.formatdate(frappe.db.get_value("Appraisal Cycle", doc.appraisal_cycle, "end_date")) }} الساعة 23:59</p>

<p>الإجراء المطلوب:<br>
· المدير المباشر: تواصل مع الموظف للوقوف على السبب. إذا تعذّر عليه الإرسال، بإمكانك إدخال درجاته مباشرة. موعدك الإجمالي لإنجاز المراجعة لا يزال {{ frappe.utils.formatdate(frappe.db.get_value("Appraisal Cycle", doc.appraisal_cycle, "end_date")) }}.<br>
· الموارد البشرية: يُرجى توثيق هذا التصعيد. إذا لم يُعالَج الأمر قبل الموعد النهائي للمدير، سيُسجَّل الموظف على أنه غير ممتثل لهذه الدورة.</p>
