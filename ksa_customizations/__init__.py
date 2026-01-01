__version__ = "0.0.1"

import functools
import frappe

def wrap_script():
    """ Decorator to wrap server script functions to check function enable/disable status in KSA Scripts doctype. """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            method_path = f"{fn.__module__}.{fn.__name__}"

            row = frappe.db.get_value(
                "KSA Scripts",
                {"method": method_path},
                ["name", "disabled"],
                as_dict=True,
            )

            if not row:
                doc = frappe.get_doc({
                    "doctype": "KSA Scripts",
                    "method": method_path,
                })
                doc.insert(ignore_permissions=True)
            else:
                if row.disabled:
                    return

            return fn(*args, **kwargs)

        return wrapper

    return decorator

__all__ = ["wrap_script"]