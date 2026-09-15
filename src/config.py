"""Runtime configuration for the third-party integrations (sign-up + newsletter).

Values come from environment variables so the same source builds correctly
whether or not the integrations have been set up yet. See README.md for what
each one is and where to get it. Sensible non-secret placeholders are used
when a variable is missing, so the site always builds; the README explains
what still needs filling in before launch.
"""
import os


class Config:
    def __init__(self):
        # Google Apps Script Web App URL that receives sign-up form POSTs.
        self.gas_url = os.environ.get("GAS_SIGNUP_URL", "https://script.google.com/macros/s/REPLACE_WITH_APPS_SCRIPT_DEPLOYMENT_ID/exec")
        # Name of the honeypot field the sign-up form and the Apps Script backend agree on.
        self.gas_honeypot_field = os.environ.get("GAS_HONEYPOT_FIELD", "company_website")

        # Mailchimp embedded-form target (see the "Signup form" embed code Mailchimp
        # generates for a list, or the audience's "Manage contacts" page). The action
        # URL host is a dc-specific list-manage.com/subscribe/post endpoint; u and id
        # identify the account and audience/list.
        self.mc_action = os.environ.get("MAILCHIMP_ACTION_URL", "https://REPLACE.list-manage.com/subscribe/post")
        self.mc_u = os.environ.get("MAILCHIMP_U", "REPLACE_MC_U")
        self.mc_id = os.environ.get("MAILCHIMP_LIST_ID", "REPLACE_MC_LIST_ID")
        # Mailchimp's own bot-trap field name is unique per list: b_{u}_{id}.
        self.mc_honeypot_field = f"b_{self.mc_u}_{self.mc_id}"


CONFIG = Config()
