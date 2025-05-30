# Copyright 2024 Michele Rusticucci - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta
from unittest import mock

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

_module_ns = "odoo.addons.currency_rate_update_fta"
_file_ns = _module_ns + ".models.res_currency_rate_provider_fta"
_FTA_provider_class = _file_ns + ".ResCurrencyRateProviderFTA"


@tagged("post_install", "-at_install")
class TestCurrencyRateUpdateFTA(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Company = cls.env["res.company"]
        cls.CurrencyRateProvider = cls.env["res.currency.rate.provider"]

        cls.today = fields.Date.today()
        cls.chf_currency = cls.env.ref("base.CHF")
        cls.eur_currency = cls.env.ref("base.EUR")

        cls.company = cls.Company.create(
            {
                "name": "Test Company",
                "currency_id": cls.chf_currency.id,
            }
        )

        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company

        cls.fta_provider = cls.CurrencyRateProvider.create(
            {
                "service": "fta",
                "currency_ids": [(4, cls.chf_currency.id), (4, cls.eur_currency.id)],
            }
        )

    def test_obtain_rates_latest(self):
        today = self.today

        with mock.patch(
            _FTA_provider_class + "._get_latest_rate",
            return_value={today: {"USD": "1.1"}},
        ):
            result = self.fta_provider._obtain_rates("CHF", ["USD"], today, today)

        self.assertEqual(result, {today: {"USD": "1.1"}})

    def test_obtain_rates_historical(self):
        past_date = self.today - relativedelta(days=3)
        future_date = self.today - relativedelta(days=1)

        with mock.patch(
            _FTA_provider_class + "._get_historical_rate",
            return_value={past_date: {"EUR": "0.85"}, future_date: {"EUR": "0.87"}},
        ):
            result = self.fta_provider._obtain_rates(
                "CHF", ["EUR"], past_date, future_date
            )

        self.assertEqual(
            result, {past_date: {"EUR": "0.85"}, future_date: {"EUR": "0.87"}}
        )

    def test_obtain_rates_other_service(self):
        self.fta_provider.service = "none"

        with mock.patch(
            _FTA_provider_class + "._obtain_rates", return_value={"super_called": True}
        ):
            result = self.fta_provider._obtain_rates(
                "CHF", ["USD"], self.today, self.today
            )

        self.assertEqual(result, {"super_called": True})

    def test_request_data_wraps_exceptions(self):
        with mock.patch(f"{_file_ns}.requests.request", side_effect=Exception("fail")):
            with self.assertRaises(UserError):
                self.fta_provider._request_data("http://invalid")

    def test_parse_data_applies_divisor_and_filters(self):
        xml = """<?xml version="1.0"?>
        <xmldaily xmlns="https://www.backend-rates.ezv.admin.ch/xmldaily">
          <devise code="AAA">
            <kurs>200</kurs>
            <waehrung>2 CHF</waehrung>
          </devise>
          <devise code="BBB">
            <kurs>50</kurs>
            <waehrung>1 CHF</waehrung>
          </devise>
        </xmldaily>
        """
        mock_resp = mock.Mock()
        mock_resp.content = xml.encode()
        parsed = self.fta_provider._parse_data(mock_resp, ["AAA"])
        self.assertIn("AAA", parsed)
        self.assertEqual(parsed["AAA"], "100.0")
        self.assertNotIn("BBB", parsed)

    def test_get_latest_rate_calls_internal(self):
        fake_data = {"X": "9.99"}
        today = date.today()
        with mock.patch.object(
            self.fta_provider,
            "_request_data",
            return_value=mock.Mock(content=b"<dummy/>"),
        ) as mock_request, mock.patch.object(
            self.fta_provider, "_parse_data", return_value=fake_data
        ) as mock_parse:
            result = self.fta_provider._get_latest_rate("base_url", ["X"], "BASE")
        self.assertIn(today, result)
        self.assertEqual(result[today], fake_data)
        mock_request.assert_called_once_with("base_url")
        mock_parse.assert_called_once()

    def test_get_historical_rate_iterates_days(self):
        fake_data = {"Y": "0.42"}
        start = date.today() - timedelta(days=2)
        end = date.today() - timedelta(days=1)
        with mock.patch.object(
            self.fta_provider,
            "_request_data",
            return_value=mock.Mock(content=b"<dummy/>"),
        ) as mock_request, mock.patch.object(
            self.fta_provider, "_parse_data", return_value=fake_data
        ) as mock_parse:
            result = self.fta_provider._get_historical_rate(
                "base_url", ["Y"], start, end, "BASE"
            )
        expected_dates = [start, start + timedelta(days=1)]
        self.assertEqual(sorted(result.keys()), expected_dates)
        for dt in expected_dates:
            self.assertEqual(result[dt], fake_data)
        self.assertEqual(mock_request.call_count, len(expected_dates))
        self.assertEqual(mock_parse.call_count, len(expected_dates))
