# Copyright 2012 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv.expression import TERM_OPERATORS, is_leaf


class AccountMove(models.Model):
    _inherit = "account.move"

    ref_normalized = fields.Char(
        string="Reference (normalized)",
        compute="_compute_ref_normalized",
        search="_search_ref_normalized",
        help="Without spaces, to ease searching",
    )

    @api.depends("ref")
    def _compute_ref_normalized(self):
        for move in self:
            move.ref_normalized = move.ref and move.ref.replace(" ", "")

    @api.model
    def _search_ref_normalized(self, operator, value):
        """Perform a search on ``ref_normalized``

        This field is not stored on the database, but it's a computed version of ``ref``
        that contains no spaces.

        When searching on ``ref_normalized``, the spaces in ``value`` are ignored.
        """
        if operator not in TERM_OPERATORS:
            raise UserError(_("Invalid operator %s", operator))
        need_wildcard = operator in ("like", "ilike", "not like", "not ilike")
        sql_operator = {"=like": "like", "=ilike": "ilike"}.get(operator, operator)
        value = value and value.replace(" ", "")
        value = f"%{value}%" if need_wildcard else value
        query = f"""
            SELECT id
            FROM {self._table}
            WHERE REPLACE(ref, ' ' , '') {sql_operator} %s
        """
        self.flush_model(["ref"])
        return [("id", "inselect", (query, (value,)))]

    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        # OVERRIDE to search on ``ref_normalized`` instead of ``ref`` when using
        # the ``like`` or ``ilike`` operators.
        new_args = []
        like_operators = (op for op in TERM_OPERATORS if "like" in op)
        for element in args:
            field, operator, value = element if is_leaf(element) else (None, None, None)
            if field != "ref" or operator not in like_operators:
                new_args.append(element)
                continue
            new_args.append(("ref_normalized", operator, value))
        return super()._search(
            new_args,
            offset=offset,
            limit=limit,
            order=order,
            count=count,
            access_rights_uid=access_rights_uid,
        )

    def partner_banks_to_show(self):
        """
        Extend method from account_payment_partner to add specific
        logic for switzerland bank payments if base method does not give
        a result
        """
        res = super().partner_banks_to_show()
        if not res:
            if self.journal_id:
                return self.journal_id.bank_account_id
        return res
