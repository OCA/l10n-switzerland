# -*- encoding: utf-8 -*-
#
#  opae_wizard.py
#  l10n_ch
#
#  Created by Jérôme Bove
#
#  Copyright (c) 2010 CamptoCamp. All rights reserved.
##############################################################################
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
import wizard
import pooler
import mx.DateTime
import pdb


FORM = """<?xml version="1.0"?>
<form string="OPAE file creation - Results">
<separator colspan="4" string="Clic on 'Save as' to save the OPAE file :" />
    <field name="opae"/>
</form>"""

FIELDS = {
    'opae': {
        'string': 'OPAE File',
        'type': 'binary',
        'readonly': True,
    },
}

TRANS=[
    (u'é','e'),
    (u'è','e'),
    (u'à','a'),
    (u'ê','e'),
    (u'î','i'),
    (u'ï','i'),
    (u'â','a'),
    (u'ä','a'),
]

def _create_opae(obj, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    pdb.set_trace()
    payment_order_obj = pool.get('payment.order')
    payment = payment_order_obj.browse(cr, uid, data['ids'])[0]
    transaction_numer = -1
    for line in payment.line_ids:
        maturity_date = line.ml_maturity_date
        debit_account_number = line.partner_id.property_account_payable #ou line.partner_id.property_account_receivable
        debit_tax_account_number = debit_account_number
        order_number = line._id - payment.line_ids[0]._id + 1
        transaction_type = line.bank_id.state or payment.mode.bank_id.state or ''
        
        transaction_number += 1
        deposit_currency = line.currency.code
        deposit_amount = line.amount
        bonification_currency = deposit_currency
        pool.get('res.users').browse(cr,uid,uid).context_lang[-2:]
        country_code = pool.get('res.users').browse(cr,uid,uid).context_lang[-2:]
        toto_postal_account_number = line.bank_id.post_number or payment.mode.bank_id.post_number or ''
        toto_iban = line.bank_id.iban or payment.mode.bank_id.iban or ''
        titi_name = line.info_partner.split('\n')[0]
        titi_street = line.info_partner.split('\n')[1]
        titi_npa = line.info_partner.split('\n')[2].split()[0]
        titi_city = line.info_partner.split('\n')[2][len(titi_npa):]
        titi_add_designation = ''
        toto_name = titi_name
        toto_street = titi_street
        toto_npa = titi_npa
        toto_city = titi_city
        toto_add_designation = titi_add_designation
        if line.communication and line.communication2:
            communication = line.communication + ' ' + line.communication2
        else:
            communication = line.communication
        
        if len(communication) <= 35:
            communication_bloc_1 = communication
        elif len (communication) <= 70:
            communication_bloc_1 = communication[:34]
            communication_bloc_2 = communication[35:]
        elif len (communication) <= 105:
            communication_bloc_1 = communication[:34]
            communication_bloc_2 = communication[35:69]
            communication_bloc_3 = communication[70:]
        elif len (communication) <= 140:
            communication_bloc_1 = communication[:34]
            communication_bloc_2 = communication[35:69]
            communication_bloc_3 = communication[70:104]
            communication_bloc_4 = communication[105:]
        else:
            communication_bloc_1 = communication[:34]
            communication_bloc_2 = communication[35:69]
            communication_bloc_3 = communication[70:104]
            communication_bloc_4 = communication[105:139]
        
        tata_name = line.info_owner.split('\n')[0]
        tata_street = line.info_owner.split('\n')[1]
        tata_npa = line.info_owner.split('\n')[2].split()[0]
        tata_city = line.info_owner.split('\n')[2][len(tata_npa):]
        tata_add_designation = ''
        bic = line.bank_id.bank.bic or payment.mode.bank_id.bank.bic
        titi_bank_name = payment.mode.bank_id.bank.name
        titi_bank_add_designation = ''
        titi_bank_street = payment.mode.bank_id.bank.street
        titi_bank_city = payment.mode.bank_id.bank.city
        titi_add_designation = ''
        if transaction.type == ''
        modulo_11_digit = 
        
        
        
        
    return {'opae': opae_data}


class wizard_opae_create(wizard.interface):
    states = {
        'init' : {
            'actions' : [_create_opae],
            'result' : {'type' : 'form',
                'arch' : FORM,
                'fields' : FIELDS,
                'state' : [('end', 'OK', 'gtk-ok', True)]
            }
        },
    }

wizard_opae_create('account.opae_create')
# vim:expanopaeb:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
