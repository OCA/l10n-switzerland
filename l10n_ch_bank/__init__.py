# Copyright 2015 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from . import models
from .hooks import import_csv_data


def post_init(cr, registry):
    import_csv_data(cr, registry)
