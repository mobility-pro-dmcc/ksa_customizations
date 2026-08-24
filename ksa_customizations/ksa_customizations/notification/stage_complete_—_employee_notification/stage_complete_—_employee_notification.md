<p>Dear {{ doc.employee_name }}</p>

<p>Your {{ doc.appraisal_cycle }} appraisal has progressed to the next stage.</p>

<p>Current status:<br>
Stage completed: {{ doc.workflow_state }}<br>
Cycle closes: {{ frappe.utils.formatdate(doc.end_date) }}</p>

<p>You will receive your final score once the cycle is closed and COO sign-off is complete. Any questions in the meantime — speak with your direct manager.</p>

<p>View appraisal status: {{ frappe.utils.get_url_to_form('Appraisal', doc.name) }}</p>

<hr>

<p>── النسخة العربية ──</p>

<p>عزيزي {{ doc.employee_name }}،</p>

<p>نُعلمك بأن تقييمك للربع {{ doc.appraisal_cycle }} انتقل إلى المرحلة التالية ضمن سلسلة الموافقات.</p>

<p>حالة تقييمك الحالية:<br>
المرحلة المكتملة: {{ doc.workflow_state }}<br>
تاريخ إغلاق الدورة: {{ frappe.utils.formatdate(doc.end_date) }}</p>

<p>ستتلقى درجتك النهائية فور إغلاق الدورة واكتمال موافقة المدير التنفيذي. لأي استفسار خلال هذه الفترة، لا تتردد في التواصل مع مديرك المباشر.</p>

<p>متابعة حالة تقييمك: {{ frappe.utils.get_url_to_form('Appraisal', doc.name) }}</p>
