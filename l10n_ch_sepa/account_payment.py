# -*- coding: utf-8 -*-
##############################################################################
#
#    SEPA Credit Transfer module for OpenERP
#    Copyright (C) 2017 Camptocamp
#    @author: Anar Baghirli <a.baghirli@mobilunity.com>
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

from openerp.osv import fields, osv


class payment_line(osv.osv):

    _inherit = 'payment.line'

    _columns = {
        'local_instrument': fields.selection([
            ('CH01', 'CH01'),
            ('CH02', 'CH02'),
            ('CH03', 'CH03'), ],
            'Local_instrument',),
    }
