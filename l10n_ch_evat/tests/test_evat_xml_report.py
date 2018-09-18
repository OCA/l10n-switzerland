# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime
from odoo import fields
from odoo.tests.common import TransactionCase, SavepointCase


class TestProdEvatXmlReport(TransactionCase):
    """
    Temporary test to run on prod db
    """
    def test_xml_generation(self):
        evat = self.env['evat.xml.report'].create({
            'name': 'Test 2018',
            'date_from': fields.Date.from_string('2018-01-01'),
            'date_to': fields.Date.from_string('2018-12-31'),
            'target_moves': 'posted',
            'type_of_submission': '1',
        })
        evat.generate_xml_report()


class TestEvatXmlReport(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestEvatXmlReport, cls).setUpClass()
        chart_template = cls.env.ref('l10n_ch.l10nch_chart_template')
        def_purchase_tax = cls.env.ref('l10n_ch.vat_77_purchase_incl')
        def_sale_tax = cls.env.ref('l10n_ch.vat_77_incl')
        # Install COA
        cls.env['account.config.settings'].create({
            'chart_template_id': chart_template.id,
            'purchase_tax_id': def_purchase_tax.id,
            'sale_tax_id': def_sale_tax.id,
        }).execute()

    def test_default_dates(self):
        evat = self.env['evat.xml.report']
        date_results = {
            '2018-01-01': {'from': '2017-10-01', 'to': '2017-12-31'},
            '2018-02-15': {'from': '2017-10-01', 'to': '2017-12-31'},
            '2018-03-31': {'from': '2017-10-01', 'to': '2017-12-31'},
            '2018-04-01': {'from': '2018-01-01', 'to': '2018-03-31'},
            '2018-05-15': {'from': '2018-01-01', 'to': '2018-03-31'},
            '2018-06-30': {'from': '2018-01-01', 'to': '2018-03-31'},
            '2018-07-01': {'from': '2018-04-01', 'to': '2018-06-30'},
            '2018-08-15': {'from': '2018-04-01', 'to': '2018-06-30'},
            '2018-09-30': {'from': '2018-04-01', 'to': '2018-06-30'},
            '2018-10-01': {'from': '2018-07-01', 'to': '2018-09-30'},
            '2018-11-15': {'from': '2018-07-01', 'to': '2018-09-30'},
            '2018-12-31': {'from': '2018-07-01', 'to': '2018-09-30'},
        }
        for base_date, res in date_results.iteritems():
            self.assertEqual(
                evat._default_date_from(datetime.strptime(base_date,
                                                          '%Y-%m-%d')),
                datetime.strptime(res.get('from'), '%Y-%m-%d').date()
            )
            self.assertEqual(
                evat._default_date_to(datetime.strptime(base_date,
                                                        '%Y-%m-%d')),
                datetime.strptime(res.get('to'), '%Y-%m-%d').date()
            )
