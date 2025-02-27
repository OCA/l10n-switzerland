# Copyright 2024 Michele Rusticucci - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest import mock

from dateutil.relativedelta import relativedelta

from odoo import fields
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
