# -*- coding: utf-8 -*-
# © 2015 Nicolas Bessi (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class ResCompany(models.Model):

    _inherit = 'res.company'

    bvr_background_on_merge = fields.Boolean(
        'Insert BVR Background with invoice ?'
    )
