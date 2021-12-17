# -*- coding: utf-8 -*-
# copyright 2016 Akretion - Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountPaymentLine(models.Model):
    _inherit = 'account.payment.line'

    local_instrument = fields.Selection(
        selection_add=[('CH01', 'CH01 (BVR)')])
    communication_type = fields.Selection(
        selection_add=[('bvr', 'BVR'), ("qrr", "QRR")])

    def invoice_reference_type2communication_type(self):
        res = super(AccountPaymentLine, self).\
            invoice_reference_type2communication_type()
        res.update({'bvr': 'bvr', 'qrr': 'qrr'})
        return res
