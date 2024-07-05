# Copyright 2015 Camptocamp SA
# Copyright 2016 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
import logging
from datetime import datetime

from babel.numbers import NumberFormatError, parse_decimal

from odoo import exceptions, fields, models
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class AccountCresusImport(models.TransientModel):
    _name = "account.cresus.import"
    _description = "Export Accounting"

    company_id = fields.Many2one("res.company", "Company", invisible=True)
    report = fields.Text(readonly=True)
    journal_id = fields.Many2one("account.journal", "Journal", required=True)
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done"), ("error", "Error")],
        readonly=True,
        default="draft",
    )
    file = fields.Binary(required=True)
    imported_move_ids = fields.Many2many(
        "account.move", "import_cresus_move_rel", string="Imported moves"
    )
    index = fields.Integer()

    HEAD_CRESUS = [
        "date",
        "debit",
        "credit",
        "pce",
        "ref",
        "amount",
        "typtvat",
        "currency_amount",
        "analytic_account",
    ]

    def prepare_move(self, lines, date, ref, journal_id):
        move = {}
        move["date"] = date
        move["ref"] = ref
        move["journal_id"] = journal_id
        move["line_ids"] = [(0, 0, ln) for ln in lines]
        return move

    def prepare_line(
        self,
        name,
        debit_amount,
        credit_amount,
        account_code,
        cresus_tax_code,
        analytic_account_code,
        tax_ids,
    ):
        account_obj = self.env["account.account"]
        tax_obj = self.env["account.tax"]
        analytic_account_obj = self.env["account.analytic.account"]

        line = {}
        line["name"] = name
        line["debit"] = debit_amount
        line["credit"] = credit_amount

        account = account_obj.search([("code", "=", account_code)], limit=1)
        if not account:
            raise exceptions.MissingError(_("No account with code %s") % account_code)
        line["account_id"] = account.id
        if account.currency_id:
            line["currency_id"] = account.currency_id.id

        if cresus_tax_code:
            tax = tax_obj.search(
                [
                    ("tax_cresus_mapping", "=", cresus_tax_code),
                    ("price_include", "=", True),
                ],
                limit=1,
            )
            line["tax_line_id"] = tax.id
        if analytic_account_code:
            analytic_account = analytic_account_obj.search(
                [("code", "=", analytic_account_code)], limit=1
            )
            line["analytic_distribution"] = {str(analytic_account.id): 100.00}

        if tax_ids:
            line["tax_ids"] = [(4, id, 0) for id in tax_ids]
        return line

    def _parse_csv(self):
        """Parse stored CSV file.

        Manage base 64 decoding.

        :returns: generator

        """
        Attachment = self.env["ir.attachment"]
        csv_attachment = Attachment.search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("res_field", "=", "file"),
            ]
        )
        delimiter = "\t"
        csv_filepath = Attachment._full_path(csv_attachment.store_fname)
        if True:
            with open(csv_filepath) as decoded:
                try:
                    data = csv.DictReader(
                        decoded, fieldnames=self.HEAD_CRESUS, delimiter=delimiter
                    )
                except csv.Error as error:
                    raise exceptions.ValidationError(
                        _(
                            "CSV file is malformed\n"
                            "Please choose the correct separator\n"
                            "the error detail is:\n"
                            "%r"
                        )
                        % error
                    ) from error
                for line in data:
                    line["date"] = self._parse_date(line["date"])
                    yield line

    def _parse_date(self, date_string):
        """Parse a date coming from Crésus and put it in the format used by Odoo.

        Both 01.01.70 and 01.01.1970 have been sighted in Crésus' output.

        :param date_string: cresus data
        :returns: a date string
        """
        for fmt in ["%d.%m.%y", "%d.%m.%Y"]:
            try:
                dt = datetime.strptime(date_string, fmt)
                break
            except ValueError:
                continue
        else:
            raise exceptions.ValidationError(_("Can't parse date '%s'") % date_string)
        return fields.Date.to_string(dt)

    def _standardise_data(self, data):
        """split accounting lines where needed

        Crésus writes one csv line per move when there are just two lines
        (take some money from one account and put all of it in another),
        and uses ellipses in more complex cases. What matters is the pce
        label, which is the same on all lines of a move.
        """
        journal_id = self.journal_id.id
        previous_pce = None
        previous_date = None
        previous_tax_id = None
        lines = []
        for self.index, line_cresus in enumerate(data, 1):
            if previous_pce is not None and previous_pce != line_cresus["pce"]:
                yield self.prepare_move(
                    lines, date=previous_date, ref=previous_pce, journal_id=journal_id
                )
                lines = []
            previous_pce = line_cresus["pce"]
            previous_date = line_cresus["date"]

            try:
                recto_amount_decimal = parse_decimal(
                    line_cresus["amount"], locale="de_CH"
                )
            except NumberFormatError:
                # replacing old version of group separator
                recto_amount_decimal = parse_decimal(
                    line_cresus["amount"].replace("'", "’"), locale="de_CH"
                )
            recto_amount = float(recto_amount_decimal)

            verso_amount = 0.0
            if recto_amount < 0:
                recto_amount, verso_amount = 0.0, -recto_amount

            tax_ids = [previous_tax_id] if previous_tax_id else []
            previous_tax_id = None
            if line_cresus["debit"] != "...":
                line = self.prepare_line(
                    name=line_cresus["ref"],
                    debit_amount=recto_amount,
                    credit_amount=verso_amount,
                    account_code=line_cresus["debit"],
                    cresus_tax_code=line_cresus["typtvat"],
                    analytic_account_code=line_cresus["analytic_account"],
                    tax_ids=tax_ids,
                )
                lines.append(line)
                if "tax_line_id" in line:
                    previous_tax_id = line["tax_line_id"]

            if line_cresus["credit"] != "...":
                line = self.prepare_line(
                    name=line_cresus["ref"],
                    debit_amount=verso_amount,
                    credit_amount=recto_amount,
                    account_code=line_cresus["credit"],
                    cresus_tax_code=line_cresus["typtvat"],
                    analytic_account_code=line_cresus["analytic_account"],
                    tax_ids=tax_ids,
                )
                lines.append(line)
                if "tax_line_id" in line:
                    previous_tax_id = line["tax_line_id"]

        yield self.prepare_move(
            lines, date=line_cresus["date"], ref=previous_pce, journal_id=journal_id
        )

    def _import_file(self):
        self.index = 0
        data = self._parse_csv()
        data = self._standardise_data(data)
        for mv in data:
            self.with_context(dont_create_taxes=True).write(
                {"imported_move_ids": [(0, False, mv)]}
            )
            self.invalidate_cache(fnames=["imported_move_ids"])

    def import_file(self):
        try:
            self._import_file()
        except Exception as exc:
            _logger.exception(exc)
            self.env.cr.rollback()
            self.write(
                {
                    "state": "error",
                    "report": "Error (at row %s):\n%s" % (self.index, exc),
                }
            )
            return {
                "name": _("Accounting Crésus Import"),
                "type": "ir.actions.act_window",
                "res_model": "account.cresus.import",
                "res_id": self.id,
                "view_type": "form",
                "view_mode": "form",
                "target": "new",
            }
        self.state = "done"
        # show the resulting moves in main content area
        return {
            "domain": str([("id", "in", self.imported_move_ids.ids)]),
            "name": _("Imported Journal Entries"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "type": "ir.actions.act_window",
        }
