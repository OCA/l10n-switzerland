# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrSalaryRuleCategory(models.Model):

    _inherit = 'hr.salary.rule.category'
    name = fields.Char(translate=True)
    note = fields.Char(translate=True)
