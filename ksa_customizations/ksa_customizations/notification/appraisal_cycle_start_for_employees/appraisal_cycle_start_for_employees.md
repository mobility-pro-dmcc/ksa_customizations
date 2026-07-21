<p>Dear {{ doc.employee_name }},</p>

<p>Your {{ doc.appraisal_cycle }} performance appraisal cycle is now open.</p>

<p>You have 48 hours to complete your self-assessment and submit to your direct manager. Deadline: {{ frappe.utils.add_days(frappe.utils.today(), 2) }}</p>

<p>What you need to do:<br>
1. Log in to the HR system: {{ frappe.utils.get_url() }}<br>
2. Go to My Appraisal → {{ doc.appraisal_cycle }}<br>
3. Review your KPIs and enter your self-score for each one<br>
4. Add a short comment per score — be specific, use actual numbers<br>
5. Click Submit — your direct manager is notified immediately</p>

<p>Your KPIs this quarter:<br>
{% for kpi in frappe.db.get_list("Goal", {"appraisal_cycle": doc.appraisal_cycle, "employee": doc.employee, "is_group":["!=", 1]}, ["goal_name", "kra", "progress"]) %}
{{ kpi.goal_name }} — {{ kpi.kra }} — {{ kpi.progress }}%<br>
{% endfor %}
</p>

<p>A few things to keep in mind:<br>
&middot; Your manager will review every score against actual results — make sure your assessment is accurate and objective.<br>
&middot; Back your scores with numbers. "Revenue was SAR X vs target SAR Y" is stronger than "target achieved".<br>
&middot; Any questions about a KPI or target — speak to your manager before submitting.<br>
&middot; Not submitting by {{ frappe.utils.add_days(frappe.utils.today(), 2) }} will trigger an automatic notification to your manager and HR.</p>

<p>Hashim Abdul Rahaman Khalil<br>
HR Manager — Arabian Tires Group<br>
Questions? hashim@arabiantires.com</p>

<hr>

<p>عزيزي {{ doc.employee_name }}،</p>

<p>انطلقت اليوم دورة تقييم الأداء لـ {{ doc.appraisal_cycle }}، وقد حان وقت تقييمك الذاتي.</p>

<p>لديك مدة ٤٨ ساعة لاستكمال التقييم وإرساله إلى مديرك المباشر. الموعد النهائي: {{ frappe.utils.add_days(frappe.utils.today(), 2) }}.</p>

<p>خطوات الإنجاز:<br>
١. سجّل دخولك إلى نظام الموارد البشرية: {{ frappe.utils.get_url() }}<br>
٢. انتقل إلى: تقييمي &larr; {{ doc.appraisal_cycle }}<br>
٣. راجع مؤشرات أدائك وأدخل تقييمك لكل مؤشر<br>
٤. أضف تعليقاً موجزاً على كل درجة — استند إلى الأرقام الفعلية<br>
٥. أرسل التقييم — سيُخطَر مديرك المباشر فور إرسالك</p>

<p>مؤشراتك هذا الربع:<br>
{% for kpi in frappe.db.get_list("Goal", {"appraisal_cycle": doc.appraisal_cycle, "employee": doc.employee}) %}
{{ kpi.goal_name }} — {{ kpi.kra }} — {{ kpi.progress }}%<br>
{% endfor %}
</p>

<p>ملاحظات مهمة:<br>
&middot; سيراجع مديرك كل درجة في ضوء النتائج الفعلية، لذا احرص على أن يكون تقييمك دقيقاً وموضوعياً.<br>
&middot; استند دائماً إلى الأرقام. عبارة «بلغت الإيرادات X ريال من أصل هدف Y ريال» أفضل بكثير من «تم تحقيق الهدف».<br>
&middot; إن كان لديك استفسار حول أي مؤشر أو هدفه، تواصل مع مديرك قبل الإرسال.<br>
&middot; عدم الإرسال بحلول {{ frappe.utils.add_days(frappe.utils.today(), 2) }} سيُفضي إلى إخطار مديرك وإدارة الموارد البشرية تلقائياً.</p>

<p>هاشم عبد الرحمن خليل<br>
مدير الموارد البشرية — مجموعة الإطارات العربية<br>
للاستفسار تواصل مع الموارد البشرية على: hashim@arabiantires.com</p>
