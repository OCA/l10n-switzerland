# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, api


class payment_slip(models.Model):
    """implement amount hook"""

    _inherit = "l10n_ch.payment_slip"

    def _compute_amount_hook(self):
        """Hook to return the total amount of payment slip

        :return: total amount of payment slip
        :rtype: float
        """
        context = self.env.context
        if context.get('__slip_credit_control_line_id'):
            cr_line_obj = self.env['credit.control.line']
            credit_line_id = context['__slip_credit_control_line_id']
            credit_line = cr_line_obj.browse(credit_line_id)
            amount = credit_line.balance_due + credit_line.dunning_fees_amount
        else:
            amount = super(payment_slip, self)._compute_amount_hook()
        return amount

    # extend 'depends'
    @api.one
    @api.depends('move_line_id.credit_control_line_ids',
                 'move_line_id.credit_control_line_ids.dunning_fees_amount')
    def compute_amount(self):
        return super(payment_slip, self).compute_amount()
