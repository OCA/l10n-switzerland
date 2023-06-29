# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

from .pain_parser_ch import PainParserCH

_logger = logging.getLogger(__name__)


class PaymentReturnImport(models.TransientModel):
    _inherit = "payment.return.import"

    @api.model
    def _parse_single_document(self, data_file):
        """
        Try to parse the file as the following format or fall back on next
        parser:
            - pain.002.001.03.CH
        """
        pain_parser = PainParserCH()
        try:
            _logger.debug("Try parsing as a PAIN Direct Debit Unpaid CH " "Report.")
            return pain_parser.parse(data_file)
        except ValueError:
            _logger.debug(
                "Payment return file is not a ISO20022 CH " "supported file.",
                exc_info=True,
            )
            return super()._parse_single_document(data_file)
