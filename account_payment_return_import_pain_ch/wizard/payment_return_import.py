# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

from .pain_ch_parser import PainCHParser

_logger = logging.getLogger(__name__)


class PaymentReturnImport(models.TransientModel):
    _inherit = "payment.return.import"

    def _complete_parsed_data(self, payment_returns):
        """Complete CH Pain parser data"""
        new_payment_returns = []
        for payment_return in payment_returns:
            for transaction in payment_return["transactions"]:
                move = self.env["account.move"].browse(int(transaction["reference"]))
                transaction["amount"] = move.amount_total
                transaction["partner_id"] = move.partner_id.id
                transaction["reference"] = move.ref
            payment_order = self.env["account.payment.order"].search(
                [("name", "=", payment_return.pop("order_name"))]
            )
            payment_return["payment_order_id"] = payment_order.id
            if "account_number" not in payment_return:
                payment_return[
                    "account_number"
                ] = payment_order.company_partner_bank_id.acc_number
            payment_return["journal_id"] = payment_order.journal_id.id
            new_payment_returns.append(payment_return)
        return new_payment_returns

    @api.model
    def _parse_file(self, data_file):
        """Parse a PAIN.002.001.03 XML file."""
        try:
            _logger.debug("Try parsing with Direct Debit Unpaid Report.")
            return self._complete_parsed_data(PainCHParser().parse(data_file))
        except ValueError:
            # Not a valid file, returning super will call next candidate:
            _logger.debug(
                "Payment return file was not a Direct Debit Unpaid " "Report file.",
                exc_info=True,
            )
            return super()._parse_file(data_file)
