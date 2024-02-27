##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2014 Compassion (http://www.compassion.ch)
#    @author: Cyril Sester <cyril.sester@outlook.com>
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

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        # LSV files need ISR reference in the communication field.
        if payment_order.payment_method_id.pain_version == "pain.008.001.02.ch.03":
            vals["communication"] = self.move_id.ref.replace(" ", "")
        if payment_order.payment_type == "inbound":
            if payment_order.company_partner_bank_id.bank_id.clearing == "9000":
                # Force correct values for Postfinance
                vals.update(
                    {"local_instrument": "DDCOR1", "communication_type": "normal"}
                )
            else:
                # No other types than LSV+ in Switzerland
                vals.update(
                    {
                        "local_instrument": "LSV+",
                    }
                )
        return vals
