# Copyright 2012-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from .. import postfinance


class Bank(models.Model):
    """Inherit res.bank class in order to add swiss specific field"""

    _inherit = "res.bank"

    code = fields.Char(string="Code", help="Internal reference")
    clearing = fields.Char(
        string="Clearing number",
        help="Swiss unique bank identifier also used in IBAN number",
    )
    city = fields.Char(string="City", help="City of the bank")
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
    def name_search(self, name, args=None, operator="ilike", limit=80):
        """Extends to look on bank code, bic, name, street and city"""
        if args is None:
            args = []
        ids = []
        cols = ("code", "bic", "name", "street", "city")
        if name:
            for val in name.split(" "):
                for col in cols:
                    tmp_ids = self.search([(col, "ilike", val)] + args, limit=limit)
                    if tmp_ids:
                        ids += tmp_ids.ids
                        break
        else:
            ids = self.search(args, limit=limit).ids
        # we sort by occurrence
        to_ret_ids = list(set(ids))
        to_ret_ids = sorted(to_ret_ids, key=lambda x: ids.count(x), reverse=True)
        return self.browse(to_ret_ids).name_get()
