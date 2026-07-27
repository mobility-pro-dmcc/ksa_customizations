<p>The previous reviewer has completed the appraisal review for {{ doc.employee_name }} for the {{ doc.appraisal_cycle }} quarter, and the document has now moved to your stage.</p>
<p>Your deadline: {{ frappe.utils.formatdate(doc.end_date) }} 23:59</p>

<p>Your role at this stage:<br>
HR Compliance Check: Confirm all stages are complete, comments are logged, and process was followed. You are not scoring. Approve to move to COO or flag an issue to hold.<br>
Functional Manager / COO: Review the scores and approve or adjust with your own assessment and a written reason.</p>

<p>What you need to do:<br>
1. Open the appraisal: {{ frappe.utils.get_url_to_form('Appraisal', doc.name) }}<br>
2. Review the submission and all previous stage comments<br>
3. Approve, adjust (with reason), or flag an issue<br>
4. Submit — next stage triggers automatically</p>

<p>Not submitting by {{ frappe.utils.formatdate(doc.end_date) }} will notify HR.</p>

<hr>
<p>── النسخة العربية ──</p>

<p>أتمّ المُراجِع السابق مراجعته لتقييم {{ doc.employee_name }} للربع {{ doc.appraisal_cycle }}، وانتقل الملف الآن إليك في مرحلتك.</p>
<p>موعدك النهائي: {{ frappe.utils.formatdate(doc.end_date) }} الساعة 23:59</p>

<p>دورك في هذه المرحلة:<br>
· الموارد البشرية — فحص الامتثال: تحقق من اكتمال جميع المراحل وتدوين التعليقات واتباع الإجراءات الصحيحة. دورك هنا امتثالي لا تقييمي — وافق لإحالة الملف إلى المدير التنفيذي، أو أوقفه مؤقتاً في حال وجود ملاحظة إجرائية.<br>
· المدير الوظيفي / المدير التنفيذي: راجع الدرجات بموضوعية، ووافق أو عدّل مع إضافة مبرر مكتوب لأي تغيير.</p>

<p>خطوات الإنجاز:<br>
١. افتح التقييم: {{ frappe.utils.get_url_to_form('Appraisal', doc.name) }}<br>
٢. اطّلع على الإرسال وتعليقات المراحل السابقة<br>
٣. وافق أو عدّل أو أوقف مؤقتاً مع بيان السبب<br>
٤. أرسل — ستنتقل المرحلة التالية تلقائياً</p>

<p>عدم الإرسال بحلول الموعد النهائي سيُفضي إلى إخطار إدارة الموارد البشرية.</p>