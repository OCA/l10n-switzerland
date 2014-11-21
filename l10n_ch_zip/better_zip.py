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


class res_better_zip_ext(osv.osv):

    " Inherit res.better.zip class in order to add swiss specific fields "
    _inherit = 'res.better.zip'

    """ fields from the original file downloaded from here:
    https://match.post.ch/downloadCenter?product=2 -> File "PLZ Plus 1" """
    _columns = {
        'active': fields.boolean('Active'),
        " Ordnungsnummer Post "
        'onrp': fields.integer('Order number Post', size=5, help="Primary Key"),
        'zip_type': fields.integer('Zip type', size=2),
        " Zusatzziffer "
        'additional_digit': fields.integer('Additional digit', size=2),
        'lang': fields.integer('Sprachcode', size=1, help="1 = deutsch, 2 = französisch, 3 = italienisch, 4 = rätoromanisch"),
        'lang2': fields.integer('Sprachcode abweichend', size=1, help="1 = deutsch, 2 = französisch, 3 = italienisch, 4 = rätoromanisch"),
        'sort': fields.integer('Bestandeszugehörigkeit Sortierfile', size=1),
        'post_delivery_through': fields.integer('Briefzustellung durch', size=5),
        " Gemeindenummer BfS "
        'communitynumber_bfs': fields.integer('Community number BfS', size=5),
        'valid_from': fields.char('Valid from', size=8, help="YYYYMMDD"),
    }

    _defaults = {
        'active': lambda *a: 1,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
