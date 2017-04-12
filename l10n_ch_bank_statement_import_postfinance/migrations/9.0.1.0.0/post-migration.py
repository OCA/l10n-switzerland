# -*- coding: utf-8 -*-
# © 2017 Emanuel Cino (Compassion CH)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""
Populate related file field of bank_statement_line for old imported files.
"""


def migrate(cr, version):
    if not version:
        return

    query = """
        UPDATE account_bank_statement_line bl
        SET related_file = (SELECT max(id) FROM ir_attachment
                            WHERE res_model = 'account.bank.statement.line'
                            AND res_id = bl.id)
    """
    cr.execute(query)
