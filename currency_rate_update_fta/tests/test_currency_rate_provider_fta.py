# Copyright 2025 Michele Rusticucci
# License AGPL-3.0 or later

import xml.etree.ElementTree as ET
from datetime import date, timedelta
from unittest import mock

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

RQ = (
    "odoo.addons.currency_rate_update_fta.models."
    "res_currency_rate_provider_fta.requests.request"
)


def _xml(code, kurs, qty):
    return (
        '<?xml version="1.0"?>'
        '<xmldaily xmlns="https://www.backend-rates.ezv.admin.ch/xmldaily">'
        f'<devise code="{code}"><kurs>{kurs}</kurs><waehrung>{qty} CHF</waehrung>'
        "</devise></xmldaily>"
    ).encode()


@tagged("post_install", "-at_install")
class TestCurrencyRateFTA(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.Company = cls.env["res.company"]
        cls.Provider = cls.env["res.currency.rate.provider"]
        cls.chf = cls.env.ref("base.CHF")
        cls.eur = cls.env.ref("base.EUR")
        cls.company = cls.Company.create({"name": "TestCo", "currency_id": cls.chf.id})
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.provider = cls.Provider.create(
            {"service": "fta", "currency_ids": [(4, cls.chf.id), (4, cls.eur.id)]}
        )

    def test_obtain_rates_latest(self):
        resp = mock.Mock(content=_xml("USD", 110, 100))
        with mock.patch(RQ, return_value=resp) as req:
            got = self.provider._obtain_rates("CHF", ["USD"], self.today, self.today)
        self.assertEqual(got, {self.today: {"USD": "1.1"}})
        self.assertEqual(req.call_count, 1)

    def test_obtain_rates_historical(self):
        start = self.today - relativedelta(days=2)
        end = self.today - relativedelta(days=1)
        resp_start = mock.Mock(content=_xml("EUR", 85, 100))
        resp_end = mock.Mock(content=_xml("EUR", 87, 100))
        with mock.patch(RQ, side_effect=[resp_start, resp_end]) as req:
            got = self.provider._obtain_rates("CHF", ["EUR"], start, end)
        self.assertEqual(got, {start: {"EUR": "0.85"}, end: {"EUR": "0.87"}})
        self.assertEqual(req.call_count, 2)

    def test_obtain_rates_non_fta(self):
        self.provider.service = "none"
        parent = type(self.provider).__mro__[1]
        with mock.patch.object(parent, "_obtain_rates", return_value={"ok": True}) as m:
            got = self.provider._obtain_rates("CHF", ["USD"], self.today, self.today)
        m.assert_called_once_with("CHF", ["USD"], self.today, self.today)
        self.assertEqual(got, {"ok": True})

    def test_request_data(self):
        with mock.patch(RQ, side_effect=Exception):
            with self.assertRaises(UserError):
                self.provider._request_data("bad_url")
        mock_resp = mock.Mock()
        with mock.patch(RQ, return_value=mock_resp) as req:
            got = self.provider._request_data("url")
        self.assertIs(got, mock_resp)
        req.assert_called_once_with("GET", "url", timeout=10)

    def test_parse_data(self):
        xml = (
            '<?xml version="1.0"?>'
            '<xmldaily xmlns="https://www.backend-rates.ezv.admin.ch/xmldaily">'
            '<devise code="AAA"><kurs>200</kurs><waehrung>2 CHF</waehrung></devise>'
            '<devise code="BBB"><kurs>50</kurs><waehrung>1 CHF</waehrung></devise>'
            "</xmldaily>"
        )
        resp = mock.Mock(content=xml.encode())
        self.assertEqual(self.provider._parse_data(resp, ["AAA"]), {"AAA": "100.0"})
        with self.assertRaises(ET.ParseError):
            bad = mock.Mock(content=b"<nope")
            self.provider._parse_data(bad, ["EUR"])

    def test_get_latest_and_historical(self):
        today = date.today()
        resp_today = mock.Mock(content=_xml("X", 999, 100))  # 9.99
        start = today - timedelta(days=2)
        end = today - timedelta(days=1)
        resp_start = mock.Mock(content=_xml("Y", 111, 100))  # 1.11
        resp_end = mock.Mock(content=_xml("Y", 222, 100))  # 2.22
        with mock.patch(RQ, return_value=resp_today):
            latest = self.provider._get_latest_rate("u", ["X"], "B")
        self.assertEqual(latest, {today: {"X": "9.99"}})
        with mock.patch(RQ, side_effect=[resp_start, resp_end]) as req:
            hist = self.provider._get_historical_rate("u", ["Y"], start, end, "B")
        self.assertEqual(hist[start], {"Y": "1.11"})
        self.assertEqual(hist[end], {"Y": "2.22"})
        self.assertEqual(req.call_count, 2)

    def test_historical_empty(self):
        res = self.provider._get_historical_rate(
            "u", ["Z"], self.today, self.today - timedelta(days=1), "C"
        )
        self.assertEqual(res, {})

    def test_multiple_providers(self):
        other = self.Company.create({"name": "O", "currency_id": self.chf.id})
        self.env.user.company_ids |= other
        dup = self.Provider.create(
            {
                "service": "fta",
                "company_id": other.id,
                "currency_ids": [(4, self.chf.id)],
            }
        )
        with self.assertRaises(ValueError):
            (self.provider | dup)._obtain_rates("CHF", ["USD"], self.today, self.today)

    def test_single_fta_call(self):
        self.provider.service = "fta"
        resp = mock.Mock(content=_xml("USD", 110, 100))
        with mock.patch(RQ, return_value=resp) as req:
            self.provider._obtain_rates("CHF", ["USD"], self.today, self.today)
        self.assertEqual(req.call_count, 1)

    def test_service_field(self):
        fld = self.Provider._fields["service"]
        self.assertIn("fta", dict(fld.selection))
        self.assertEqual(fld.ondelete.get("fta"), "set default")
