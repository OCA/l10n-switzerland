# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.addons.decimal_precision as dp
from datetime import timedelta
from odoo import fields, models, api

#Import logger
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    is_correction_final_payslip = fields.Boolean(string="Bulletin final de correction")
    other_year_payslip_ids = fields.Many2many('hr.payslip', string="Autres salaires de l'années", compute="_get_other_payslips")

    @api.multi
    def _get_other_payslips(self):
        for payslip in self:
            current_year = fields.Date.from_string(payslip.date_from).year
            date_from = "%s-01-01" % current_year
            date_to = "%s-12-31" % current_year
            other_payslips = self.search([
                ('employee_id', '=', payslip.employee_id.id),
                ('id', '!=', payslip.id),
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to)
            ])
            payslip.other_year_payslip_ids = other_payslips

    @api.multi
    def get_total_of_rule_by_code(self, code, amount):
        total = 0
        for other_payslip in self.other_year_payslip_ids:
            total += sum([line.total for line in other_payslip.line_ids if line.code == code])
        total += amount
        return total