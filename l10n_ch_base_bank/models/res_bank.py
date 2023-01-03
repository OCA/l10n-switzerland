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
        # OVERRIDE to also display the ``code``, ``street`` and ``city``
        # NOTE: super() will already display the ``name`` and ``bic``
        names = dict(super().name_get())
        extra_fnames = ("street", "city")
        res = []
        for rec in self:
            extra_name = " - ".join(rec[x] for x in extra_fnames if rec[x])
            name = names[rec.id]
            name = f"{name} - {extra_name}" if extra_name else name
            res.append((rec.id, name))
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
