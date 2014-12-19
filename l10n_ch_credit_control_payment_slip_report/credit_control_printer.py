# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2013 Camptocamp SA
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
from openerp import models, api, exceptions, _


class CreditControlPrinter(models.TransientModel):
    """Print lines"""
    _inherit = 'credit.control.printer'

    @api.multi
    def print_linked_bvr(self):
        """Print BVR from credit line
        We do not use the communication
        as it is not required and will be
        less efficient

        """
        self.ensure_one()
        if not self.line_ids and not self.print_all:
            raise exceptions.Warning(
                _('No credit control lines selected.')
            )
        credits = self.line_ids
        report_name = 'slip_from_credit_control'
        report_obj = self.env['report'].with_context(active_ids=credits.ids)
        return report_obj.get_action(credits, report_name)
