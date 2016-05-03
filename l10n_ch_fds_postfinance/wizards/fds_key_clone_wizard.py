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


class FdsKeyCloneWizard(models.TransientModel):
    ''' The goal is to copy one authentication key to another user.

        This wizard is called when we click on copy key on FDS authentication
        keys configuration.
    '''
    _name = 'fds.key.clone.wizard'

    src_user_key_id = fields.Many2one(
        comodel_name='fds.authentication.keys',
        string='Copy authentication key:',
        required=True,
        help='select one key'
    )
    des_user_id = fields.Many2one(
        comodel_name='res.users',
        string='To:',
        required=True,
        help='assign the key to the user selected'
    )
    state = fields.Selection(
        selection=[('default', 'Default'),
                   ('done', 'Done')],
        readonly=True,
        default='default',
        help='[Info] keep state of the wizard'
    )

    ##################################
    #         Button action          #
    ##################################
    @api.multi
    def copy_button(self):
        ''' copy an authentication key to another user.
            Called by pressing copy button.

            :returns action: configuration for the next wizard's view
        '''
        self.ensure_one()
        self._has_userkey(self.des_user_id)
        self.src_user_key_id.clone_key_to(self.des_user_id)

        self._state_done_on()
        return self._do_populate_tasks()

    @api.multi
    def back_button(self):
        ''' go back to copy view.
            Called by pressing "Make another copy" button.

            :returns action: configuration for the next wizard's view
        '''
        self.ensure_one()
        self._state_default_on()
        return self._do_populate_tasks()

    ##############################
    #          function          #
    ##############################
    @api.multi
    def _has_userkey(self, user):
        ''' check if the authentication key already exist for the selected user

            :returns record: record of the model fds.authentication.keys
            :raises Warning: if user has already a key
        '''
        self.ensure_one()

        current_fds_id = self.env.context.get('active_id')
        has_userkey = self.env['fds.authentication.keys'].search([
            ['user_id', '=', user.id],
            ['fds_account_id', '=', current_fds_id]])

        if has_userkey:
            raise exceptions.Warning('Keys user already exist')

        return has_userkey

    @api.multi
    def _state_default_on(self):
        ''' private function that change state to default

            :returns: None
        '''
        self.state = 'default'

    @api.multi
    def _state_done_on(self):
        ''' private function that change state to done

            :returns: None
        '''
        self.state = 'done'

    @api.multi
    def _do_populate_tasks(self):
        ''' private function that continue with the same wizard.

            :returns action: configuration for the next wizard's view
        '''
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'new',
        }
