# Copyright 2012-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResPartnerBank(models.Model):
    """
    Inherit res.partner.bank class in order to add swiss specific fields
    such as:
     - ISR data
     - ISR print options for company accounts
     We leave it here in order
    """
    _inherit = "res.partner.bank"

    print_bank = fields.Boolean('Print Bank on ISR')
    print_account = fields.Boolean('Print Account Number on ISR')
    print_partner = fields.Boolean('Print Partner Address on ISR')
