# -*- coding: utf-8 -*-
##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2017 brain-tec AG (http://www.braintec-group.com)
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

from openerp.tests import TransactionCase
from openerp import exceptions
from collections import namedtuple


# To mock a payment line.
PaymentLineMockUp = namedtuple("PaymentLineMock", "amount_currency name")


class TestLsvExportWizard(TransactionCase):

    def setUp(self):
        super(TestLsvExportWizard, self).setUp()
        self.context = {}

        self.lsv_wiz = self.env['lsv.export.wizard']

        self.one_cent = 0.01
        self.rate = 1.0
        self.max_amount_lsv_chf = 99999999.99
        self.max_amount_lsv_eur = 99999999.99 / self.rate

    # Begin: Tests for _check_amount().
    def test_check_amount_negative_amount(self):
        line = PaymentLineMockUp(-1, "_")
        with self.assertRaises(exceptions.ValidationError):
            self.lsv_wiz._check_amount(line, {})

    def test_check_amount_overflow_amount_chf(self):
        try:
            line = PaymentLineMockUp(self.max_amount_lsv_chf, "negative_line")
            self.lsv_wiz._check_amount(line, {'currency': 'CHF'})
        except exceptions.ValidationError:
            self.fail("_check_amount() for lsv.export.wizard raised "
                      "exceptions.ValidationError unexpectedly!")

        with self.assertRaises(exceptions.ValidationError):
            overflow_line_chf = PaymentLineMockUp(
                self.max_amount_lsv_chf + self.one_cent, "overflow_chf_line")
            self.lsv_wiz._check_amount(
                overflow_line_chf, {'currency': 'CHF'})

    def test_check_amount_overflow_amount_eur(self):
        try:
            line = PaymentLineMockUp(self.max_amount_lsv_eur, "negative_line")
            self.lsv_wiz._check_amount(line, {'currency': 'EUR',
                                              'rate': self.rate})
        except exceptions.ValidationError:
            self.fail("_check_amount() for lsv.export.wizard raised "
                      "exceptions.ValidationError unexpectedly!")

        with self.assertRaises(exceptions.ValidationError):
            overflow_line_eur = PaymentLineMockUp(
                self.max_amount_lsv_eur + self.one_cent, "overflow_eur_line")
            self.lsv_wiz._check_amount(overflow_line_eur, {'currency': 'EUR',
                                                           'rate': self.rate})
    # End: Tests for _check_amount().
