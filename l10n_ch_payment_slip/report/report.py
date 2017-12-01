# Copyright 2014-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class ISRFromInvoice(models.AbstractModel):
    _name = 'report.one_slip_per_page_from_invoice'
