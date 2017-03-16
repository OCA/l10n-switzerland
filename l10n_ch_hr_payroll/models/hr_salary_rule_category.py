# -*- coding: utf-8 -*-
# © 2017 Leonardo Franja (Opennet Sarl)
# License into __openerp__.py.

from odoo import fields, models


class HrSalaryRuleCategory(models.Model):

    _inherit = 'hr.salary.rule.category'
    name = fields.Char(translate=True)
    note = fields.Char(translate=True)
