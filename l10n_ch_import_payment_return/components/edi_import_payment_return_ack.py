# Copyright 2023 Compassion CH (https://www.compassion.ch)
# @author: Simon Gonzalez <simon.gonzalez@bluewin.ch>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.account_payment_return_import_pain_ch.wizard.pain_ch_parser import (
    PainCHParser,
)
from odoo.addons.component.core import Component


class EDIExchangeProcessPaymentReturn(Component):
    """ACK for payment order pain002.01.03.CH"""

    _name = "edi.input.payment.ch.ack.process"
    _inherit = "edi.component.input.mixin"
    _backend_type = "sftp_pay_ord_ack"
    _usage = "input.process"

    def process(self):
        origin_output = self.exchange_record.parent_id
        payment_order = self.env[origin_output.model].browse(
            self.exchange_record.parent_id.res_id
        )
        try:
            PainCHParser.validate_status(self.exchange_record.exchange_file)
        except Exception as e:
            payment_order.action_cancel()
            raise e
        payment_order.generated2uploaded()
