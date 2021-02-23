# -*- coding: utf-8 -*-
# Copyright 2019-2020 Odoo
# Copyright 2019-2020 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import re

from openerp import models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    def _sanitize_account_number(self, acc_number):
        if acc_number:
            return re.sub(r'\W+', '', acc_number).upper()
        return False

    def _is_qr_iban(self):
        """ Tells whether or not this bank account has a QR-IBAN account number.
        QR-IBANs are specific identifiers used in Switzerland as references in
        QR-codes. They are formed like regular IBANs, but are actually something
        different.
        """
        if not self:
            return False

        self.ensure_one()
        sanitized_acc_number = self._sanitize_account_number(self.acc_number)
        iid = sanitized_acc_number[4:9]
        return (
            self.state == 'iban' and
            re.match(r'\d+', iid)
            and 30000 <= int(iid) <= 31999
        )  # Those values for iid are reserved for QR-IBANs only
