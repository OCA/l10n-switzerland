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

# import time
from openerp import models, fields


class PaymentMode(models.Model):
    _name = 'payment.mode'
    _description = 'Payment Mode'

    name = fields.Char('Name', required=True, help='Mode of Payment')

    bank_id = fields.Many2one('res.partner.bank', "Bank account",
                              required=True,
                              help='Bank Account for the Payment Mode')

    journal_id = fields.Many2one('account.journal', 'Journal', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))],
                                 help='Bank or Cash Journal for the '
                                 'Payment Mode')

    company_id = fields.\
        Many2one('res.company', 'Company', required=True,
                 default=lambda self: self.env.user.company_id.id)

    partner_id = fields.Many2one('res.partner',
                                 related='company_id.partner_id',
                                 string='Partner', store=True)

    def suitable_bank_types(self, payment_code=None, context=None):
        """Return the codes of the bank type that are suitable
        for the given payment type code"""
        if not payment_code:
            return []
        self.env.cr.execute(""" SELECT pb.state
            FROM res_partner_bank pb
            JOIN payment_mode pm ON (pm.bank_id = pb.id)
            WHERE pm.id = %s """, [payment_code])
        return [x[0] for x in self.env.cr.fetchall()]

# TO DO if used
#     def onchange_company_id (self, cr, uid, ids, company_id=False,
#                              context=None):
#         result = {}
#         if company_id:
#             partner_id = self.pool.get('res.company').\
#                browse(cr, uid, company_id, context=context).partner_id.id
#             result['partner_id'] = partner_id
#         return {'value': result}
