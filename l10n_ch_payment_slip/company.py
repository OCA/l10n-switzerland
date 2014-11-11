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
from openerpimport models, fields


class ResCompany(models.Model):
    """override company in order to add bvr vertical and
    Horizontal print delta"""
    _inherit = "res.company"

    bvr_delta_horz = fields.Float(
        'BVR Horz. Delta (px)',
        help='horiz. delta in px 1.2 will print the bvr 1.2px lefter, '
        'negative value is possible'
    )

    bvr_delta_vert = fields.Float(
        'BVR Vert. Delta (px)',
        help='vert. delta in px 1.2 will print the bvr 1.2px lower, '
        'negative value is possible'
    )

    bvr_scan_line_vert = fields.Float(
        'BVR vert. position for scan line (px)',
        help=Vert. position in px for scan line
    )

    bvr_scan_line_horz = fields.Float(
        'BVR horiz. position for scan line(px)',
        help='Horiz. position in px for scan line'
    )

    bvr_add_vert = fields.Float(
        'BVR vert. position for address (px)',
        help='Vert. position in px for address'
    )

    bvr_add_horz = fields.Float(
        'BVR horiz. position address (px)',
        help='Horiz. position in px for address'
    )

    bvr_scan_line_font_size = fields.Float(
        'BVR scan line font size (pt)'
    )

    bvr_scan_line_letter_spacing = fields.Float(
        'BVR scan line letter spacing'
    )

    bvr_background = fields.Boolean('Insert BVR background ?')
