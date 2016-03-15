# -*- coding: utf-8 -*-
# © 2012 David Coninckx (Opennet Sarl)
# License into __openerp__.py.


from openerp import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ---------- Fields management

    children = fields.Integer('Number of Children at school')
    children_student = fields.Integer('Number of Children student')
