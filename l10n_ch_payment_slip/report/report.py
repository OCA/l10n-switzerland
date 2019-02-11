# Copyright 2014-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class ISRFromInvoice(models.AbstractModel):
    _name = 'report.one_slip_per_page_from_invoice'
    _description = 'ISR Invoice report'
