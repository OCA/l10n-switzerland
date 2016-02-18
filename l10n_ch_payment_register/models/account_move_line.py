# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 brain-tec AG (http://www.braintec-group.com)
#    All Right Reserved
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

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.multi
    def line2bank(self, ids):
        """
        Try to return for each Ledger Posting line a corresponding bank
        account according to the payment type.  This work using one of
        the bank of the partner defined on the invoice eventually
        associated to the line.
        Return the first suitable bank for the corresponding partner.
        """
        line2bank = {}

        for line in self.browse(ids):
            line2bank[line.id] = False
            if line.invoice_id and line.invoice_id.partner_bank_id:
                line2bank[line.id] = line.invoice_id.partner_bank_id.id
            elif line.partner_id:
                if not line.partner_id.bank_ids:
                    line2bank[line.id] = False
                else:
                    for bank in line.partner_id.bank_ids:
                        line2bank[line.id] = bank.id
                        break
                if not line2bank.get(line.id) and line.partner_id.bank_ids:
                    line2bank[line.id] = line.partner_id.bank_ids[0].id
            else:
                raise UserError(_('There is no partner defined on the entry'
                                  ' line.'))
        return line2bank
