# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from openerp import models, _


_logger = logging.getLogger(__name__)


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _match_ref(self, transaction):
        """try to find an invoice based on transaction references.

        Adapted from l10n_ch_payment_slip/wizard/bvr_import.py line 160.
        """
        if transaction['partner_id']:
            return
        line = self.env['account.move.line'].search(
            [('transaction_ref', '=', transaction['ref']),
             ('reconciled', '=', False),
             ('account_id.user_type_id.type', 'in', ['receivable', 'payable']),
             ('journal_id.type', '=', 'sale'),
             ],
            order='date desc',
        )
        if len(line) > 1:
            _logger.warning(
                _("Too many receivable/payable lines for reference %s")
                % transaction['ref'])
            return

        if line:
            # transaction_ref is propagated on all lines
            partner_id = line.partner_id.id
            num = line.invoice_id.number if line.invoice_id else False
            if num:
                transaction['name'] = transaction['ref']
                transaction['ref'] = _('Inv. no %s') % num
            transaction['partner_id'] = partner_id

    def _complete_stmts_vals(self, statements, journal, account_number):
        statements = super(AccountBankStatementImport, self).\
            _complete_stmts_vals(statements, journal, account_number)
        for statement in statements:
            for transaction in statement['transactions']:
                self._match_ref(transaction)
        return statements
