# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Olivier Jossen, Guewen Baconnier
#    Copyright 2011-2014 Camptocamp SA
#    Copyright 2014 brain-tec AG
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""
Adds a button allowing to reload all the banks from the XML file.
Thus, if this module has already been installed but the data is changed,
the user will be able to update the banks from the file.

The import is done by cheating the import system:

* It cheats the parser / importer so it works like if all the XML nodes have
  a ``noupdate="0"`` attribute.
* It temporarily modifies the entries in ``ir.model.data`` so they are
  considered as updatable during the loading of the file.

"""

import logging
import os
from contextlib import closing
from lxml import etree

from openerp import models, api, exceptions, _
from openerp.modules.module import get_module_resource
from openerp.tools import misc, convert, config


_logger = logging.getLogger(__name__)


MODULE = 'l10n_ch_bank'


class ForceXMLImport(convert.xml_import):
    """ Import a XML file

    Disregarding of the noupdate flag of the XML file, it updates the
    records from the XML considering that all nodes have a
    ``noupdate="0"`` attribute.
    """

    def isnoupdate(self, data_node=None):
        return False


def force_xml_import(cr, xmlfile):
    """ Import a XML file like if all nodes have a ``noupdate="0"``"""
    doc = etree.parse(xmlfile)
    rng_path = os.path.join(config['root_path'], 'import_xml.rng')
    relaxng = etree.RelaxNG(etree.parse(rng_path))
    try:
        relaxng.assert_(doc)
    except AssertionError:
        _logger.error('The XML file does not fit the required schema')
        _logger.error(misc.ustr(relaxng.error_log.last_error))
        raise exceptions.Warning(_('The banks file cannot be read.'))

    obj = ForceXMLImport(cr, MODULE, {}, 'update')
    obj.parse(doc.getroot(), mode='update')


class base_config_settings(models.TransientModel):
    _inherit = 'account.config.settings'

    @api.multi
    def update_banks(self):
        """ Force the update of the banks from the XML file """
        data_obj = self.env['ir.model.data']
        entries = data_obj.search([('module', '=', MODULE),
                                   ('model', '=', 'res.bank')])
        # If the records in 'ir.model.data' have noupdate to True,
        # the XML records won't be updated
        entries.write({'noupdate': False})
        filepath = get_module_resource(MODULE, 'bank.xml')
        with closing(misc.file_open(filepath)) as fp:
            force_xml_import(self.env.cr, fp)
        entries.write({'noupdate': True})
        return True
