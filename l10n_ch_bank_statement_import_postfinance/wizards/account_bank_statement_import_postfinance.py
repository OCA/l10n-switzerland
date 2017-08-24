# -*- coding: utf-8 -*-
# Copyright 2017 Emanuel Cino <ecino@compassion.ch>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from openerp import api, models

logger = logging.getLogger(__name__)


class AccountBankStatementImport(models.TransientModel):
    _inherit = "account.bank.statement.import"

    @api.model
    def _create_bank_statements(self, stmt_vals):
        """Override to support attachements. There is always only one
        statement at a time for Postfinance Imports.
        """
        attachments = list(stmt_vals[0].pop('attachments', list()))

        statement_ids, notifs = super(
            AccountBankStatementImport,
            self
        )._create_bank_statements(stmt_vals)
        for attachment in attachments:
            att_data = {
                'name': attachment[0],
                'type': 'binary',
                'datas': attachment[1],
            }
            statement_line = self.env[
                'account.bank.statement.line'].search(
                [('file_ref', '=', attachment[0]),
                 ('statement_id', '=', statement_ids[0])]
            )
            if statement_line:
                # Link directly attachement with the right statement line
                att_data['res_id'] = statement_line.id
                att_data['res_model'] = 'account.bank.statement.line'
                att = self.env['ir.attachment'].create(att_data)
                statement_line.related_file = att
            else:
                att_data['res_id'] = statement_ids[0]
                att_data['res_model'] = 'account.bank.statement'
                self.env['ir.attachment'].create(att_data)

        return statement_ids, notifs
