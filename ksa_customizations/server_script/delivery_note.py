import mobility_customizations as mc
from ksa_customizations.server_script.common_scripts import update_contact_person

@mc.wrap_script()
def update_contact(doc, method):
    update_contact_person(doc, method)

def validate(doc, method):
    update_contact(doc, method)