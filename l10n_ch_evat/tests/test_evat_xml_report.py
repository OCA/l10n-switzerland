# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.tests.common import TransactionCase


class TestEvatXmlReport(TransactionCase):

    def test_xml_generation(self):
        evat = self.env['evat.xml.report'].create({
            'name': 'Test 2018',
            'start_date': fields.Date.from_string('2018-01-01'),
            'end_date': fields.Date.from_string('2018-12-31'),
            'target_moves': 'posted',
            'type_of_submission': '1',
        })
        evat.generate_xml_report()
