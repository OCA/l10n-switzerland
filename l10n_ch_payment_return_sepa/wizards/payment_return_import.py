# Copyright 2016 Carlos Dauden <carlos.dd_account_journal_xml_dddauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import base64

from odoo import api, models, _
from odoo.exceptions import UserError
from ..models.errors import NoPaymentReturnError, NoTransactionsError, \
    ErrorOccurred

_logger = logging.getLogger(__name__)


class PaymentReturnImport(models.TransientModel):
    _inherit = 'payment.return.import'

    @api.model
    def _check_parsed_data(self, payment_returns):
        """ Basic and structural verifications """
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

    @api.multi
    def import_file(self):
        """Process the file chosen in the wizard, create bank payment return(s)
        and go to reconciliation."""
        self.ensure_one()
        data_file = base64.b64decode(self.data_file)
        payment_returns, notifications, order_name = self.with_context(
            active_id=self.id
        )._import_file(data_file)
        result = self.env.ref(
            'account_payment_return.payment_return_action').read()[0]
        if self.match_after_import:
            payment_returns.button_match()
        if len(payment_returns) != 1:
            result['domain'] = "[('id', 'in', %s)]" % payment_returns.ids
        else:
            form_view = self.env.ref(
                'account_payment_return.payment_return_form_view')
            result.update({
                'views': [(form_view.id, 'form')],
                'res_id': payment_returns.id,
                'context': {
                    'notifications': notifications,
                    'order_name': order_name
                },
            })
        return result

    @api.model
    def _import_file(self, data_file):
        """ Create bank payment return(s) from file."""
        # The appropriate implementation module returns the required data
        payment_returns = self.env['payment.return']
        notifications = []
        payment_return_raw_list = self._parse_all_files(data_file)
        # Check raw data:
        self._check_parsed_data(payment_return_raw_list)
        order_name = ''
        # Import all payment returns:
        for payret_vals in payment_return_raw_list:
            payret_vals = self._complete_payment_return(payret_vals)
            payment_return, new_notifications = self._create_payment_return(
                payret_vals)
            if payment_return:
                payment_return.action_confirm()
                payment_returns += payment_return
            notifications.extend(new_notifications)
            order_name = payret_vals['order_name']
        if not payment_returns:
            raise UserError(_('You have already imported this file.'))
        return payment_returns, notifications, order_name

    @api.model
    def _parse_file(self, data_file):
        """Parse a PAIN.002.001.03 XML file."""
        try:
            _logger.debug("Try parsing with Direct Debit Unpaid Report.")
            return self.env['account.pain002.parser'].parse(data_file)
        except ValueError:
            # Not a valid file, returning super will call next candidate:
            _logger.debug("Paymen return file was not a Direct Debit Unpaid "
                          "Report file.",
                          exc_info=True)
            return super()._parse_file(data_file)
