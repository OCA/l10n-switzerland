# copyright 2020 Compassion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountPaymentLine(models.Model):
    _inherit = 'account.payment.line'

    local_instrument = fields.Selection(
        selection_add=[('LSV+', 'LSV+')])
