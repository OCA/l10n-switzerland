# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, api, fields


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
            image = "data:png;base64," + related_file.datas
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
