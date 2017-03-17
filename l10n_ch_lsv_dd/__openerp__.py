##############################################################################
#
#    Swiss localization Direct Debit module for Odoo
#    Copyright (C) 2014 Compassion (http://www.compassion.ch)
#    Copyright (C) 2017 brain-tec AG (http://www.braintec-group.com)
#    @author: Cyril Sester <cyril.sester@outlook.com>
#
#    This module has been inspired by the SEPA Direct Debit module
#    (by Alexis de Lattre)
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
{
    'name': 'LSV and Postfinance Direct Debit file generation',
    'summary': 'Create LSV and Direct Debit (postfinance) files',
    'version': '9.0.1.0.0',
    'license': 'AGPL-3',
    'author': "brain-tec AG,Compassion,Odoo Community Association (OCA)",
    'website': 'http://www.compassion.ch,http://www.braintec-group.com',
    'category': 'Localization',
    'depends': [
        'l10n_ch_payment_slip',
        'account_payment_order',
        'account_payment_mode',
        'account_banking_mandate',
        'account_banking_pain_base',
        'account_banking_sepa_direct_debit',
    ],
    'external_dependencies': {},
    'data': [
        'data/payment_type.xml',
        'data/export_filename_sequence.xml',
        'views/account_payment_line_view.xml',
        'views/account_payment_method_view.xml',
        'views/account_payment_mode_view.xml',
        'views/account_payment_order_view.xml',
        'views/banking_export_ch_dd_view.xml',
        'views/bank_payment_line_view.xml',
        'views/bank_view.xml',
        'views/dd_export_wizard_view.xml',
        'views/invoice_view.xml',
        'views/lsv_export_wizard_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'test': [
        'test/lsv-dd-test.yml',
    ],
    'auto_install': False,
    'installable': True,
}
