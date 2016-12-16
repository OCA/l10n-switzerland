# -*- coding: utf-8 -*-
# © 2011-2014 Nicolas Bessi (Camptocamp SA)
# © 2014 Olivier Jossen brain-tec AG
# © 2014 Guewen Baconnier (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields


class ResBank(models.Model):
    """ Inherit res.bank class in order to add swiss specific fields

    Fields from the original file downloaded from here:
    http://www.six-interbank-clearing.com/de/home/bank-master-data/download-bc-bank-master.html

    =============  ================
    Field in file  Column
    -------------  ----------------
    Gruppe         bank_group
    Filial-ID      bank_branchid
    Hauptsitz      bank_headquarter
    Vorwahl        bank_areacode
    Postkonto      bank_postaccount
    =============  ================

    .. note:: Postkonto: ccp does not allow to enter entries like
       ``*30-38151-2`` because of the ``*`` but this comes from the
       xls to import
    """
    _inherit = 'res.bank'

    bank_group = fields.Char(string='Group', size=2)
    bank_branchid = fields.Char(string='Branch-ID', size=5)
    bank_clearing_new = fields.Char(string='BCNr new', size=5)
    bank_sicnr = fields.Char(string='SIC-Nr', size=6)
    bank_headquarter = fields.Char(string='Headquarter', size=5)
    bank_bcart = fields.Char(string='BC-Art', size=1)
    bank_valid_from = fields.Date(string='Valid from')
    bank_sic = fields.Char(string='SIC', size=1)
    bank_eurosic = fields.Char(string='euroSIC', size=1)
    bank_lang = fields.Char(string='Language', size=1)
    bank_postaladdress = fields.Char(string='Postal address', size=35)
    bank_areacode = fields.Char(string='Area code', size=5)
    bank_postaccount = fields.Char(string='Post account', size=35)
