# -*- coding: utf-8 -*-
# Copyright 2011-2017 Camptocamp SA
# Copyright 2014 Olivier Jossen (brain-tec AG)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResBetterZip(models.Model):
    """ Inherit res.better.zip class in order to add swiss specific fields

    Fields from the original file downloaded from here:
    https://match.post.ch/downloadCenter?product=2 -> File "PLZ Plus 1"

    Documentation:
    http://www.swisspost.ch/post-startseite/post-adress-services-match/post-direct-marketing-datengrundlage/post-match-zip-factsheet.pdf
    """

    _inherit = 'res.better.zip'

    active = fields.Boolean(string='Active', default=True)
    onrp = fields.Char(string='Swiss Post classification no. (ONRP)',
                       size=5, help="Primary Key")
    zip_type = fields.Char(string='Postcode type', size=2)
    additional_digit = fields.Char(string='Additional poscode digits', size=2)
    lang = fields.Char(
        string='Language code', size=1,
        help="Language (language majority) within a postcode area. "
             "1 = German, 2 = French, 3 = Italian, 4 = Romansh. "
             "For multi-lingual localities, the main language is indicated.",
    )
    lang2 = fields.Char(
        'Alternative language code',
        size=1,
        help="Additional language within a postcode.\n"
             "One alternative language code may appear for each postcode.\n"
             "1 = German, 2 = French, 3 = Italian, 4 = Romansh.",
    )
    sort = fields.Boolean(
        string='Present in sort file',
        help="Indicates if the postcode is included in the «sort file»"
             "(MAT[CH]sort): 0 = not included, 1 = included. "
             "Delivery information with addresses (only postcode and "
             "streets) are published in the sort file.",
    )
    post_delivery_through = fields.Integer(
        string='Mail delivery by',
        size=5,
        help="Indicates the post office (ONRP) that delivers most of the "
             "letters to the postcode addresses. This information can be "
             "used for bag addresses too."
    )
    communitynumber_bfs = fields.Integer(
        string='FSO municipality number (BFSNR)',
        size=5,
        help="Numbering used by the Federal Statistical Office for "
             "municipalities in Switzerland and the Principality of "
             "Liechtenstein",
    )
    valid_from = fields.Date(string='Valid from')
