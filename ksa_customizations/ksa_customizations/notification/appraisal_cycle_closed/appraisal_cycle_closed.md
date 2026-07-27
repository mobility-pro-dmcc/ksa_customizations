<p>Dear {{ doc.employee }}</p>

<p>The {{ doc.appraisal_cycle }} performance appraisal cycle is now closed. All scores have been reviewed and signed off.</p>

<p>Your final results:<br>
{% for row in doc.appraisal_kra %}
    {{ row.idx }}) {{ row.kra }} ({{ row.per_weightage }}%)<br>
    <ul>
        {% for kpi in frappe.db.get_list("Goal", {"kra": row.kra, "appraisal_cycle": doc.appraisal_cycle, "employee": doc.employee, "is_group":["!=", 1]}, ["goal_name", "kra", "progress"]) %}
            <li>{{ kpi.goal_name }}: {{ kpi.progress }}%</li>
        {% endfor %}
    </ul>
{% endfor %}
Final Weighted Score: {{ "{:.2f}".format(doc.total_score * 20) }}%<br>
</p>

<p>Your quarterly incentive payout will be processed by Finance and reflected in your next salary. You will receive a separate payment confirmation from Finance once processed.</p>

<p>Any questions about your final score — you have 5 working days from today to raise them with your manager or HR.</p>

<p>Thank you for your effort and commitment this quarter.</p>

<p>Hashim Abdul Rahaman Khalil<br>
HR Manager — Arabian Tires Group</p>

<hr>

<p>── النسخة العربية ──</p>

<p>عزيزي {{ doc.employee }}،</p>

<p>أُغلقت دورة تقييم الأداء للربع {{ doc.appraisal_cycle }} رسمياً، وقد اكتملت مراجعة جميع التقييمات والموافقة عليها.</p>

<p>نتائجك النهائية:<br>
{{% for row in doc.appraisal_kra %}
    {{ row.idx }}) {{ row.kra }} ({{ row.per_weightage }}%)<br>
    <ul>
        {% for kpi in frappe.db.get_list("Goal", {"kra": row.kra, "appraisal_cycle": doc.appraisal_cycle, "employee": doc.employee, "is_group":["!=", 1]}, ["goal_name", "kra", "progress"]) %}
            <li>{{ kpi.goal_name }}: {{ kpi.progress }}%</li>
        {% endfor %}
    </ul>
{% endfor %}
الدرجة الإجمالية المرجّحة النهائية: {{ "{:.2f}".format(doc.total_score * 20) }}%<br>
</p>

<p>ستتولى إدارة المالية معالجة مكافأة الأداء الفصلية وستظهر في راتبك القادم. ستتلقى تأكيداً منفصلاً من المالية بمجرد اكتمال الصرف.</p>

<p>أمامك ٥ أيام عمل من تاريخ هذا الإشعار لرفع أي تساؤل حول درجتك النهائية إلى مديرك المباشر أو إدارة الموارد البشرية.</p>

<p>نقدّر جهدكم والتزامكم طوال هذا الربع، ونتطلع معاً إلى ربع أقوى.</p>

<p>هاشم عبد الرحمن خليل<br>
مدير الموارد البشرية — مجموعة الإطارات العربية</p>
