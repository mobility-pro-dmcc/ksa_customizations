<p>Dear {{ doc.employee_name }}</p>

<p>Your {{ doc.appraisal_cycle }} self-assessment was successfully submitted on {{ frappe.utils.formatdate(doc.modified) }} at {{ frappe.utils.format_time(doc.modified) }}.</p>

<p>Your direct manager has been notified and will complete their review by {{ frappe.utils.formatdate(doc.end_date) }}.</p>

<p>Your submitted scores:<br>

{% for row in doc.appraisal_kra %}
    {{ row.idx }}) {{ row.kra }} ({{ row.per_weightage }}%)<br>
    <ul>
        {% for kpi in frappe.db.get_list("Goal", {"kra": row.kra, "appraisal_cycle": doc.appraisal_cycle, "employee": doc.employee, "is_group":["!=", 1]}, ["goal_name", "kra", "progress"]) %}
            <li>{{ kpi.goal_name }}: {{ kpi.progress }}%</li>
        {% endfor %}
    </ul>
{% endfor %}
Weighted Self-Score: {{ "{:.2f}".format(doc.total_score * 20) }}%</p>

<p>Note: This is your self-assessed score only. Your final score is confirmed after the full review chain is complete. You will be notified when the cycle closes.</p>

<p>View your submission: {{ frappe.utils.get_url_to_form('Appraisal', doc.name) }}</p>

<hr>

<p>── النسخة العربية ──</p>

<p>عزيزي {{ doc.employee_name }}،</p>

<p>تم استلام تقييمك الذاتي للربع {{ doc.appraisal_cycle }} بنجاح، وذلك بتاريخ {{ frappe.utils.formatdate(doc.modified) }} الساعة {{ frappe.utils.format_time(doc.modified) }}.</p>

<p>تم إخطار مديرك المباشر وسيُنهي مراجعته بحلول {{ frappe.utils.formatdate(doc.end_date) }}.</p>

<p>ملخص درجاتك المُرسَلة:<br>
{% for row in doc.appraisal_kra %}
    {{ row.idx }}) {{ row.kra }} ({{ row.per_weightage }}%)<br>
    <ul>
        {% for kpi in frappe.db.get_list("Goal", {"kra": row.kra, "appraisal_cycle": doc.appraisal_cycle, "employee": doc.employee, "is_group":["!=", 1]}, ["goal_name", "kra", "progress"]) %}
            <li>{{ kpi.goal_name }}: {{ kpi.progress }}%</li>
        {% endfor %}
    </ul>
{% endfor %}
الدرجة الإجمالية المرجّحة (تقييم ذاتي): {{  "{:.2f}".format(doc.total_score * 20) }}%</p>

<p>تجدر الإشارة إلى أن هذه الدرجة تعكس تقييمك الذاتي فحسب. ستُحدَّد درجتك النهائية بعد اكتمال سلسلة المراجعة، وستُخطَر بها فور إغلاق الدورة.</p>

<p>عرض إرسالك: {{ frappe.utils.get_url_to_form('Appraisal', doc.name) }}</p>
