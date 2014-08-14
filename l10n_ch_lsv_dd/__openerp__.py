##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2014 Compassion (http://www.compassion.ch)
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
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Compassion',
    'website': 'http://www.compassion.ch',
    'category': 'Banking addons',
    'depends': ['account_direct_debit',
                'account_banking_mandate',
                'l10n_ch_payment_slip_base_transaction_id'],
    'external_dependencies': {},
    'data': [
        'data/payment_type.xml',
        'data/export_filename_sequence.xml',
        'view/banking_export_ch_dd_view.xml',
        'view/bank_view.xml',
        'view/dd_export_wizard_view.xml',
        'view/lsv_export_wizard_view.xml',
        'view/payment_order_view.xml',
        'view/invoice_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'description': '''
LSV and Postfinance Direct Debit file generator
===============================================
Features:
---------
    * LSV file generation
    * Postfinance Direct Debit file generation
    * Invoice freeing. You can "free" an invoice that is in a direct debit \
    order. This is because you have sometimes to generate 2 direct debit \
    order for the same invoice (i.e. if debit fails the first time).


Prerequisite for LSV file generation:
-------------------------------------
For LSV file generation, don't forget :
    * To set your LSV identifier in your company settings.
    * To set your BVR identifier in your company settings if you want to use \
    BVR references.
    * To setup a payment mode with payment type "LSV Direct Debit"
    * That each partner which is concerned by LSV has to have a valid bank \
    account with a valid mandate.


Standard workflow:
------------------
    * Create some invoices for partners with well configured bank accounts.
    * Create a Direct Debit Order with a payment mode having LSV payment type.
    * Make sure that due dates are in range -10 day to +30 days if you chose \
    "Due date" as preferred date.
    * Press "Confirm payments"
    * Press "Make payments". This will launch the LSV file generation wizard.
    * Download the generated file and press "Validate". If you need to \
    download the file again, you can access the generated file with the \
    "Generated Direct Debit Files" menu.

Actually, only BVR reference usage is implemented (using l10n_ch_payment_slip
module). IPI usage is not implemented yet, this way an error occurs if no BVR
ref are set in invoices.

This module uses the framework provided by the banking addons, cf
https://launchpad.net/banking-addons
    ''',
    'active': False,
    'installable': True,
}
