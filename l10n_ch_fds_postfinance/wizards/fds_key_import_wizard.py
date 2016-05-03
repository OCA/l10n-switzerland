# -*- coding: utf-8 -*-
##############################################################################
#
#    Swiss Postfinance File Delivery Services module for Odoo
#    Copyright (C) 2015 Compassion CH
#    @author: Nicolas Tran
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

from openerp import models, fields, api, exceptions
import logging
import base64

_logger = logging.getLogger(__name__)


class FdsKeyImportWizard(models.TransientModel):
    ''' FDS Postfinance keys import wizard.
        The goal is to import existing key in the database.

        This wizard is called when we click on import FDS authentication keys
        for one FDS.
        This Class inherit from fds_key_generator_wizard.
    '''
    _name = 'fds.key.import.wizard'
    _inherit = 'fds.key.generator.wizard'

    public_key_import_txt = fields.Text(
        string='Public key',
        help='copy/paste your public key'
    )
    private_key_import_txt = fields.Text(
        string='Private key',
        help='copy/paste your private key'
    )
    public_key_import_file = fields.Binary(
        string='Public key',
        help='select one file that contain your public key'
    )
    private_key_import_file = fields.Binary(
        string='Private key',
        help='select one file that contain your private key'
    )

    ##################################
    #         Button action          #
    ##################################
    @api.multi
    def import_keys_button(self):
        ''' Import public and private key then save in the database.
            Called by pressing import button.

            :returns action: configuration for the next wizard's view
            :raises Warning: if missing input information
        '''
        self.ensure_one()

        # check if authentication keys already exist
        self.userkey_exist()

        if self.private_key_import_file and self.public_key_import_file:
            # found 2 import file key
            return self._import_key('file')
        elif self.private_key_import_txt and self.public_key_import_txt:
            # found 2 import text key
            return self._import_key('text')
        elif self.private_key_import_file or self.public_key_import_file:
            # miss 1 import file key
            raise exceptions.Warning('Import key file missing')
        elif self.private_key_import_txt or self.public_key_import_txt:
            # miss 1 import text key
            raise exceptions.Warning('Import key text missing')
        else:
            raise exceptions.Warning('Import key not found')

    ##############################
    #          function          #
    ##############################
    @api.multi
    def _import_key(self, type):
        ''' private function that convert the keys depending on type,
            crypte and save in the database using inherit function (_savekeys).

            :param str type: type of the import "file" or "text"
            :returns action: configuration for the next wizard's view
        '''
        self.ensure_one()

        # convert keys
        auth_key_obj = self.env['fds.authentication.keys']
        if type == 'file':
            pub = base64.b64decode(self.public_key_import_file)
            ppk = base64.b64decode(self.private_key_import_file)
        elif type == 'text':
            pub = self.public_key_import_txt
            ppk = self.private_key_import_txt
        else:
            _logger.error("Bad implementation in fds_key_import_wizard")
            raise exceptions.Warning('Error code. Contact your admin')

        keys = auth_key_obj.import_pairkey(pub, ppk)
        # save values
        self.savekeys(keys[0], keys[1])
        # change view wizard
        self.write({'state': 'generate'})
        return self._do_populate_tasks()
