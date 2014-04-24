# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
# All Right Reserved
#
# Author : Yannick Vaucher (Camptocamp)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import base64

from openerp.osv import orm, fields

from l10n_ch_sepa.base_sepa.msg_sepa import MsgSEPAFactory


class WizardPain001(orm.TransientModel):
    _name = "wizard.pain001"

    _columns = {
        'pain_001_file': fields.binary('XML File', readonly=True)
    }

    def _get_country_code(self, payment):
        ''' return the coutry code or None
        from the bank defined in a payment order'''
        if payment.mode.bank_id.bank.country:
            return payment.mode.bank_id.bank.country.code
        elif payment.user_id.company_id.partner_id.country:
            return payment.user_id.company_id.partner_id.country.code
        return None

    def _get_pain_def(self, country_code):
        ''' Get the right message definition based on country code
         of selected company bank (via payment mode)
         if no country is defined, take the company country
         - Here we could add a second level for bank definitions'''
        if country_code:
            class_name = 'pain.001' + '.' + country_code.lower()
            if MsgSEPAFactory.has_instance(class_name):
                return MsgSEPAFactory.get_instance(class_name)
        return MsgSEPAFactory.get_instance('pain.001')

    def _create_attachment(self, cr, uid, data, context=None):
        ''' Create an attachment using data provided
            data needed are :
                - model : type of object to attach to
                - id : id of object model
                - base64_data
        '''
        attachment_obj = self.pool.get('ir.attachment')
        vals = {
            'name': 'pain001_%s' % time.strftime("%Y-%m-%d_%H:%M:%S",
                                                 time.gmtime()),
            'datas': data['base64_data'],
            'datas_fname': 'pain001_%s.xml' % time.strftime(
                "%Y-%m-%d_%H:%M:%S",
                time.gmtime()),
            'res_model': data['model'],
            'res_id': data['id'],
            }
        attachment_obj.create(cr, uid, vals, context=context)

    def create_pain_001(self, cr, uid, ids, context=None):
        ''' create a pain 001 file into wizard and add it as an attachment '''

        payment_obj = self.pool.get('payment.order')

        if context is None:
            context = {}
        if isinstance(ids, list):
            wiz_id = ids[0]
        else:
            wiz_id = ids
        current = self.browse(cr, uid, wiz_id, context=context)

        pay_id = context.get('active_id', [])

        payment = payment_obj.browse(cr, uid, pay_id, context=context)

        cc = self._get_country_code(payment)
        pain = self._get_pain_def(cc)

        pain_001 = pain.compute_export(cr, uid, pay_id, context=context)
        pain_001_file = base64.encodestring(pain_001.encode('utf-8'))

        data = {'base64_data': pain_001_file, 'id': pay_id}
        data['model'] = 'payment.order'

        self._create_attachment(cr, uid, data, context=context)

        current.write({'pain_001_file': pain_001_file})
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
