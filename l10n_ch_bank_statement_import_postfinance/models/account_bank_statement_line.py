# -*- coding: utf-8 -*-
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
    def get_statement_line_for_reconciliation_widget(self):
        data = super(AccountBankStatementLine,
                     self).get_statement_line_for_reconciliation_widget()
        if self.related_file.datas:
            related_file = self.related_file
            image = "data:png;base64," + related_file.datas.decode("utf-8")
            data['img_src'] = ['src', image]
            data['modal_id'] = ['id', 'img' + str(related_file.id)]
            data['data_target'] = [
                'data-target', '#img' + str(related_file.id)]
        return data

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
