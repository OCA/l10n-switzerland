# -*- coding: utf-8 -*-
from odoo import models, api, exceptions, _


class CreditControlPrinter(models.TransientModel):
    """Print lines"""
    _inherit = 'credit.control.printer'

    @api.multi
    def print_linked_isr(self):
        self.ensure_one()
        if not self.line_ids and not self.print_all:
            raise exceptions.Warning(
                _('No credit control lines selected.')
            )
        credits = self.line_ids
        report_name = 'slip_from_credit_control'
        report_obj = self.env['report'].with_context(active_ids=credits.ids)
        return report_obj.get_action(credits, report_name)
