# -*- coding: utf-8 -*-
# Copyright 2009 Camptocamp SA
# Copyright 2015 Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResPartnerBank(models.Model):
    """
    Inherit res.partner.bank class in order to add swiss specific fields
    such as:
     - BVR data
     - BVR print options for company accounts
     We leave it here in order
    """
    _inherit = "res.partner.bank"

    dta_code = fields.Char('DTA code')
