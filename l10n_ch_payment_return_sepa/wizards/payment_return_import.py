# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models, _
from ..models.errors import NoPaymentReturnError, NoTransactionsError, \
    ErrorOccurred

_logger = logging.getLogger(__name__)


class PaymentReturnImport(models.TransientModel):
    _inherit = 'payment.return.import'

    @api.model
    def _check_parsed_data(self, payment_returns):
        """ Override base function to avoid raising errors when the statement has no
        transaction """
        if not payment_returns:
            raise NoPaymentReturnError(_(
                'This file doesn\'t contain any payment return.'))
        for payret_vals in payment_returns:
            if payret_vals.get('transactions'):
                return
        # If we get here, no transaction was found:
        if payment_returns[0].get('error'):
            raise ErrorOccurred(payment_returns[0]['error'], payment_returns)
        else:
            raise NoTransactionsError(
                _('This file doesn\'t contain any transaction.'),
                payment_returns
            )

    @api.model
    def _parse_file(self, data_file):
        """Parse a PAIN.002.001.03 XML file."""
        try:
            _logger.debug("Try parsing with Direct Debit Unpaid Report.")
            return self.env['account.pain002.parser'].parse(data_file)
        except ValueError:
            # Not a valid file, returning super will call next candidate:
            _logger.debug("Payment return file was not a Direct Debit Unpaid "
                          "Report file.",
                          exc_info=True)
            return super()._parse_file(data_file)
