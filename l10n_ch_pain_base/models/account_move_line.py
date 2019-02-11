# copyright 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        if self.invoice_id and self.invoice_id.reference_type == 'isr':
            vals['local_instrument'] = 'CH01'
            if vals['communication']:
                vals['communication'] = vals['communication'].replace(' ', '')
        return vals
