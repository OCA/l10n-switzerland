# -*- coding: utf-8 -*-
from odoo import models, api


class PaymentSlip(models.Model):
    """implement amount hook"""

    _inherit = "l10n_ch.payment_slip"

    def _compute_amount_hook(self):
        """Hook to return the total amount of payment slip

        :return: total amount of payment slip
        :rtype: float
        """
        amount = super(PaymentSlip, self)._compute_amount_hook()
        context = self.env.context
        if context.get('slip_credit_control_line_id'):
            cr_line_obj = self.env['credit.control.line']
            credit_line_id = context['slip_credit_control_line_id']
            credit_line = cr_line_obj.browse(credit_line_id)
            amount += credit_line.dunning_fees_amount
        return amount

    @api.depends('move_line_id.credit_control_line_ids',
                 'move_line_id.credit_control_line_ids.dunning_fees_amount')
    def compute_amount(self):
        return super(PaymentSlip, self).compute_amount()
