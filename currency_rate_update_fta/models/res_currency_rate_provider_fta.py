# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import xml.etree.ElementTree as ET
from datetime import date, timedelta

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError


class ResCurrencyRateProviderFTA(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("fta", "Federal Tax Administration (Switzerland)")],
        ondelete={"fta": "set default"},
    )

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "fta":
            return super()._obtain_rates(base_currency, currencies, date_from, date_to)
        base_url = "https://www.backend-rates.bazg.admin.ch/api/xmldaily"
        if date_from < date.today():
            return self._get_historical_rate(
                base_url, currencies, date_from, date_to, base_currency
            )
        else:
            return self._get_latest_rate(base_url, currencies, base_currency)

    def _get_latest_rate(self, base_url, currencies, base_currency):
        """Get all the exchange rates for today"""
        url = f"{base_url}"
        data = self._request_data(url)
        return {date.today(): self._parse_data(data, currencies)}

    def _get_historical_rate(
        self, base_url, currencies, date_from, date_to, base_currency
    ):
        """Get all the exchange rates from 'date_from' to 'date_to'"""
        content = {}
        current_date = date_from
        while current_date <= date_to:
            url = f"{base_url}/?d={current_date.strftime('%Y%m%d')}"
            data = self._request_data(url)
            content[current_date] = self._parse_data(data, currencies)
            current_date += timedelta(days=1)
        return content

    def _request_data(self, url):
        try:
            return requests.request("GET", url, timeout=10)
        except Exception as e:
            raise UserError(
                _("Couldn't fetch data. Please contact your administrator.")
            ) from e

    def _parse_data(self, data, currencies):
        result = {}
        root = ET.fromstring(data.content)
        namespace = {"ns": "https://www.backend-rates.ezv.admin.ch/xmldaily"}
        for devise in root.findall("ns:devise", namespace):
            currency_code = devise.get("code").upper()
            if currency_code in currencies:
                rate = devise.find("ns:kurs", namespace).text
                div = devise.find("ns:waehrung", namespace).text
                div_list = div.split(" ")
                divisor = int(div_list[0])
                rate_float = float(rate)
                result[currency_code] = str(rate_float / divisor)
        return result
