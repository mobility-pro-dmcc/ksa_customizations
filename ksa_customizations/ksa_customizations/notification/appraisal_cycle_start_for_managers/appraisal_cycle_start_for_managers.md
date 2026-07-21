<p>Dear</p>

<p>The {{ doc.name }} appraisal cycle opened today, {{ frappe.utils.formatdate(doc.start_date) }}. All employees have been notified and have until {{ frappe.utils.formatdate(doc.end_date) }} to submit.</p>

<p>Key deadlines — fixed for all:<br>
Employee self-assessment: {{ frappe.utils.formatdate(doc.end_date) }} 23:59<br>
Direct manager review: {{ frappe.utils.formatdate(doc.end_date) }} 23:59<br>
Functional manager review (Finance only): {{ frappe.utils.formatdate(doc.end_date) }} 23:59<br>
HR compliance check: {{ frappe.utils.formatdate(doc.end_date) }} 23:59<br>
COO sign-off: {{ frappe.utils.formatdate(doc.end_date) }} 23:59</p>

<p>Important: Your deadline is fixed regardless of when employees submit. If anyone misses their window you will be notified and can enter scores on their behalf.</p>

<p>You will receive an individual notification each time a team member submits. Any employee who misses their deadline is escalated to you and HR automatically.</p>

<p>Live dashboard: {{ frappe.utils.get_url_to_list('Appraisal') }}</p>

<p>Hashim Abdul Rahaman Khalil<br>
HR Manager — Arabian Tires Group</p>

<hr>

<p>── النسخة العربية ──</p>

<p>عزيزي،</p>

<p>انطلقت دورة تقييم الأداء للربع {{ doc.name }} اليوم {{ frappe.utils.formatdate(doc.start_date) }}. تم إخطار جميع الموظفين ومنحهم مهلة حتى {{ frappe.utils.formatdate(doc.end_date) }} لإرسال تقييماتهم الذاتية.</p>

<p>المواعيد النهائية — ثابتة للجميع:<br>
التقييم الذاتي للموظفين: {{ frappe.utils.formatdate(doc.end_date) }} الساعة 23:59<br>
مراجعة المدير المباشر: {{ frappe.utils.formatdate(doc.end_date) }} الساعة 23:59<br>
مراجعة المدير الوظيفي (المالية فقط): {{ frappe.utils.formatdate(doc.end_date) }} الساعة 23:59<br>
فحص الامتثال — الموارد البشرية: {{ frappe.utils.formatdate(doc.end_date) }} الساعة 23:59<br>
موافقة المدير التنفيذي: {{ frappe.utils.formatdate(doc.end_date) }} الساعة 23:59</p>

<p>ملاحظة جوهرية: موعدك النهائي ثابت ولا يتأثر بتوقيت إرسال الموظفين. في حال تأخر أي موظف، ستتلقى إشعاراً فورياً ويمكنك إدخال درجاته مباشرة.</p>

<p>ستتلقى إشعاراً منفصلاً في كل مرة يُرسل فيها أحد أعضاء فريقك. أي موظف يتجاوز موعده سيُصعَّد تلقائياً إليك وإلى الموارد البشرية.</p>

<p>لوحة المتابعة المباشرة: {{ frappe.utils.get_url_to_list('Appraisal') }}</p>

<p>هاشم عبد الرحمن خليل<br>
مدير الموارد البشرية — مجموعة الإطارات العربية</p>