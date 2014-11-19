# b-*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2010 brain-tec AG (http://www.brain-tec.ch) 
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
from openerp.osv import orm, fields


class res_bank_ext(orm.Model):
    """Inherit res.bank class in order to add swiss specific fields"""
    _inherit = 'res.bank'
    
    # fields from the original file downloaded from here: http://www.six-interbank-clearing.com/de/home/bank-master-data/download-bc-bank-master.html
    _columns = {
        'bank_gruppe': fields.char('Gruppe', size=2),
        'bank_filialid': fields.char('Filial-ID', size=5),
        'bank_clearing_neu': fields.char('BCNr neu', size=5),
        'bank_sicnr': fields.char('SIC-Nr', size=6),
        'bank_hauptsitz': fields.char('Hauptsitz', size=5),
        'bank_bcart': fields.char('BC-Art', size=1),
        'bank_valid_from': fields.char('gültig ab', size=8),
        'bank_sic': fields.char('SIC', size=1),
        'bank_eurosic': fields.char('euroSIC', size=1),
        'bank_lang': fields.char('Sprache', size=1),
        'bank_postadresse': fields.char('Postadresse', size=35),
        'bank_vorwahl': fields.char('Vorwahl', size=5),
        'bank_postkonto': fields.char('Postkonto', size=35),  # ccp does not allow to enter entries like *30-38151-2 because of the '*' but this comes from the xls to import
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
