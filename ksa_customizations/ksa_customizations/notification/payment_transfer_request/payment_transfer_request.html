{% set sender_id = frappe.db.get_value("Account", doc.paid_from, "custom_assigned_person") %}
{% set reciever_id = frappe.db.get_value("Account", doc.paid_to, "custom_assigned_person") %}
{% if doc.workflow_state == "Open" %}
{{ frappe.db.get_value("Contact", {"user": sender_id}, "sales_person") }} أرسل لك طلبًا بخصوص المستند 
<a href="{{ doc.get_url() }}">{{ doc.name }}</a>.
{% elif doc.workflow_state == "Submitted" %}
{{ frappe.db.get_value("Contact", {"user": reciever_id}, "sales_person") }} قام بقبول طلبك 
<a href="{{ doc.get_url() }}">{{ doc.name }}</a>.
{% elif doc.workflow_state == "Discarded" %}
{{ frappe.db.get_value("Contact", {"user": reciever_id}, "sales_person") }} قام برفض طلبك 
<a href="{{ doc.get_url() }}">{{ doc.name }}</a>.
{% endif %}
