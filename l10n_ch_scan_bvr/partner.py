# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Vincent Renaville
#    Copyright 2013 Camptocamp SA
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

from openerp.osv.orm import Model, fields


class ResPartner(Model):
    _inherit = 'res.partner'

    _columns = {
        'supplier_invoice_default_product': fields.many2one(
            'product.product',
            'Default product supplier invoice',
            help="Use by the scan BVR wizard, if completed, it'll generate "
                 "a line with the proper amount and this specified product"
        ),
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
