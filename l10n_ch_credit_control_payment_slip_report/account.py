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
from openerp.osv import orm


class account_move_line(orm.Model):
    """Overrride BVR amount to take in account dunning fees"""

    _inherit = "account.move.line"

    def _get_bvr_amount(self, cr, uid, move, rtype=None):
        """Hook to get amount in CHF for BVR
        The amount must include dunning fees

        :param move: move line report
        :param rtype: report type string just in case

        :returns: BVR float amount

        """
        fees = getattr(move, 'bvr_dunning_fees', 0.0)
        return move.debit + fees
