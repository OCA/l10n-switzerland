import logging

from odoo import http
from odoo.http import request
from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)


def _render_view(is_integrated, template_xml_id, values=None):
    values = dict(values or {})
    if is_integrated:
        values["is_integrated"] = is_integrated
        return request.env["ir.ui.view"]._render_template(template_xml_id, values)
    else:
        return request.render(template_xml_id, values)


class EbillSubscriptionController(http.Controller):
    @http.route(
        "/ebill/subscribe",
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
        sitemap=False,
    )
    def subscribe(self, is_integrated=False, **kw):
        email = kw.get("email")

        normalized_email = email_normalize(email)
        if not normalized_email:
            return _render_view(
                is_integrated,
                "ebill_postfinance_recipient_subscription.subscribe_template",
                {"submitted_email": email},
            )

        try:
            ebill_service = request.env[
                "ebill.postfinance.service"
            ]._get_ebill_service_instance()
            token_sub = ebill_service.initiate_ebill_recipient_subscription(email)

            return _render_view(
                is_integrated,
                "ebill_postfinance_recipient_subscription.validate_template",
                {
                    "token": token_sub.SubscriptionInitiationToken,
                    "email": email,
                },
            )

        except Exception:
            _logger.warning(
                "Failed to initiate eBill subscription for email '%s'.",
                email,
                exc_info=True,
            )
            return _render_view(
                is_integrated,
                "ebill_postfinance_recipient_subscription.subscribe_template",
                {"submitted_email": email},
            )

    @http.route(
        "/ebill/validate",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        sitemap=False,
    )
    def confirm(self, is_integrated=False, **post):
        token = post.get("token")
        activation_code = post.get("validation_code")
        email = post.get("email")
        ebill_service = request.env[
            "ebill.postfinance.service"
        ]._get_ebill_service_instance()

        try:
            partner_data = ebill_service.confirm_ebill_recipient_subscription(
                token, activation_code
            )

            if not (partner_data and partner_data.EbillAccountID):
                _logger.warning(
                    f"eBill validation failed for token '{token}' "
                    f"(e.g., incorrect code)."
                )

                return _render_view(
                    is_integrated,
                    "ebill_postfinance_recipient_subscription.validate_template",
                    {
                        "error": (
                            "Validation failed. Please verify the code or check "
                            "if an eBill connection is possible with this email."
                        ),
                        "token": token,
                        "email": email,
                    },
                )

            party = getattr(partner_data, "Party", None)
            partner_address = getattr(party, "Address", None)
            name = (partner_data.EmailAddress or "").split("@", 1)[
                0
            ] or partner_data.EmailAddress  # fallback name

            if partner_address:
                name = " ".join(
                    filter(
                        None,
                        [
                            (partner_address.GivenName or "").strip(),
                            (partner_address.FamilyName or "").strip(),
                        ],
                    )
                )

            ebill_recipient_info = {
                "email": partner_data.EmailAddress,
                "ebill_account_id": partner_data.EbillAccountID,
                "name": name,
                "street": partner_address.Address1 if partner_address else None,
                "zip": partner_address.ZIP if partner_address else None,
                "city": partner_address.City if partner_address else None,
            }

            ebill_service._ensure_partner_and_contract(ebill_recipient_info)

            return _render_view(
                is_integrated,
                "ebill_postfinance_recipient_subscription.success_template",
            )

        except Exception as e:
            _logger.warning(
                "Exception during confirmation, likely "
                "a wrong activation code for token '%s': %s",
                token,
                e,
                exc_info=True,
            )

            return _render_view(
                is_integrated,
                "ebill_postfinance_recipient_subscription.validate_template",
                {
                    "error": (
                        "Validation failed. Please verify the code or check "
                        "if an eBill connection is possible with this email."
                    ),
                    "token": token,
                    "email": email,
                },
            )

    @http.route(
        "/ebill/current-user/contract",
        type="json",
        auth="user",
        methods=["POST"],
        sitemap=False,
    )
    def ebill_me_contract(self, **kw):
        try:
            user = request.env.user
            partner = user.sudo().partner_id

            if not partner or partner == request.env.ref(
                "base.public_partner", raise_if_not_found=False
            ):
                return {"has_contract": False, "contract": None}

            ebill_service = request.env[
                "ebill.postfinance.service"
            ]._get_ebill_service_instance()
            transmit_method = ebill_service._get_ebill_transmit_method()
            contract = partner.sudo().get_active_contract(transmit_method)

            if not contract:
                contract = partner._lookup_ebill_contract()
                if not contract:
                    return {
                        "has_contract": False,
                        "contract": None,
                        "partner": {
                            "id": partner.id,
                            "name": partner.name,
                            "email": partner.email,
                        },
                    }
            return {
                "has_contract": True,
                "partner": {
                    "id": partner.id,
                    "name": partner.name,
                    "email": partner.email,
                },
                "contract": {
                    "id": contract.id,
                    "state": contract.state,
                    "transmit_method": transmit_method.name,
                    "postfinance_billerid": contract.postfinance_billerid or None,
                    "service_id": contract.postfinance_service_id.id
                    if contract.postfinance_service_id
                    else None,
                },
            }
        except Exception as e:
            _logger.error("Error in /ebill/current-user/contract: %s", e, exc_info=True)
            return {"error": "Could not check eBill contract for current user."}
