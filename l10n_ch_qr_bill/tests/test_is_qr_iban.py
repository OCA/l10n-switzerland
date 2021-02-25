# -*- coding: utf-8 -*-
# Copyright 2021 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.tests.common import SavepointCase
from odoo.exceptions import ValidationError

CH_IBAN = 'CH15 3881 5158 3845 3843 7'
QR_IBAN = 'CH21 3080 8001 2345 6782 7'


class TestIsQRIBAN(SavepointCase):

    def setUp(self):
        super(TestIsQRIBAN, self).setUp()
        self.env.user.company_id.partner_id.write(
            {
                "street": "Route de Berne 88",
                "street2": "",
                "zip": "2000",
                "city": "Neuchâtel",
                "country_id": self.env.ref('base.ch').id,
            }
        )

    def create_account(self, acc_number, qr_iban):
        """ Generates a test res.partner.bank. """
        return self.env['res.partner.bank'].create(
            {
                'acc_number': acc_number,
                'l10n_ch_qr_iban': qr_iban,
                'partner_id': self.env.user.company_id.partner_id.id,
            }
        )

    def test_QR_IBAN_acc_number(self):
        bank_acc = self.create_account(QR_IBAN, False)
        self.assertTrue(bank_acc._is_qr_iban())

    def test_QR_IBAN_qr_iban_type_iban(self):
        """Set l10n_ch_qr_iban and an iban in acc_number"""
        bank_acc = self.create_account(CH_IBAN, QR_IBAN)
        self.assertTrue(bank_acc._is_qr_iban())

    def test_QR_IBAN_qr_iban_type_bank(self):
        """Set l10n_ch_qr_iban and a non iban account in acc_number"""
        bank_acc = self.create_account("Not an iban", QR_IBAN)
        self.assertTrue(bank_acc._is_qr_iban())

    def test_bad_qr_iban(self):
        """IBAN is not QR-IBAN"""
        with self.assertRaises(ValidationError):
            self.create_account(CH_IBAN, CH_IBAN)

    def test_bad_qr_iban_country_code(self):
        """Only CH and LI are allowed"""
        NOT_QR_IBAN = QR_IBAN.replace("CH", "FR")
        with self.assertRaises(ValidationError):
            self.create_account(CH_IBAN, NOT_QR_IBAN)

    def test_bad_qr_iban_range(self):
        """Check no false positive with range 30000-31999"""
        NOT_QR_IBAN = "CH1131111111111"
        with self.assertRaises(ValidationError):
            self.create_account(CH_IBAN, NOT_QR_IBAN)

    def test_not_qr_iban(self):
        bank_acc = self.create_account(CH_IBAN, False)
        self.assertFalse(bank_acc._is_qr_iban())

    def test_not_qr_iban_bank(self):
        """Set l10n_ch_qr_iban and an iban in acc_number"""
        bank_acc = self.create_account("Not an iban", False)
        self.assertFalse(bank_acc._is_qr_iban())

    def test_not_qr_iban_bank_sneaky(self):
        """Set acc_number with a non IBAN which shouldn't be detected as a
        QR-IBAN"""
        NOT_QR_IBAN = "CH1131111111111"
        bank_acc = self.create_account(NOT_QR_IBAN, False)
        self.assertFalse(bank_acc._is_qr_iban())
