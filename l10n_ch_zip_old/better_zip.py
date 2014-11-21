# b-*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2014 brain-tec AG (http://www.brain-tec.ch)
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


class res_better_zip_ext(orm.Model):
    """Inherit res.better.zip class in order to add swiss specific fields"""
    _inherit = 'res.better.zip'
    
    # fields from the original file downloaded from here: https://match.post.ch/downloadCenter?product=2 -> File "PLZ Plus 1"
    _columns = {
        'active': fields.boolean('Active'),
        'onrp': fields.integer('Ordnungsnummer Post', size=5, help="Primärschlüssel"),
        'zip_typ': fields.integer('PLZ-Typ', size=2),
        'zusatzziffer': fields.integer('Zusatzziffer', size=2),
        'lang': fields.integer('Sprachcode', size=1, help="1 = deutsch, 2 = französisch, 3 = italienisch, 4 = rätoromanisch"),
        'lang2': fields.integer('Sprachcode abweichend', size=1, help="1 = deutsch, 2 = französisch, 3 = italienisch, 4 = rätoromanisch"),
        'sort': fields.integer('Bestandeszugehörigkeit Sortierfile', size=1),
        'post_delivery_through': fields.integer('Briefzustellung durch', size=5),
        'gemeindenummer_bfs': fields.integer('Gemeindenummer BfS', size=5),
        'valid_from': fields.char('Gültigkeitsdatum', size=8, help="YYYYMMDD"),
    }
    
    _defaults = {
        'active': lambda *a: 1,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
