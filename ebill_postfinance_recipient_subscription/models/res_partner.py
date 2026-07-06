import logging

from odoo import models

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    def _lookup_ebill_contract(self):
        self.ensure_one()

        ebill_service = self.env[
            "ebill.postfinance.service"
        ]._get_ebill_service_instance()

        if not self.email:
            _logger.info("Partner %s has no email for eBill lookup.", self.id)
            return None

        try:
            recipient_ids = [self.email]
            results = ebill_service.get_ebill_recipient_subscription_status_bulk(
                recipient_ids
            )

            bill_recipients_obj = getattr(results, "BillRecipients", None)
            received_recipients = getattr(bill_recipients_obj, "BillRecipient", [])

            allowed_recipient = next(
                (
                    r
                    for r in received_recipients
                    if getattr(r, "SubmissionStatus", None) == "ALLOWED"
                    and r.EmailAddress.lower() == self.email.lower()
                ),
                None,
            )

            if not allowed_recipient:
                _logger.info(
                    "No 'ALLOWED' eBill subscription found for partner %s (email: %s).",
                    self.id,
                    self.email,
                )
                return None

            ebill_recipient_info = {
                "partner_id": self.id,
                "ebill_account_id": allowed_recipient.EbillAccountID,
            }

            partner, contract = ebill_service._ensure_partner_and_contract(
                ebill_recipient_info
            )

            _logger.info(
                "eBill subscription found for partner %s. "
                "Returning info to controller...",
                self.id,
            )
            return contract

        except Exception as e:
            _logger.error(
                "Unexpected Exception during bulk search occurred: %s",
                e,
                exc_info=True,
            )
            return None
