# -*- coding: utf-8 -*-
# Copyright 2015 Camptocamp SA - Nicolas Bessi
# Copyright 2017 Jean Respen
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openerp import models, fields


class ResCompany(models.Model):

    _inherit = 'res.company'

    bvr_background_on_merge = fields.Boolean(
        'Insert BVR Background with invoice ?'
    )
