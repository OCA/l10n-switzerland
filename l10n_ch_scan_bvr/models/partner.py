# -*- coding: utf-8 -*-
#
#  File: models/partner.py
#  Module: l10n_ch_scan_bvr
#
##############################################################################
#
#    Author: Nicolas Bessi, Vincent Renaville
#    Copyright 2012 Camptocamp SA
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


from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ------------------------- Fields management

    supplier_invoice_default_product = fields.Many2one(
        'product.product',
        string='Default product supplier invoice',
        help="""Used by the scan BVR wizard. If completed, it'll generate
 a line with the proper amount and this specified product"""
    )
