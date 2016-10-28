# -*- coding: utf-8 -*-
# © 2016 Ermin Trevisan (twanda AG)
# License into __openerp__.py.


from openerp import fields, models


class HrSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'

    # ---------- make code, name and note translatable

    code = fields.Char(translate=True)
    name = fields.Char(translate=True)
    note = fields.Char(translate=True)
