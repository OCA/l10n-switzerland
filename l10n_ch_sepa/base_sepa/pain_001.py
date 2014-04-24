# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2011 Camptocamp SA
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

import os
import time

from mako import exceptions
from mako.lookup import TemplateLookup

import pooler
from openerp import addons
from openerp.osv import orm
from openerp.tools.translate import _

from msg_sepa import MsgSEPA, MsgSEPAFactory


class Pain001(MsgSEPA):

    _DEFAULT_XSD_PATH = os.path.join('base_sepa', 'base_xsd',
                                     'pain.001.001.03.xsd')
    _BASE_TMPL_DIR = os.path.join('base_sepa', 'base_template')
    _DEFAULT_TMPL_NAME = 'pain.001.001.03.xml.mako'

    _data = {}

    def __init__(self, xsd_path=_DEFAULT_XSD_PATH,
                 tmpl_dirs=None,
                 tmpl_name=_DEFAULT_TMPL_NAME):
        '''tmpl_path : path to mako template'''
        if tmpl_dirs is None:
            tmpl_dirs = []

        dirs = [addons.get_module_resource('l10n_ch_sepa',
                                           self._BASE_TMPL_DIR)]
        for dir in tmpl_dirs:
            dirs += [addons.get_module_resource('l10n_ch_sepa', dir)]

        lookup = TemplateLookup(directories=dirs, input_encoding='utf-8',
                                output_encoding='unicode')
        self.mako_tpl = lookup.get_template(tmpl_name)
        self._xml_data = None

        xsd_path = addons.get_module_resource('l10n_ch_sepa', xsd_path)
        super(Pain001, self).__init__(xsd_path)

    def _check_data(self):
        '''
        Do all data check to ensure no data is missing to generate the XML file
        '''
        if not self._data:
            raise orm.except_orm(_('Error'), _('No data has been entered'))

        if not self._data['payment']:
            raise orm.except_orm(_('Error'), _('A payment order is missing'))
        payment = self._data['payment']

        if payment.state in ['draft']:
            raise orm.except_orm(
                _('ErrorPaymentState'),
                _('Payment is in draft state. Please confirm it first.'))

        cp_bank_acc = payment.mode.bank_id
        if not cp_bank_acc:
            raise orm.except_orm(_('ErrorCompanyBank'),
                                 _('No company bank is defined in payment'))
        if not cp_bank_acc.bank.bic and not cp_bank_acc.bank_bic:
            raise orm.except_orm(_('ErrorCompanyBankBIC'),
                                 _('The selected company bank account has no '
                                   'BIC number'))
        if (not cp_bank_acc.iban
                and not cp_bank_acc.get_account_number()):
            raise orm.except_orm(
                _('ErrorCompanyBankAccNumber'),
                _('The selected company bank has no IBAN and no Account '
                  'number'))

        #Check each invoices
        for line in payment.line_ids:
            crd_bank_acc = line.bank_id
            if not crd_bank_acc:
                raise orm.except_orm(
                    _('ErrorCreditorBank'),
                    _('No bank selected for creditor of invoice %s')
                    % (line.name,))
            if not crd_bank_acc.bank.bic and not crd_bank_acc.bank_bic:
                raise orm.except_orm(
                    _('ErrorCreditorBankBIC'),
                    _('Creditor bank account has no BIC number for invoice %s')
                    % (line.name,))
            if (not crd_bank_acc.iban
                    and not crd_bank_acc.get_account_number()):
                raise orm.except_orm(
                    _('ErrorCompanyBankAccNumber'),
                    _('The selected company bank has no IBAN and no Account '
                      'number'))

    def _gather_payment_data(self, cr, uid, id, context=None):
        ''' Record the payment order data based on its id '''
        pool = pooler.get_pool(cr.dbname)
        payment_obj = pool.get('payment.order')

        payment = payment_obj.browse(cr, uid, id, context=context)
        self._data['payment'] = payment

    def compute_export(self, cr, uid, id, context=None):
        '''Compute the payment order 'id' as xml data using mako template'''
        pool = pooler.get_pool(cr.dbname)
        module_obj = pool['ir.module.module']
        this_module_id = module_obj.search(
            cr, uid,
            [('name', '=', 'l10n_ch_sepa')],
            context=context)
        this_module = module_obj.browse(cr, uid, this_module_id,
                                        context=context)[0]
        module_version = this_module.latest_version

        self._gather_payment_data(cr, uid, id, context=context)
        self._check_data()

        try:
            self._xml_data = self.mako_tpl.render_unicode(
                order=self._data['payment'],
                thetime=time,
                module_version=module_version,
                sepa_context={})
        except Exception:
            raise Exception(exceptions.text_error_template().render())

        if not self._xml_data:
            raise orm.except_orm(
                _('XML is Empty !'),
                _('An error has occured during XML generation'))

        # Validate the XML generation
        self._is_xsd_valid()

        return self._xml_data

MsgSEPAFactory.register_class('pain.001', Pain001)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
