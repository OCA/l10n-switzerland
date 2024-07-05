# Copyright 2016 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import difflib
import logging
import tempfile

import odoo.tests.common as common
from odoo.modules import get_resource_path

_logger = logging.getLogger(__name__)


class TestImport(common.TransactionCase):
    def setUp(self):
        super(TestImport, self).setUp()

        tax_obj = self.env["account.tax"]
        account_obj = self.env["account.account"]

        for code in [
            "1000",
            "1010",
            "1210",
            "2200",
            "2800",
            "2915",
            "6512",
            "6513",
            "6642",
            "9100",
            "10101",
        ]:
            found = account_obj.search([("code", "=", code)])
            if found:  # patch it within the transaction
                found.account_type = "income"
            else:
                account_obj.create(
                    {
                        "name": "dummy %s" % code,
                        "code": code,
                        "account_type": "income",
                        "reconcile": True,
                    }
                )
        self.vat = tax_obj.create(
            {
                "name": "dummy VAT",
                "price_include": True,
                "amount": 4.2,
                "tax_cresus_mapping": "VAT",
            }
        )

    def test_import(self):
        journal_obj = self.env["account.journal"]
        misc = journal_obj.search([("code", "=", "MISC")], limit=1)
        if not misc:
            misc = journal_obj.create(
                {"code": "MISC", "name": "dummy MISC", "type": "general"}
            )

        def get_path(filename):
            res = get_resource_path("l10n_ch_import_cresus", "tests", filename)
            return res

        with open(get_path("input.csv"), "rb") as src:
            contents = base64.b64encode(src.read()).decode("utf-8")

        wizard = self.env["account.cresus.import"].create(
            {"journal_id": misc.id, "file": contents}
        )
        wizard._import_file()

        res = wizard.imported_move_ids
        res._check_balanced({"records": res, "self": res})

        gold = open(get_path("golden-output.txt"), "r")
        temp = tempfile.NamedTemporaryFile("w+", prefix="odoo-l10n_ch_import_cresus")

        # Get a predictable representation that can be compared across runs
        def p(u):
            temp.write(u)
            temp.write("\n")

        first = True
        for mv in res:
            if not first:
                p("")
            first = False
            p("move ‘%s’" % mv.ref)
            p("  (dated %s)" % mv.date)
            p("  (in journal %s)" % mv.journal_id.code)
            p("  with lines:")
            for ln in mv.line_ids:
                p("    line “%s”" % ln.name)
                if ln.debit:
                    p("      debit = %s" % ln.debit)
                if ln.credit:
                    p("      credit = %s" % ln.credit)
                p("      account is ‘%s’" % ln.account_id.code)
                if ln.tax_line_id:
                    p("      originator tax is ‘%s’" % ln.tax_line_id.name)
                if ln.tax_ids:
                    p("      taxes = (‘%s’)" % "’, ‘".join(ln.tax_ids.mapped("name")))
        temp.seek(0)
        diff = list(
            difflib.unified_diff(
                gold.readlines(), temp.readlines(), gold.name, temp.name
            )
        )
        gold.close()
        temp.close()
        if len(diff) > 2:
            for i in diff:
                _logger.error(i.rstrip())
            self.fail("actual output doesn't match exptected output")
