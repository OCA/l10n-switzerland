# Copyright 2012 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression

from .. import postfinance


class Bank(models.Model):
    _inherit = "res.bank"

    code = fields.Char(help="Internal reference")
    clearing = fields.Char(
        string="Clearing number",
        help="Swiss unique bank identifier also used in IBAN number",
    )
    city = fields.Char(help="City of the bank")
    country_code = fields.Char(
        string="Country code", related="country.code", readonly=True
    )

    def is_swiss_post(self):
        return self.bic == postfinance.BIC

    def name_get(self):
        """Format displayed name"""
        res = []
        cols = ("bic", "name", "street", "city")
        for bank in self:
            vals = (bank[x] for x in cols if bank[x])
            res.append((bank.id, " - ".join(vals)))
        return res

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        # OVERRIDE to search also on ``code``, ``street`` and ``city``
        # NOTE: super() will also search on ``name`` and ``bic``
        res = super()._name_search(name, args, operator, limit, name_get_uid)
        if not name or operator in expression.NEGATIVE_TERM_OPERATORS:
            return res
        args = args or []
        extra_fnames = ("code", "street", "city")
        extra_domains = [[(fname, operator, name)] for fname in extra_fnames]
        extra_domain = expression.OR(extra_domains)
        extra_res = self._search(expression.AND([extra_domain, args]), limit=limit)
        extra_res = [_id for _id in extra_res if _id not in res]
        return list(res) + extra_res
