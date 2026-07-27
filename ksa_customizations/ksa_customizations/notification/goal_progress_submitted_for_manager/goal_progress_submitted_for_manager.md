<p>Dear</p>

<p>{{ doc.employee_name }} submitted their {{ doc.appraisal_cycle }} self-assessment on {{ frappe.utils.formatdate(doc.modified) }} at {{ frappe.utils.format_time(doc.modified) }}.</p>

<p>Your deadline to review all team submissions is {{ frappe.utils.formatdate(doc.end_date) }} 23:59. This is fixed — it does not change based on when each person submits.</p>

<p>Their submitted scores:<br>
{% for row in doc.appraisal_kra %}
    {{ row.idx }}) {{ row.kra }} ({{ row.per_weightage }}%)<br>
    <ul>
        {% for kpi in frappe.db.get_list("Goal", {"kra": row.kra, "appraisal_cycle": doc.appraisal_cycle, "employee": doc.employee, "is_group":["!=", 1]}, ["goal_name", "kra", "progress"]) %}
            <li>{{ kpi.goal_name }}: {{ kpi.progress }}%</li>
        {% endfor %}
    </ul>
{% endfor %}
Weighted Self-Score: {{ "{:.2f}".format(doc.total_score * 20) }}%</p>

<p>What you need to do:<br>
1. Open their appraisal: {{ frappe.utils.get_url_to_form('Appraisal', doc.name) }}<br>
2. Review each score against actual results<br>
3. Approve, or enter your own score with a written reason<br>
4. Submit — next stage triggers automatically</p>

<p>Anyone who has not submitted by {{ frappe.utils.formatdate(doc.end_date) }} will be escalated to you and HR — you can enter their scores directly.</p>

<hr>

<p>عزيزي،</p>

<p>أرسل {{ doc.employee_name }} تقييمه الذاتي للربع {{ doc.appraisal_cycle }} بتاريخ {{ frappe.utils.formatdate(doc.modified) }} الساعة {{ frappe.utils.format_time(doc.modified) }}.</p>

<p>موعدك النهائي لمراجعة جميع إرسالات فريقك هو {{ frappe.utils.formatdate(doc.end_date) }} الساعة 23:59. هذا الموعد ثابت ولا يتغير بحسب توقيت إرسال كل موظف.</p>

<p>درجاته المُرسَلة:<br>
{% for row in doc.appraisal_kra %}
    {{ row.idx }}) {{ row.kra }} ({{ row.per_weightage }}%)<br>
    <ul>
        {% for kpi in frappe.db.get_list("Goal", {"kra": row.kra, "appraisal_cycle": doc.appraisal_cycle, "employee": doc.employee, "is_group":["!=", 1]}, ["goal_name", "kra", "progress"]) %}
            <li>{{ kpi.goal_name }}: {{ kpi.progress }}%</li>
        {% endfor %}
    </ul>
{% endfor %}
الدرجة الإجمالية المرجّحة (تقييم ذاتي): {{ "{:.2f}".format(doc.total_score * 20) }}%</p>

<p>خطوات المراجعة:<br>
١. افتح ملف التقييم: {{ frappe.utils.get_url_to_form('Appraisal', doc.name) }}<br>
٢. راجع كل درجة في مقابل النتائج الفعلية التي لديك<br>
٣. وافق على الدرجة أو عدّلها مع إضافة مبرر مكتوب<br>
٤. أرسل — ستنتقل الدورة تلقائياً إلى المرحلة التالية</p>

<p>أي موظف لم يُرسل بحلول موعده النهائي سيُصعَّد تلقائياً إليك وإلى الموارد البشرية، وبإمكانك عندها إدخال درجاته مباشرة.</p>
