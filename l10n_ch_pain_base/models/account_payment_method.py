# -*- coding: utf-8 -*-
# © 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    bic_required = fields.Boolean(
        string='BIC Required', default=True,
        help="If active, Odoo will ask for a BIC when generating the file")
