# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.exceptions import UserError


class ISRBatchPrintWizard(models.TransientModel):

    _name = 'isr.batch.print.wizard'
    _description = 'Printing Wizard for payment slip'

    invoice_ids = fields.Many2many(comodel_name='account.invoice',
                                   string='Invoices')
    error_message = fields.Text('Errors', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(ISRBatchPrintWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            invoices = self.env['account.invoice'].browse(active_ids)
            msg = self.check_generatable(invoices)
            if msg:
                res['error_message'] = msg
            res['invoice_ids'] = active_ids
        return res

    @api.model
    def check_generatable(self, invoices):
        try:
            invoices._check_isr_generatable()
        except UserError as e:
            return e.name

    @api.multi
    def print_payment_slips(self):
        if self.invoice_ids:
            return self.invoice_ids.print_isr()
        else:
            return {'type': 'ir.actions.act_window_close'}
