# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Financial contributors: Hasa SA, Open Net SA,
#                            Prisme Solutions Informatique SA, Quod SA
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


class ResCompany(Model):
    """override company in order to add bvr vertical and
    Horizontal print delta"""
    _inherit = "res.company"

    _columns = {
        'bvr_delta_horz': fields.float('BVR Horz. Delta (mm)',
            help='horiz. delta in mm 1.2 will print the bvr 1.2mm lefter, negative value is possible'),

        'bvr_delta_vert': fields.float('BVR Vert. Delta (mm)',
            help='vert. delta in mm 1.2 will print the bvr 1.2mm lower, negative value is possible'),

        'bvr_scan_line_vert': fields.float('BVR vert. position for scan line (mm)',
            help='Vert. position in mm for scan line'),

        'bvr_scan_line_horz': fields.float('BVR horiz. position for scan line(mm)',
            help='Horiz. position in mm for scan line'),

        'bvr_add_vert': fields.float('BVR vert. position for address (mm)',
            help='Vert. position in mm for address'),

        'bvr_add_horz': fields.float('BVR horiz. position address (mm)',
            help='Horiz. position in mm for address'),

        'bvr_scan_line_font_size': fields.float('BVR scan line font size (pt)'),

        'bvr_scan_line_letter_spacing': fields.float('BVR scan line letter spacing'),

        'bvr_background': fields.boolean('Insert BVR background ?'),
    }

    _defaults = {
        'bvr_delta_vert': -5,
        'bvr_scan_line_vert': 265,
        'bvr_scan_line_horz': 67,
        'bvr_scan_line_font_size': 11,
        'bvr_scan_line_letter_spacing': 2.55,
        'bvr_add_vert': 6,
        'bvr_add_horz': 60,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
