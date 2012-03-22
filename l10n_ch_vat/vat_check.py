# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher (Camptocamp)
#    Contributor:
#    Copyright 2012 Camptocamp SA
#    Donors:
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

from osv import osv
import re
from base_vat.base_vat import _ref_vat


_ref_vat['ch'] = 'CHE-123.456.789 TVA or CH TVA 123456'

class res_partner(osv.osv):
    _inherit = 'res.partner'

 
    def check_vat_ch(self, vat):
        '''
        Check Switzerland VAT number.
        '''
        # VAT number in Switzerland will change between 2011 and 2013 
        # http://www.estv.admin.ch/mwst/themen/00154/00589/01107/index.html?lang=fr
        # Old format is "TVA 123456" we will admit the user has to enter ch before the number
        # Format will becomes such as "CHE-999.999.99C TVA"
        # Both old and new format will be accepted till end of 2013
        # Accepted format are: (spaces are ignored)
        #     CH TVA ######
        #     CH IVA ######
        #     CH MWST #######
        #
        #     CHE#########MWST
        #     CHE#########TVA
        #     CHE#########IVA
        #     CHE-###.###.### MWST
        #     CHE-###.###.### TVA
        #     CHE-###.###.### IVA
        #
        check_vat_ch_re1 = re.compile(r'(MWST|TVA|IVA)[0-9]{6}$')
        check_vat_ch_re2 = re.compile(r'E([0-9]{9}|-[0-9]{3}\.[0-9]{3}\.[0-9]{3})(MWST|TVA|IVA)$')
        if check_vat_ch_re1.match(vat):
            return True
        match = check_vat_ch_re2.match(vat)
        if match: 
            # For new TVA numbers, do a mod11 check
            num = filter(lambda s: s.isdigit(), match.group(1))        # get the digits only
            factor = (5,4,3,2,7,6,5,4)
            csum = sum([int(num[i]) * factor[i] for i in range(8)])
            check = 11 - (csum % 11)
            return check == int(num[8])
        return False


res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
