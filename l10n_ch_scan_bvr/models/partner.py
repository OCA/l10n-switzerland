# -*- coding: utf-8 -*-
# Author: Vincent Renaville
# Copyright 2013 Camptocamp SA
# Copyright 2015 Alex Comba - Agile Business Group
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    supplier_invoice_default_product = fields.Many2one(
        comodel_name='product.product',
        string='Default product supplier invoice',
        help="Used by the scan BVR wizard. If completed, it'll generate "
             "a line with the proper amount and this specified product"
    )
