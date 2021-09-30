# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
from openerp.tests.common import HttpCase

CH_IBAN = 'CH15 3881 5158 3845 3843 7'
QR_IBAN = 'CH21 3080 8001 2345 6782 7'


class TestSwissQR(HttpCase):

    def setUp(self):
        super(TestSwissQR, self).setUp()
        domain = [('company_id', '=', self.env.ref('base.main_company').id)]
        if not self.env['account.account'].search_count(domain):
            self.skipTest("No Chart of account found")

        # Activate SwissQR in Swiss invoices
        self.env['ir.config_parameter'].create(
            {'key': 'l10n_ch.print_qrcode', 'value': '1'}
        )
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

    def create_invoice(self, currency_to_use='base.CHF'):
        """ Generates a test invoice """

        product = self.env.ref("product.product_product_4")
        acc_type = self.env.ref('account.data_account_type_bank')
        account = self.env['account.account'].create({
            'name': 'Test account for QR-bill',
            'code': 'TESTQR',
            'type': 'other',
            'user_type': acc_type.id
            })
        invoice = (
            self.env['account.invoice']
            .with_context(default_type='out_invoice')
            .create(
                {
                    'type': 'out_invoice',
                    'partner_id': self.customer.id,
                    'currency_id': self.env.ref(currency_to_use).id,
                    'account_id': account.id,
                    'date_invoice': time.strftime('%Y') + '-12-22',
                    'invoice_line': [
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
                'state': 'iban'
            }
        )

    def swissqr_not_generated(self, invoice):
        """Prints the given invoice and tests that no Swiss QR generation is triggered.

        """
        self.assertFalse(
            invoice.validate_swiss_code_arguments(),
            'No Swiss QR should be generated for this invoice',
        )

    def swissqr_generated(self, invoice, ref_type='NON'):
        """Prints the given invoice and tests that a Swiss QR generation is triggered.

        """
        self.assertTrue(
            invoice.validate_swiss_code_arguments(), 'A Swiss QR can be generated'
        )
        if ref_type == 'QRR':
            struct_ref = invoice.l10n_ch_qrr
            unstr_msg = invoice.number
        else:
            struct_ref = ''
            unstr_msg = invoice.name or ''
        acc_number = invoice.partner_bank_id.acc_number
        iban = invoice.partner_bank_id._sanitize_account_number(acc_number)
        unstr_msg = (unstr_msg or invoice.number).replace('/', '%2F')
        payload = (
            "SPC%0A"
            "0200%0A"
            "1%0A"
            "{iban}%0A"
            "K%0A"
            "YourCompany%0A"
            "Route+de+Berne+88%0A"
            "2000+Neuch%C3%A2tel%0A"
            "%0A%0A"
            "CH%0A"
            "%0A%0A%0A%0A%0A%0A%0A"
            "42.00%0A"
            "CHF%0A"
            "K%0A"
            "Partner%0A"
            "Route+de+Berne+41%0A"
            "1000+Lausanne%0A"
            "%0A%0A"
            "CH%0A"
            "{ref_type}%0A"
            "{struct_ref}%0A"
            "{unstr_msg}%0A"
            "EPD%0A"
        ).format(
            iban=iban,
            ref_type=ref_type,
            struct_ref=struct_ref,
            unstr_msg=unstr_msg,
        )

        expected_url = ("/report/qrcode/?value={}"
                        "&width=256&height=256&bar_border=0").format(payload)

        url = invoice.build_swiss_code_url()
        self.assertEqual(url, expected_url)

    def test_swissQR_missing_bank(self):
        # Let us test the generation of a SwissQR for an invoice, first by showing an
        # QR is included in the invoice is only generated when Odoo has all the data
        # it needs.
        self.invoice1.invoice_validate()
        self.swissqr_not_generated(self.invoice1)

    def test_swissQR_iban(self):
        # Now we add an account for payment to our invoice
        # Here we don't use a structured reference
        iban_account = self.create_account(CH_IBAN)
        self.invoice1.partner_bank_id = iban_account
        self.invoice1.invoice_validate()
        self.invoice1.action_move_create()
        self.swissqr_generated(self.invoice1, ref_type="NON")

    def test_swissQR_qriban(self):
        # Now use a proper QR-IBAN, we are good to print a QR Bill
        qriban_account = self.create_account(QR_IBAN)
        self.assertTrue(qriban_account._is_qr_iban())
        self.invoice1.partner_bank_id = qriban_account
        self.invoice1.reference_type = 'QRR'
        self.invoice1.invoice_validate()
        self.invoice1.action_move_create()
        self.swissqr_generated(self.invoice1, ref_type="QRR")
