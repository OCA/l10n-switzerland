# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests import TransactionCase


class TestQRInternational(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "QR Test",
                "street": "Rue du Fort Hatry",
                "zip": "90000",
                "city": "Belfort",
                "country_id": cls.env.ref("base.fr").id,
            }
        )
        cls.ch_company_bank = cls.env.ref("l10n_ch.partner_demo_company_bank_account")
        cls.chf_currency = cls.env.ref("base.CHF")

    def test_qr_international(self):
        errors = self.ch_company_bank._get_error_messages_for_qr(
            "ch_qr", self.partner, self.chf_currency
        )
        self.assertTrue(errors)
        self.partner.force_swiss_qr_invoice = True
        errors = self.ch_company_bank._get_error_messages_for_qr(
            "ch_qr", self.partner, self.chf_currency
        )
        self.assertFalse(errors)
