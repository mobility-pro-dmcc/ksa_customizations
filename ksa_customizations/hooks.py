app_name = "ksa_customizations"
app_title = "KSA Customizations"
app_publisher = "Mobility Pro DMCC"
app_description = "Customization for ATG"
app_email = "info@mobilityp.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "ksa_customizations",
# 		"logo": "/assets/ksa_customizations/logo.png",
# 		"title": "KSA Customizations",
# 		"route": "/ksa_customizations",
# 		"has_permission": "ksa_customizations.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/ksa_customizations/css/ksa_customizations.css"
# app_include_js = "/assets/ksa_customizations/js/ksa_customizations.js"

# include js, css files in header of web template
# web_include_css = "/assets/ksa_customizations/css/ksa_customizations.css"
# web_include_js = "/assets/ksa_customizations/js/ksa_customizations.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ksa_customizations/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"Delivery Note" : "public/js/delivery_note_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "ksa_customizations/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "ksa_customizations.utils.jinja_methods",
# 	"filters": "ksa_customizations.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "ksa_customizations.install.before_install"
# after_install = "ksa_customizations.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "ksa_customizations.uninstall.before_uninstall"
# after_uninstall = "ksa_customizations.uninstall.after_uninstall"

# Migration
# ------------ 
before_migrate = "ksa_customizations.before_migrate.Migration"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "ksa_customizations.utils.before_app_install"
# after_app_install = "ksa_customizations.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "ksa_customizations.utils.before_app_uninstall"
# after_app_uninstall = "ksa_customizations.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ksa_customizations.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Payment Reconciliation": "ksa_customizations.overrides.payment_reconciliation.CustomPaymentReconciliation"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Sales Invoice": {
        # "on_submit": "ksa_customizations.server_script.sales_invoice.on_submit",
        # "on_cancel": "ksa_customizations.server_script.sales_invoice.on_cancel",
        "validate": "ksa_customizations.server_script.sales_invoice.validate",
    },
    "Payment Entry": {
        "on_submit": "ksa_customizations.server_script.payment_entry.on_submit",
        "before_cancel": "ksa_customizations.server_script.payment_entry.before_cancel"
    },
    "Sales Order": {
        "validate": "ksa_customizations.server_script.sales_order.validate",
    },
    "Quotation": {
        "validate": "ksa_customizations.server_script.quotation.validate",
    },
    "Delivery Note": {
        "validate": "ksa_customizations.server_script.delivery_note.validate",
    },
    "Customer": {
        "on_update": "ksa_customizations.server_script.customer.on_update",
    },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
# 	"all": [
# 		"ksa_customizations.tasks.all"
# 	],
	"daily": [
		"ksa_customizations.events.repost_item_valuation_for_zero_qty_stock_entries"
	],
# 	"hourly": [
# 		"ksa_customizations.tasks.hourly"
# 	],
# 	"weekly": [
# 		"ksa_customizations.tasks.weekly"
# 	],
# 	"monthly": [
# 		"ksa_customizations.tasks.monthly"
# 	],
}

# Testing
# -------

# before_tests = "ksa_customizations.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ksa_customizations.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ksa_customizations.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["ksa_customizations.utils.before_request"]
# after_request = ["ksa_customizations.utils.after_request"]

# Job Events
# ----------
# before_job = ["ksa_customizations.utils.before_job"]
# after_job = ["ksa_customizations.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"ksa_customizations.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

