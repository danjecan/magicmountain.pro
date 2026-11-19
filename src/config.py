"""Runtime configuration for the third-party integrations (sign-up + newsletter).

Values come from environment variables so the same source builds correctly
whether or not the integrations have been set up yet. See README.md for what
each one is and where to get it. Sensible non-secret placeholders are used
when a variable is missing, so the site always builds; the README explains
what still needs filling in before launch.
"""
import os


def _env(name, default=""):
    """Like os.environ.get, but an empty value counts as unset: the deploy workflow passes
    every optional repo variable, and an unset one arrives as an empty string."""
    return os.environ.get(name) or default


class Config:
    def __init__(self):
        # Google Apps Script Web App URL that receives sign-up form POSTs.
        self.gas_url = _env("GAS_SIGNUP_URL", "https://script.google.com/macros/s/REPLACE_WITH_APPS_SCRIPT_DEPLOYMENT_ID/exec")
        # Cloudflare Turnstile site key (public by design). Empty = no widget; the Apps Script
        # then also has no secret and skips the check. See gas/Code.gs.
        self.turnstile_site_key = _env("TURNSTILE_SITE_KEY", "")
        # Name of the honeypot field the sign-up form and the Apps Script backend agree on.
        self.gas_honeypot_field = _env("GAS_HONEYPOT_FIELD", "company_website")

        # Mailchimp embedded-form target (see the "Signup form" embed code Mailchimp
        # generates for a list, or the audience's "Manage contacts" page). The action
        # URL host is a dc-specific list-manage.com/subscribe/post endpoint; u and id
        # identify the account and audience/list.
        self.mc_action = _env("MAILCHIMP_ACTION_URL", "https://REPLACE.list-manage.com/subscribe/post")
        self.mc_u = _env("MAILCHIMP_U", "REPLACE_MC_U")
        self.mc_id = _env("MAILCHIMP_LIST_ID", "REPLACE_MC_LIST_ID")
        # Mailchimp's own bot-trap field name is unique per list: b_{u}_{id}.
        self.mc_honeypot_field = f"b_{self.mc_u}_{self.mc_id}"


CONFIG = Config()
