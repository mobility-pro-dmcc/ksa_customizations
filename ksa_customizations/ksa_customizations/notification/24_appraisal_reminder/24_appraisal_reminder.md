<p>Dear {{ doc.employee }}</p>

<p>This is a reminder that your {{ doc.appraisal_cycle }} self-assessment has not been submitted yet.</p>

<p>Deadline: {{ frappe.utils.formatdate(doc.end_date) }} 23:59 — 24 hours from now.</p>

<p>Submit here: {{ frappe.utils.get_url_to_form('Appraisal', doc.name) }}</p>

<p>Missing the deadline will trigger an automatic notification to your direct manager and HR, and your scores may be entered on your behalf.</p>

<p>Technical issue? Contact HR immediately: hashim@arabiantires.com</p>

<hr>

<p>── النسخة العربية ──</p>

<p>عزيزي {{ doc.employee }}،</p>

<p>نودّ تذكيرك بأن تقييمك الذاتي للربع {{ doc.appraisal_cycle }} لم يُرسَل حتى الآن.</p>

<p>الموعد النهائي: {{ frappe.utils.formatdate(doc.end_date) }} الساعة 23:59 — أي بعد ٢٤ ساعة فقط.</p>

<p>أرسل تقييمك من هنا: {{ frappe.utils.get_url_to_form('Appraisal', doc.name) }}</p>

<p>تجاوز الموعد النهائي دون إرسال سيؤدي إلى إخطار مديرك المباشر وإدارة الموارد البشرية تلقائياً، وقد تُدخَل درجاتك بالنيابة عنك.</p>

<p>في حال واجهت أي عائق تقني، تواصل مع الموارد البشرية فوراً على: hashim@arabiantires.com</p>
