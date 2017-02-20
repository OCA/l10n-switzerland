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


class TestBank(TransactionCase):

    def setUp(self):
        super(TestBank, self).setUp()
        self.context = {}

        self.res_bank_obj = self.env['res.partner.bank']
        self.bank_obj = self.env['res.bank']

        self.correct_length_dd = 6
        self.correct_length_lsv = 5

    # Begin: Tests for is_post_dd_ident_valid
    def test_dd_identifier_not_valid_not_string(self):
        # cr, uid, context = self.cr, self.uid, self.context
        self.assertFalse(self.res_bank_obj.is_post_dd_ident_valid([]))

    def test_dd_identifier_not_valid_not_ascii(self):
        with self.assertRaises(exceptions.ValidationError):
            self.res_bank_obj.is_post_dd_ident_valid("\x81")

    def test_dd_identifier_not_valid_bad_length(self):
        self.assertFalse(self.res_bank_obj.is_post_dd_ident_valid(
            "1" * (self.correct_length_dd - 1)))
        self.assertFalse(self.res_bank_obj.is_post_dd_ident_valid(
            "1" * (self.correct_length_dd + 1)))

    def test_dd_identifier_not_valid_bad_mod10r(self):
        self.assertFalse(self.res_bank_obj.is_post_dd_ident_valid("123456"))

    def test_dd_identifier_valid(self):
        self.assertTrue(self.res_bank_obj.is_post_dd_ident_valid("123457"))
    # End: Tests for is_post_dd_ident_valid

    # Begin: Tests for is_lsv_identifier_valid
    def test_lsv_identifier_not_valid_not_string(self):
        self.assertFalse(self.res_bank_obj.is_lsv_identifier_valid([]))

    def test_lsv_identifier_not_valid_not_ascii(self):
        with self.assertRaises(exceptions.ValidationError):
            self.res_bank_obj.is_lsv_identifier_valid("\x81")

    def test_lsv_identifier_not_valid_bad_length(self):
        self.assertFalse(self.res_bank_obj.is_lsv_identifier_valid(
            "1" * (self.correct_length_lsv - 1)))
        self.assertFalse(self.res_bank_obj.is_lsv_identifier_valid(
            "1" * (self.correct_length_lsv + 1)))

    def test_lsv_identifier_valid(self):
        self.assertTrue(self.res_bank_obj.is_lsv_identifier_valid(
            "1" * self.correct_length_lsv))
    # End: Tests for is_lsv_identifier_valid
