<p>Dear {{ doc.employee_name }}</p>

<p>Your {{ doc.appraisal_cycle }} self-assessment was successfully submitted on {{ frappe.utils.formatdate(doc.modified) }} at {{ frappe.utils.format_time(doc.modified) }}.</p>

<p>You Direct Manager has been notified and will complete their review by {{ frappe.utils.formatdate(doc.end_date) }}.</p>

<p>Your submitted score:<br>
{{ doc.goal_name }} → Self-Score: {{ doc.progress }}%<br>
<p>Note: This is your self-assessed score only. Your final score is confirmed after the full review chain is complete. You will be notified when the cycle closes.</p>

<p>View your submission: {{ frappe.utils.get_url_to_form('Goal', doc.name) }}</p>

<hr>

<p>── النسخة العربية ──</p>

<p>عزيزي {{ doc.employee_name }}،</p>

<p>تم استلام تقييمك الذاتي للربع {{ doc.appraisal_cycle }} بنجاح، وذلك بتاريخ {{ frappe.utils.formatdate(doc.modified) }} الساعة {{ frappe.utils.format_time(doc.modified) }}.</p>

<p>تم إخطار مديرك المباشر وسيُنهي مراجعته بحلول {{ frappe.utils.formatdate(doc.end_date) }}.</p>

<p>ملخص درجاتك المُرسَلة:<br>
    {{ doc.goal_name }} ← تقييمك الذاتي: {{ doc.progress }}%<br>

<p>تجدر الإشارة إلى أن هذه الدرجة تعكس تقييمك الذاتي فحسب. ستُحدَّد درجتك النهائية بعد اكتمال سلسلة المراجعة، وستُخطَر بها فور إغلاق الدورة.</p>

<p>عرض إرسالك: {{ frappe.utils.get_url_to_form('Goal', doc.name) }}</p>
