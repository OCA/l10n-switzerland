# -*- coding: utf-8 -*-
# © 2016 Coninckx David (Open Net Sarl)
# © 2017 Leonardo Franja (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    slip_id = fields.Many2one('hr.payslip', string='Pay slip')
