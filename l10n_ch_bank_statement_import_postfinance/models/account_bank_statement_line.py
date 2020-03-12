# Copyright 2015 Nicolas Bessi Camptocamp SA
# Copyright 2017-2019 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, fields


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    related_file = fields.Many2one(
        comodel_name='ir.attachment',
        string='Related file',
        readonly=True
    )
    datas = fields.Binary(related='related_file.datas')
    file_ref = fields.Char()

    @api.multi
    def click_icon(self):
        view_id = self.env.ref(
            'l10n_ch_bank_statement_import_postfinance.'
            'attachement_form_postfinance879').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attachment',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ir.attachment',
            'view_id': view_id,
            'res_id': self.related_file.id,
            'target': 'new',
        }
