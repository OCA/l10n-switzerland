# Copyright 2012-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, models


class AccountMove(models.Model):

    _inherit = "account.move"

    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        domain = []
        for arg in args:
            if not isinstance(arg, (tuple, list)) or len(arg) != 3:
                domain.append(arg)
                continue
            field, operator, value = arg
            if field != "ref":
                domain.append(arg)
                continue
            if operator not in (
                "like",
                "ilike",
                "=like",
                "=ilike",
                "not like",
                "not ilike",
            ):
                domain.append(arg)
                continue
            if value:
                value = value.replace(" ", "")
                if not value:
                    # original value contains only spaces, the query
                    # would return all rows, so avoid a costly search
                    # and drop the domain triplet
                    continue
                # add wildcards for the like search, except if the operator
                # is =like of =ilike because they are supposed to be there yet
                if operator.startswith("="):
                    operator = operator[1:]
                else:
                    value = "%{}%".format(value)
            # add filtered operator to query
            query_op = (
                "SELECT id FROM account_move "
                "WHERE REPLACE(ref, ' ', '') %s %%s" % (operator,)
            )
            # avoid pylint check on no-sql-injection query_op is safe
            query = query_op
            self.env.cr.execute(query, (value,))
            ids = [t[0] for t in self.env.cr.fetchall()]
            domain.append(("id", "in", ids))

        return super()._search(
            domain,
            offset=offset,
            limit=limit,
            order=order,
            count=count,
            access_rights_uid=access_rights_uid,
        )

    @api.constrains("ref", "payment_reference")
    def _check_bank_type_for_type_isr(self):
        """Compatibility with module `account_payment_partner`"""
        for move in self:
            if move.move_type == "out_invoice" and move._has_isr_ref():
                if hasattr(super(), "partner_banks_to_show"):
                    bank_acc = move.partner_banks_to_show()
                else:
                    bank_acc = move.partner_bank_id
                if not bank_acc:
                    raise exceptions.ValidationError(
                        _(
                            "Bank account shouldn't be empty, for ISR ref"
                            " type, you can set it manually or set appropriate"
                            " payment mode."
                        )
                    )
                if (
                    bank_acc.acc_type != "qr-iban"
                    and (
                        move.currency_id.name == "CHF"
                        and not bank_acc.l10n_ch_isr_subscription_chf
                    )
                    or (
                        move.currency_id.name == "EUR"
                        and not bank_acc.l10n_ch_isr_subscription_eur
                    )
                ):
                    raise exceptions.ValidationError(
                        _(
                            "Bank account must contain a subscription number for"
                            " ISR ref type."
                        )
                    )
        return True

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
