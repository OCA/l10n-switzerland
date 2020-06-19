# -*- coding: utf-8 -*-
# Copyright 2019-2020 Odoo
# Copyright 2019-2020 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import re

from odoo import models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    def _is_qr_iban(self):
        """ Tells whether or not this bank account has a QR-IBAN account number.
        QR-IBANs are specific identifiers used in Switzerland as references in
        QR-codes. They are formed like regular IBANs, but are actually something
        different.
        """
        if not self:
            return False

        self.ensure_one()

        iid_start_index = 4
        iid_end_index = 8
        iid = self.sanitized_acc_number[iid_start_index : iid_end_index + 1]
        return (
            self.acc_type == 'iban'
            and re.match(r'\d+', iid)
            and 30000 <= int(iid) <= 31999
        )  # Those values for iid are reserved for QR-IBANs only
