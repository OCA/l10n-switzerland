# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tools import convert_file


def import_csv_data(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""
    filenames = ['data/res.bank.csv']
    for filename in filenames:
        convert_file(
            cr, 'l10n_ch_bank',
            filename, None, mode='init', noupdate=True,
            kind='init', report=None,
        )


def post_init(cr, registry):
    import_csv_data(cr, registry)
