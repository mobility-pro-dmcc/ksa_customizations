<p>Dear</p>

<p>{{ doc.employee }} submitted their {{ doc.appraisal_cycle }} self-assessment on {{ frappe.utils.formatdate(doc.modified) }} at {{ frappe.utils.format_time(doc.modified) }}.</p>

<p>Your deadline to review all team submissions is {{ frappe.utils.formatdate(doc.end_date) }} 23:59. This is fixed — it does not change based on when each person submits.</p>

<p>Their submitted scores:<br>
    {{ doc.goal_name }} → {{ doc.progress }}%</p>

<p>What you need to do:<br>
1. Open their kpi: {{ frappe.utils.get_url_to_form('Goal', doc.name) }}<br>
2. Review score against actual results<br>
3. Approve, or enter your own score<br>
4. Submit — next stage triggers automatically</p>

<p>Anyone who has not submitted by {{ frappe.utils.formatdate(doc.end_date) }} will be escalated to you and HR.</p>

<hr>

<p>── النسخة العربية ──</p>

<p>عزيزي,</p>

<p>أرسل {{ doc.employee }} تقييمه الذاتي للربع {{ doc.appraisal_cycle }} بتاريخ {{ frappe.utils.formatdate(doc.modified) }} الساعة {{ frappe.utils.format_time(doc.modified) }}.</p>

<p>موعدك النهائي لمراجعة جميع إرسالات فريقك هو {{ frappe.utils.formatdate(doc.end_date) }} الساعة 23:59. هذا الموعد ثابت ولا يتغير بحسب توقيت إرسال كل موظف.</p>

<p>درجاته المُرسَلة:<br>
    {{ doc.goal_name }} ← التقييم الذاتي: {{ doc.progress }}%</p>

<p>خطوات المراجعة:<br>
١. افتح ملف التقييم: {{ frappe.utils.get_url_to_form('Goal', doc.name) }}<br>
٢. راجع الدرجة في مقابل النتائج الفعلية التي لديك<br>
٣. وافق على الدرجة أو عدّلها<br>
٤. أرسل — ستنتقل الدورة تلقائياً إلى المرحلة التالية</p>

<p>أي موظف لم يُرسل بحلول موعده النهائي سيُصعَّد تلقائياً إليك وإلى الموارد البشرية.</p>
