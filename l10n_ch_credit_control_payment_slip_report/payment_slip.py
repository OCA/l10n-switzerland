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
from openerp import models


class payment_slip(models.Model):
    """implement amount hook"""

    _inherit = "l10n_ch.payment_slip"

    def _compute_amount_hook(self):
        """Hook to return the total amount of pyament slip

        :return: total amount of payment slip
        :rtype: float
        """
        amount = super(payment_slip, self)._compute_amount_hook()
        credit_lines = self.env['credit.control.line'].search(
            [('move_line_id', '=', self.move_line_id.id),
             ('state', 'in', ('to_be_sent', 'sent'))]
        )
        if credit_lines:
            return amount + sum(line.dunning_fees_amount
                                for line in credit_lines)
        return amount
