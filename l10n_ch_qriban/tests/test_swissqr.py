# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import time

from odoo.addons.account.tests.account_test_no_chart import TestAccountNoChartCommon

CH_IBAN = 'CH15 3881 5158 3845 3843 7'
QR_IBAN = 'CH21 3080 8001 2345 6782 7'


class TestSwissQR(TestAccountNoChartCommon):

    @classmethod
    def setUpClass(cls):
        super(TestSwissQR, cls).setUpClass()

        cls.setUpAccountJournal()

        # Activate SwissQR in Swiss invoices
        cls.env['ir.config_parameter'].create(
            {'key': 'l10n_ch.print_qrcode', 'value': '1'}
        )
        cls.customer = cls.env['res.partner'].create(
            {
                "name": "Partner",
                "street": "Route de Berne 41",
                "street2": "",
                "zip": "1000",
                "city": "Lausanne",
                "country_id": cls.env.ref("base.ch").id,
            }
        )
        cls.env.user.company_id.invoice_reference_type = "ch_isr"
        cls.env.user.company_id.partner_id.write(
            {
                "street": "Route de Berne 88",
                "street2": "",
                "zip": "2000",
                "city": "Neuchâtel",
                "country_id": cls.env.ref('base.ch').id,
            }
        )
        cls.invoice1 = cls.create_invoice('base.CHF')

    @classmethod
    def create_invoice(cls, currency_to_use='base.CHF'):
        """ Generates a test invoice """

        product = cls.env.ref("product.product_product_4")
        acc_type = cls.env.ref('account.data_account_type_current_assets')
        account = cls.env['account.account'].search(
            [('user_type_id', '=', acc_type.id)], limit=1
        )
        invoice = (
            cls.env['account.invoice']
            .with_context(default_type='out_invoice')
            .create(
                {
                    'type': 'out_invoice',
                    'partner_id': cls.customer.id,
                    'currency_id': cls.env.ref(currency_to_use).id,
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

    def swissqr_not_generated(self, invoice):
        """ Prints the given invoice and tests that no Swiss QR generation
        is triggered. """
        self.assertFalse(
            invoice.can_generate_qr_bill(),
            'No Swiss QR should be generated for this invoice',
        )

    def swissqr_generated(self, invoice, ref_type='NON'):
        """ Prints the given invoice and tests that a Swiss QR generation
        is triggered. """
        self.assertTrue(
            invoice.can_generate_qr_bill(), 'A Swiss QR can be generated'
        )

        if ref_type == 'QRR':
            self.assertTrue(invoice.reference)
            struct_ref = invoice.reference
            unstr_msg = invoice.name or ''
        else:
            struct_ref = ''
            unstr_msg = (
                invoice.reference or
                invoice.name or
                ''
            )
        unstr_msg = (unstr_msg or invoice.number).replace('/', '%2F')

        payload = (
            "SPC%0A"
            "0200%0A"
            "1%0A"
            "{iban}%0A"
            "K%0A"
            "YourCompany%0A"
            # "Route+de+Berne+88%0A" has extra + which seems unrelevant
            "Route+de+Berne+88+%0A"
            "2000+Neuch%C3%A2tel%0A"
            "%0A%0A"
            "CH%0A"
            "%0A%0A%0A%0A%0A%0A%0A"
            "42.00%0A"
            "CHF%0A"
            "K%0A"
            "Partner%0A"
            # "Route+de+Berne+41%0A" has extra + which seems unrelevant
            "Route+de+Berne+41+%0A"
            "1000+Lausanne%0A"
            "%0A%0A"
            "CH%0A"
            "{ref_type}%0A"
            "{struct_ref}%0A"
            "{unstr_msg}%0A"
            "EPD"
        ).format(
            iban=invoice.partner_bank_id.sanitized_acc_number,
            ref_type=ref_type,
            struct_ref=struct_ref or '',
            unstr_msg=unstr_msg,
        )

        expected_url = ("/report/barcode/?type=QR_quiet&value={}"
                        "&width=256&height=256&humanreadable=1").format(payload)

        url = invoice.partner_bank_id.build_swiss_code_url(
            invoice.amount_total,
            invoice.currency_id.name,
            None,
            invoice.partner_id,
            None,
            invoice.reference,
            invoice.name or invoice.number,
        )
        self.assertEqual(url, expected_url)

    def test_swissQR_missing_bank(self):
        # Let us test the generation of a SwissQR for an invoice, first by
        # showing a QR is included in the invoice is only generated when Odoo
        # has all the data it needs.
        self.invoice1.action_invoice_open()
        self.swissqr_not_generated(self.invoice1)

    def test_swissQR_iban(self):
        # Now we add an account for payment to our invoice
        # Here we don't use a structured reference
        iban_account = self.create_account(CH_IBAN)
        self.invoice1.partner_bank_id = iban_account
        self.invoice1.action_invoice_open()
        self.swissqr_generated(self.invoice1, ref_type="NON")

    def test_swissQR_qriban(self):
        # Now use a proper QR-IBAN, we are good to print a QR Bill
        qriban_account = self.create_account(QR_IBAN)
        self.assertTrue(qriban_account.acc_type, 'qr-iban')
        self.invoice1.partner_bank_id = qriban_account
        self.invoice1.action_invoice_open()
        self.swissqr_generated(self.invoice1, ref_type="QRR")
