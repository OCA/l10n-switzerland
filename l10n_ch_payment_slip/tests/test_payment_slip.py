# Copyright 2014-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time
import re
import logging
from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestPaymentSlip(common.SavepointCase):
    _compile_get_ref = re.compile(r'[^0-9]')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.report1slip_from_inv = cls.env.ref(
            'l10n_ch_payment_slip.one_slip_per_page_from_invoice',
        )

    def make_bank(self):
        company = self.env.ref('base.main_company')
        self.assertTrue(company)
        partner = self.env.ref('base.main_partner')
        self.assertTrue(partner)
        bank = self.env['res.bank'].create(
            {
                'name': 'BCV',
                'bic': 'BBRUBEBB',
                'clearing': '234234',
            }
        )
        bank_account = self.env['res.partner.bank'].create(
            {
                'partner_id': partner.id,
                'bank_id': bank.id,
                'bank_bic': bank.bic,
                'acc_number': 'ISR account',
                'l10n_ch_isr_subscription_chf': '01-1234-1',
                'l10n_ch_isrb_id_number': '123456',
                'print_bank': True,
                'print_account': True,
                'print_partner': True,
                'sequence': 1,
            }
        )
        return bank_account

    def make_invoice(self):
        if not hasattr(self, 'bank_account'):
            self.bank_account = self.make_bank()
        account_model = self.env['account.account']
        account_debtor = account_model.search([('code', '=', '1100')])
        if not account_debtor:
            account_debtor = account_model.create({
                'code': 1100,
                'name': 'Debitors',
                'user_type_id':
                    self.env.ref('account.data_account_type_receivable').id,
                'reconcile': True,
            })
        account_sale = account_model.search([('code', '=', '3200')])
        if not account_sale:
            account_sale = account_model.create({
                'code': 3200,
                'name': 'Goods sales',
                'user_type_id':
                    self.env.ref('account.data_account_type_revenue').id,
                'reconcile': False,
            })

        invoice = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_12').id,
            'name': 'A customer invoice',
            'account_id': account_debtor.id,
            'type': 'out_invoice',
            'partner_bank_id': self.bank_account.id
        })

        self.env['account.invoice.line'].create({
            'account_id': account_sale.id,
            'product_id': False,
            'quantity': 1,
            'price_unit': 862.50,
            'invoice_id': invoice.id,
            'name': 'product that cost 862.50 all tax included',
        })
        invoice.action_invoice_open()
        # waiting for the cache to refresh
        attempt = 0
        while not invoice.move_id:
            invoice.refresh()
            time.sleep(0.1)
            attempt += 1
            if attempt > 20:
                break
        return invoice

    def test_invoice_confirmation(self):
        """Test that confirming an invoice generate slips correctly"""
        invoice = self.make_invoice()
        self.assertTrue(invoice.move_id)
        self.assertTrue(invoice.move_id.ref)
        self.assertEqual(
            invoice.isr_reference.replace(' ', ''), invoice.move_id.ref
        )
        for line in invoice.move_id.line_ids:
            slip = self.env['l10n_ch.payment_slip'].search(
                [('move_line_id', '=', line.id)]
            )
            if line.account_id.user_type_id.type in ('payable', 'receivable'):
                self.assertTrue(slip)
                self.assertEqual(slip.amount_total, 862.50)
                self.assertEqual(slip.invoice_id.id, invoice.id)
            else:
                self.assertFalse(slip)

    def test_slip_validity(self):
        """Test that confirming slip are valid"""
        invoice = self.make_invoice()
        self.assertTrue(invoice.move_id)
        for line in invoice.move_id.line_ids:
            slip = self.env['l10n_ch.payment_slip'].search(
                [('move_line_id', '=', line.id)]
            )
            if line.account_id.user_type_id.type in ('payable', 'receivable'):
                self.assertTrue(slip.reference)
                self.assertTrue(slip.scan_line)
                self.assertTrue(slip.slip_image)
                self.assertTrue(slip.a4_pdf)
                inv_num = line.invoice_id.number
                line_ident = self._compile_get_ref.sub(
                    '', "%s%s" % (inv_num, line.id)
                )
                self.assertIn(line_ident, slip.reference.replace(' ', ''))

    def test_isr_reference(self):
        # no partner ref
        self.env.ref('base.res_partner_12').ref = ''
        invoice = self.make_invoice()
        self.assertTrue(invoice.isr_reference)
        reference = invoice.isr_reference.replace(' ', '')
        self.assertEqual(len(reference), 27)
        self.assertEqual(reference[:6], '123456')
        self.assertEqual(reference[6:13], '0' * 7)

        # standard
        self.env.ref('base.res_partner_12').ref = '12345'
        invoice = self.make_invoice()
        self.assertTrue(invoice.isr_reference)
        reference = invoice.isr_reference.replace(' ', '')
        self.assertEqual(len(reference), 27)
        self.assertEqual(reference[:6], '123456')
        self.assertEqual(reference[6:13], '0012345')

        # partner ref without num
        self.env.ref('base.res_partner_12').ref = 'alpha'
        invoice = self.make_invoice()
        self.assertTrue(invoice.isr_reference)
        reference = invoice.isr_reference.replace(' ', '')
        self.assertEqual(len(reference), 27)
        self.assertEqual(reference[:6], '123456')
        self.assertEqual(reference[6:13], '0' * 7)

        # contains alphanumerics
        self.env.ref('base.res_partner_12').ref = 'alpha123'
        invoice = self.make_invoice()
        self.assertTrue(invoice.isr_reference)
        reference = invoice.isr_reference.replace(' ', '')
        self.assertEqual(len(reference), 27)
        self.assertEqual(reference[:6], '123456')
        self.assertEqual(reference[6:13], '0000123')

        # partner_ref too long
        self.env.ref('base.res_partner_12').ref = '0987654321'
        invoice = self.make_invoice()
        self.assertTrue(invoice.isr_reference)
        reference = invoice.isr_reference.replace(' ', '')
        self.assertEqual(len(reference), 27)
        self.assertEqual(reference[:6], '123456')
        self.assertEqual(reference[6:13], '7654321')

        # customer id with more chars
        invoice.partner_bank_id.l10n_ch_isrb_id_number = '123456789'
        self.env.ref('base.res_partner_12').ref = '12345'
        invoice = self.make_invoice()
        self.assertTrue(invoice.isr_reference)
        reference = invoice.isr_reference.replace(' ', '')
        self.assertEqual(len(reference), 27)
        self.assertEqual(reference[:9], '123456789')
        self.assertEqual(reference[9:16], '0012345')

    def test_print_report(self):
        invoice = self.make_invoice()
        data, format_report = self.report1slip_from_inv.render(invoice.id)
        self.assertTrue(data)
        self.assertEqual(format_report, 'pdf')

    def test_print_multi_report_merge_in_memory(self):
        # default value as in memory
        self.assertEqual(self.env.user.company_id.merge_mode, 'in_memory')
        invoice1 = self.make_invoice()
        invoice2 = self.make_invoice()
        data, format_report = self.report1slip_from_inv.render(
            [invoice1.id, invoice2.id])
        self.assertTrue(data)
        self.assertEqual(format_report, 'pdf')

    def test_print_multi_report_merge_on_disk(self):
        self.env.user.company_id.merge_mode = 'on_disk'
        invoice1 = self.make_invoice()
        invoice2 = self.make_invoice()
        data, format_report = self.report1slip_from_inv.render(
            [invoice1.id, invoice2.id])
        self.assertTrue(data)
        self.assertEqual(format_report, 'pdf')

    def test_address_format(self):
        invoice = self.make_invoice()
        self.assertTrue(invoice.move_id)
        line = invoice.move_id.line_ids[0]
        slip = self.env['l10n_ch.payment_slip'].search(
            [('move_line_id', '=', line.id)]
        )
        com_partner = slip.get_comm_partner()
        address_lines = slip._get_address_lines(com_partner.id)
        self.assertEqual(
            address_lines,
            ['3404  Edgewood Road', '', '72401 Jonesboro']
        )

    def test_address_format_user_demo(self):
        invoice = self.make_invoice()
        self.assertTrue(invoice.move_id)
        line = invoice.move_id.line_ids[0]
        slip = self.env['l10n_ch.payment_slip'].search(
            [('move_line_id', '=', line.id)]
        )
        com_partner = slip.get_comm_partner()
        demo_user = self.env.ref('base.user_demo')
        address_lines = slip.sudo(demo_user)._get_address_lines(com_partner.id)
        self.assertEqual(
            address_lines,
            ['3404  Edgewood Road', '', '72401 Jonesboro']
        )

    def test_address_format_no_country(self):
        invoice = self.make_invoice()
        self.assertTrue(invoice.move_id)
        line = invoice.move_id.line_ids[0]
        slip = self.env['l10n_ch.payment_slip'].search(
            [('move_line_id', '=', line.id)]
        )
        com_partner = slip.get_comm_partner()
        com_partner.country_id = False
        address_lines = slip._get_address_lines(com_partner.id)
        self.assertEqual(
            address_lines,
            ['3404  Edgewood Road', '', '72401 Jonesboro']
        )

    def test_address_format_special_format(self):
        """ Test special formating without street2 """

        ICP = self.env['ir.config_parameter']
        ICP.set_param(
            'isr.address.format',
            "%(street)s\n%(zip)s %(city)s"
        )
        invoice = self.make_invoice()
        self.assertTrue(invoice.move_id)
        line = invoice.move_id.line_ids[0]
        slip = self.env['l10n_ch.payment_slip'].search(
            [('move_line_id', '=', line.id)]
        )
        com_partner = slip.get_comm_partner()
        com_partner.country_id = False
        address_lines = slip._get_address_lines(com_partner.id)
        self.assertEqual(
            address_lines,
            ['3404  Edgewood Road', '72401 Jonesboro']
        )

    def test_address_length(self):
        invoice = self.make_invoice()
        self.assertTrue(invoice.move_id)
        line = invoice.move_id.line_ids[0]
        slip = self.env['l10n_ch.payment_slip'].search(
            [('move_line_id', '=', line.id)]
        )
        com_partner = slip.get_comm_partner()
        address_lines = slip._get_address_lines(com_partner.id)
        f_size = 11

        len_tests = [
            (15, (11, None)),
            (23, (11, None)),
            (26, (10, None)),
            (27, (10, None)),
            (30, (9, None)),
            (32, (8, 34)),
            (34, (8, 34)),
            (40, (8, 34))]

        for text_len, result in len_tests:
            com_partner.name = 'x' * text_len
            res = slip._get_address_font_size(
                f_size, address_lines, com_partner)

            self.assertEqual(res, result, "Wrong result for len %s" % text_len)

    def test_print_isr(self):
        invoice = self.make_invoice()
        isr = invoice.print_isr()
        self.assertEqual(isr['report_name'],
                         'l10n_ch_payment_slip.one_slip_per_page_from_invoice')
        self.assertEqual(isr['report_file'],
                         'l10n_ch_payment_slip.one_slip_per_page')

    def test_reload_from_attachment(self):

        def _find_invoice_attachment(self, invoice):
            return self.env['ir.attachment'].search([
                ('res_model', '=', invoice._name),
                ('res_id', '=', invoice.id)
            ])

        ActionReport = self.env['ir.actions.report']
        invoice = self.make_invoice()
        report_name = 'l10n_ch_payment_slip.one_slip_per_page_from_invoice'
        report_payment_slip = ActionReport._get_report_from_name(report_name)
        bvr_action = invoice.print_isr()
        # Print the report a first time
        act_report = report_payment_slip.with_context(bvr_action['context'])
        pdf = act_report.render_reportlab_pdf(res_ids=invoice.ids)
        # Ensure no attachment was stored
        attachment = _find_invoice_attachment(self, invoice)
        self.assertEqual(len(attachment), 0)
        # Set the report to store and reload from attachment
        report_payment_slip.write({
            'attachment_use': True,
            'attachment':
                "('ESR'+(object.number or '').replace('/','')+'.pdf')"
        })
        # Print the report again
        pdf1 = act_report.render_reportlab_pdf(res_ids=invoice.ids)
        # Ensure pdf is the same
        self.assertEqual(pdf, pdf1)
        # Ensure attachment was stored
        attachment1 = _find_invoice_attachment(self, invoice)
        self.assertEqual(len(attachment1), 1)
        # Print the report another time
        pdf2 = act_report.render_reportlab_pdf(res_ids=invoice.ids)
        # Ensure pdf and attachment are the same as before
        attachment2 = _find_invoice_attachment(self, invoice)
        self.assertEqual(len(attachment2), 1)
        self.assertEqual(pdf1, pdf2)
        self.assertEqual(attachment1, attachment2)
        # Allow cancelling entries on the journal
        invoice.journal_id.update_posted = True
        # Cancel the invoice and set back to draft
        invoice.action_invoice_cancel()
        invoice.action_invoice_draft()
        # Ensure attachment was unlinked
        attachment = _find_invoice_attachment(self, invoice)
        self.assertEqual(len(attachment), 0)
