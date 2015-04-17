# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import types
import time
import StringIO
from contextlib import contextmanager, closing
import re
from mock import patch, MagicMock
from reportlab.pdfgen.canvas import Canvas

import openerp.tests.common as test_common


def make_pdf():
    canvas_size = (595.27, 841.89)
    with closing(StringIO.StringIO()) as buff:
        canvas = Canvas(buff,
                        pagesize=canvas_size,
                        pageCompression=None)
        canvas.showPage()
        canvas.save()
        return buff.getvalue()


@contextmanager
def mock_render_report():
    render = ('openerp.addons.l10n_ch_payment_slip.report.ir_action.'
              'ir_actions_report_xml_reportlab.render_report')
    pdf_mock = MagicMock()
    pdf_mock.side_effect = [(make_pdf(), 'pdf')]
    with patch(render, pdf_mock):
        yield


class TestPaymentSlipLayout(test_common.TransactionCase):
    _compile_get_ref = re.compile(r'[^0-9]')

    def setUp(self):
        super(TestPaymentSlipLayout, self).setUp()
        company = self.env.ref('base.main_company')
        self.assertTrue(company)
        partner = self.env.ref('base.main_partner')
        self.assertTrue(partner)
        bank = self.env['res.bank'].create(
            {
                'name': 'BCV',
                'ccp': '01-1234-1',
                'bic': '234234',
                'clearing': '234234',
            }
        )
        self.bank_account = self.env['res.partner.bank'].create(
            {
                'partner_id': partner.id,
                'owner_name': partner.name,
                'street':  partner.street,
                'city': partner.city,
                'zip':  partner.zip,
                'state': 'bvr',
                'bank': bank.id,
                'bank_name': bank.name,
                'bank_bic': bank.bic,
                'acc_number': 'R 12312123',
                'bvr_adherent_num': '1234567',
                'print_bank': True,
                'print_account': True,
                'print_partner': True,
            }
        )

        self.invoice = self.env['account.invoice'].create(
            {
                'partner_id': self.env.ref('base.res_partner_12').id,
                'reference_type': 'none',
                'name': 'A customer invoice',
                'account_id': self.env.ref('account.a_recv').id,
                'type': 'out_invoice',
                'partner_bank_id': self.bank_account.id
            }
        )

        self.env['account.invoice.line'].create(
            {
                'product_id': False,
                'quantity': 1,
                'price_unit': 862.50,
                'invoice_id': self.invoice.id,
                'name': 'product that cost 862.50 all tax included',
            }
        )
        self.invoice.signal_workflow('invoice_open')
        # We wait the invoice line cache to be refreshed
        attempt = 0
        while not self.invoice.move_id:
            self.invoice.refresh()
            time.sleep(0.1)
            attempt += 1
            if attempt > 20:
                break

    def test_report_generator(self):
        with mock_render_report():
            # registry is used in order to avoid decorator hell
            gen = self.registry['report']._compute_documents_list(
                self.env.cr,
                self.env.uid,
                [self.invoice.id],
                context={}
            )
            self.assertIsInstance(gen, types.GeneratorType)
            pdfs = [x for x in gen]
            self.assertTrue(len(pdfs) == 2)

    def test_report_generator_merge(self):
        with mock_render_report():
            # registry is used in order to avoid decorator hell
            gen = self.registry['report']._compute_documents_list(
                self.env.cr,
                self.env.uid,
                [self.invoice.id],
                context={}
            )
            self.assertIsInstance(gen, types.GeneratorType)
            self.env['report'].merge_pdf_in_memory(gen)

        with mock_render_report():
            # registry is used in order to avoid decorator hell
            gen = self.registry['report']._compute_documents_list(
                self.env.cr,
                self.env.uid,
                [self.invoice.id],
                context={}
            )
            self.assertIsInstance(gen, types.GeneratorType)
            self.env['report'].merge_pdf_on_disk(gen)
