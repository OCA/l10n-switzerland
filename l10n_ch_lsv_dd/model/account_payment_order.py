##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2014 Compassion (http://www.compassion.ch)
#    Copyright (C) 2017 brain-tec AG (http://www.braintec-group.com)
#    @author: Cyril Sester <cyril.sester@outlook.com>
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
from openerp import models, api, _
import base64


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.multi
    def show_invoices(self):
        move_ids = [pay_line.move_line_id.move_id.id
                    for pay_order in self
                    for pay_line in pay_order.payment_line_ids]

        action = {
            'name': _('Related invoices'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('move_id', 'in', move_ids)],
            'res_model': 'account.invoice',
            'target': 'current',
        }

        return action

    @api.multi
    def generate_payment_file(self):
        """ Overridden to consider LSV and DD.
            Returns (payment file as string, filename)
        """
        self.ensure_one()

        payment_method_code = self.payment_method_id.code

        # We are going to re-use the wizard, thus we pass the active_ids through the context.
        new_context = self._context.copy()
        new_context.update({'active_ids': self.ids})

        # We use as the currency that of the journal, or the currency of the company if not defined.
        currency = self.journal_id.currency_id or self.journal_id.company_id.currency_id

        if payment_method_code == 'lsv':
            lsv_treatment_type = self.payment_method_id.lsv_treatment_type or 'T'
            lsv_export_wizard = self.env['lsv.export.wizard'].\
                create({'treatment_type': lsv_treatment_type,
                        'currency': currency.name,
                        })
            lsv_export_wizard.with_context(new_context).generate_lsv_file()
            return base64.decodestring(lsv_export_wizard.file), lsv_export_wizard.filename

        elif payment_method_code == 'postfinance.dd':
            dd_export_wizard = self.env['post.dd.export.wizard'].\
                create({'currency': currency.name})
            dd_export_wizard.with_context(new_context).generate_dd_file()
            return base64.decodestring(dd_export_wizard.file), dd_export_wizard.filename

        else:
            res = super(AccountPaymentOrder, self).generate_payment_file()

        return res
