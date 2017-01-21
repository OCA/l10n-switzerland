# -*- coding: utf-8 -*-
# © 2011-2014 Nicolas Bessi (Camptocamp SA)
# © 2014 Olivier Jossen brain-tec AG
# © 2015 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from . import models


def post_init(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""
    from openerp.tools import convert_file
    filename = 'data/res.bank.csv'
    convert_file(cr, 'l10n_ch_bank', filename, None, mode='init',
                 noupdate=True, kind='init', report=None)
