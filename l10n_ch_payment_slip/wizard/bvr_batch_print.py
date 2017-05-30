# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.exceptions import UserError


class BvrBatchPrintWizard(models.TransientModel):

    _name = 'bvr.batch.print.wizard'

    invoice_ids = fields.Many2many(comodel_name='account.invoice',
                                   string='Invoices')
    error_message = fields.Text('Errors')

    @api.model
    def default_get(self, fields):
        res = super(BvrBatchPrintWizard, self).default_get(fields)
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
            invoices._check_bvr_generatable()
        except UserError, e:
            return e.name

    @api.multi
    def print_payment_slips(self):
        if self.invoice_ids:
            return self.invoice_ids.print_bvr()
        else:
            return {'type': 'ir.actions.act_window_close'}
