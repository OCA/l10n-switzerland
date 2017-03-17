# -*- coding: utf-8 -*-
# © 2012 David Coninckx (Opennet Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ---------- Fields management

    children = fields.Integer('Number of Children at school')
    children_student = fields.Integer('Number of Children student')
