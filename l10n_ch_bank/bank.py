# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA / Migrated to version 8 by brain-tec AG
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

from openerp.osv import osv, fields


class res_bank_ext(osv.osv):

    " Inherit res.bank class in order to add swiss specific fields "
    _inherit = 'res.bank'

    """ fields from the original file downloaded from here:
    http://www.six-interbank-clearing.com/de/home/bank-master-data/download-bc-bank-master.html """
    _columns = {
        " Gruppe "
        'bank_group': fields.char('Group', size=2),
        " Filial-ID "
        'bank_branchid': fields.char('Branch-ID', size=5),
        'bank_clearing_new': fields.char('BCNr new', size=5),
        'bank_sicnr': fields.char('SIC-Nr', size=6),
        " Hauptsitz "
        'bank_headquarter': fields.char('Headquarter', size=5),
        'bank_bcart': fields.char('BC-Art', size=1),
        'bank_valid_from': fields.char('Valid from', size=8),
        'bank_sic': fields.char('SIC', size=1),
        'bank_eurosic': fields.char('euroSIC', size=1),
        'bank_lang': fields.char('Sprache', size=1),
        'bank_postaladdress': fields.char('Postal address', size=35),
        " Vorwahl "
        'bank_areacode': fields.char('Area code', size=5),
        """ Postkonto - ccp does not allow to enter entries like *30-38151-2
        because of the '*' but this comes from the xls to import """
        'bank_postaccount': fields.char('Post account', size=35),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
