# -*- coding: utf-8 -*-
# Copyright 2017 Jean Respen and Nicolas Bessi
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openerp import models, fields


class ResCompany(models.Model):

    _inherit = 'res.company'

    bvr_background_on_merge = fields.Boolean(
        'Insert BVR Background with invoice ?'
    )
