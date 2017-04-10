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

from openerp import models, api


class AccountMoveLine(models.Model):
    '''
    Use hooks to add BVR ref generation if account is IBAN and has LSV
    identifier
    '''

    _inherit = 'account.move.line'

    def _is_generate_bvr(self, invoice):
        ''' If linked bank account is an IBAN account with LSV identifier,
            we also generate a BVR ref (as it's necessary in LSV file)
        '''
        val = super(AccountMoveLine, self)._is_generate_bvr(invoice)
        return val or (invoice.partner_bank_id and
                       invoice.partner_bank_id.state == 'iban' and
                       invoice.partner_bank_id.lsv_identifier)

    @api.multi
    def line2bank(self, payment_mode_id):
        ''' Override line2bank to avoid choosing a bank that has only
            cancelled mandate.
        '''
        pay_mode_obj = self.env['payment.mode']
        if payment_mode_id:
            pay_mode = pay_mode_obj.browse(payment_mode_id)
            if pay_mode.type.payment_order_type == 'debit':
                line2bank = dict()
                bank_types = pay_mode_obj.suitable_bank_types(payment_mode_id)
                for line in self:
                    line2bank[line.id] = False
                    if line.partner_id:
                        bank_id = self._get_active_bank_account(
                            line.partner_id.bank_ids,
                            bank_types)
                        if bank_id:
                            line2bank[line.id] = bank_id
                        else:
                            line2bank.update(
                                super(AccountMoveLine, line).line2bank(
                                    payment_mode_id))
                return line2bank
        return super(AccountMoveLine, self).line2bank(payment_mode_id)

    def _get_active_bank_account(self, banks, bank_types):
        for bank in banks:
            if bank.state in bank_types:
                for mandate in bank.mandate_ids:
                    if mandate.state == 'valid':
                        return bank.id
