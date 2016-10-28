# -*- coding: utf-8 -*-
# © 2012 David Coninckx (Opennet Sarl)
# Make additional fields translatable by Ermin Trevisan (twanda AG)
# License into __openerp__.py.

from openerp import fields, models
import openerp.addons.decimal_precision as dp


class HrContract(models.Model):
    _inherit = 'hr.contract'

    holiday_rate = fields.Float(string='Holiday Rate', translate=True)
    obp_rate = fields.Float(string='OBP Rate', translate=True,
                            digits=dp.get_precision('Payroll Rate'))
    obp_amount = fields.Float(string='OBP Amount', translate=True,
                              digits=dp.get_precision('Account'))
