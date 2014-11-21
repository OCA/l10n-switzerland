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

from openerp.osv import orm


class account_move_line(orm.Model):
    '''
    Use hooks to add bvr ref generation if account is IBAN and has LSV
    identifier
    '''

    _inherit = 'account.move.line'

    def _is_generate_bvr(self, cr, uid, invoice, context=None):
        ''' If linked bank account is an iban account with LSV identifier,
            we also generate a bvr ref (as it's necessary in LSV file)
        '''
        val = super(account_move_line, self)._is_generate_bvr(cr, uid, invoice,
                                                              context)
        return val or (invoice.partner_bank_id and
                       invoice.partner_bank_id.state == 'iban' and
                       invoice.partner_bank_id.lsv_identifier)
