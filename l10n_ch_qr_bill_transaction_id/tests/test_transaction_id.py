# -*- coding: utf-8 -*-
# Copyright 2020 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import time

from odoo.addons.account.tests.account_test_classes import AccountingTestCase

CH_IBAN = 'CH15 3881 5158 3845 3843 7'
QR_IBAN = 'CH21 3080 8001 2345 6782 7'


class TestTransactionID(AccountingTestCase):
    def setUp(self):
        super(TestTransactionID, self).setUp()
        self.customer = self.env['res.partner'].create(
            {
                "name": "Partner",
                "street": "Route de Berne 41",
                "street2": "",
                "zip": "1000",
                "city": "Lausanne",
                "country_id": self.env.ref("base.ch").id,
            }
        )
        self.env.user.company_id.partner_id.write(
            {
                "street": "Route de Berne 88",
                "street2": "",
                "zip": "2000",
                "city": "Neuchâtel",
                "country_id": self.env.ref('base.ch').id,
            }
        )
        self.invoice1 = self.create_invoice('base.CHF')

    def create_invoice(self, currency_xmlid='base.CHF'):
        """ Generates a test invoice """

        product = self.env.ref("product.product_product_4")
        acc_type = self.env.ref('account.data_account_type_current_assets')
        account = self.env['account.account'].search(
            [('user_type_id', '=', acc_type.id)], limit=1
        )
        invoice = (
            self.env['account.invoice']
            .with_context(default_type='out_invoice')
            .create(
                {
                    'type': 'out_invoice',
                    'partner_id': self.customer.id,
                    'currency_id': self.env.ref(currency_xmlid).id,
                    'date': time.strftime('%Y') + '-12-22',
                    'invoice_line_ids': [
                        (
                            0,
                            0,
                            {
                                'name': product.name,
                                'product_id': product.id,
                                'account_id': account.id,
                                'quantity': 1,
                                'price_unit': 42.0,
                            },
                        )
                    ],
                }
            )
        )
        return invoice

    def create_account(self, number):
        """ Generates a test res.partner.bank. """
        return self.env['res.partner.bank'].create(
            {
                'acc_number': number,
                'partner_id': self.env.user.company_id.partner_id.id,
            }
        )

    def test_swissQR_missing_bank(self):
        # Let us test the generation of a SwissQR for an invoice, first by showing an
        # QR is included in the invoice is only generated when Odoo has all the data
        # it needs.
        self.invoice1.action_invoice_open()
        self.assertFalse(self.invoice1.transaction_id)

    def test_swissQR_iban(self):
        # Now we add an account for payment to our invoice
        # Here we don't use a structured reference
        iban_account = self.create_account(CH_IBAN)
        self.invoice1.partner_bank_id = iban_account
        self.invoice1.action_invoice_open()
        self.assertFalse(self.invoice1.transaction_id)

    def test_swissQR_qriban(self):
        # Now use a proper QR-IBAN, we are good to print a QR Bill
        # In this case the transaction_id must be set
        qriban_account = self.create_account(QR_IBAN)
        self.assertTrue(qriban_account.acc_type, 'qr-iban')
        self.invoice1.partner_bank_id = qriban_account
        self.invoice1.action_invoice_open()
        self.assertEqual(
            self.invoice1.transaction_id, self.invoice1.l10n_ch_qrr
        )
