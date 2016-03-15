# -*- coding: utf-8 -*-
# © 2012 David Coninckx (Opennet Sarl)
# License into __openerp__.py.

from openerp import fields, models
import openerp.addons.decimal_precision as dp


class HrContract(models.Model):
    _inherit = 'hr.contract'

    holiday_rate = fields.Float(string='Holiday Rate')
    lpp_rate = fields.Float(string='LPP Rate',
                            digits=dp.get_precision('Payroll Rate'))
    lpp_amount = fields.Float(string='LPP Amount',
                              digits=dp.get_precision('Account'))
