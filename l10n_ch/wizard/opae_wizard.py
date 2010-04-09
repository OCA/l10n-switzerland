# -*- encoding: utf-8 -*-
#
#  opae_wizard.py
#  l10n_ch
#
#  Created by Nicolas Bessi based on Credric Krier contribution
#
#  Copyright (c) 2009 CamptoCamp. All rights reserved.
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
from mx import DateTime
import pdb
import base64


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
class OPAE(object):
    "container for opae atributes"

    
def _prepare_opae(obj, cr, uid, data, context):
    opae = OPAE()
    opae.pool = pooler.get_pool(cr.dbname)
    pool = opae.pool
    opae.payment_order_obj = pool.get('payment.order')
    payment = opae.payment_order_obj.browse(cr, uid, data['ids'])[0]
    payment_order_obj = opae.payment_order_obj
    opae.transaction_id = -1
    opae.order_id = 0
    opae.payment = payment
    opae.data = ''
    opae.check_header = False
    opae.currencies = {}
    
    for line in payment.line_ids:
        opae.line = line
        opae.order_id += 1
        opae.maturity_date = payment.date_prefered == 'due' and line.ml_maturity_date and DateTime.strptime(line.ml_maturity_date,'%Y-%m-%d') or payment.date_prefered == 'fixed' and payment.date_planned and DateTime.strptime(payment.date_planned,'%Y-%M-%d') or payment.date_prefered == 'now' and DateTime.now()
        opae.debit_account_number = ''.join(payment.mode.bank_id.bvr_number.split('-'))
        opae.debit_tax_account_number = opae.debit_account_number
        opae.order_number = line._id - payment.line_ids[0]._id + 1
        opae.transaction_type = line.bank_id.state or payment.mode.bank_id.state
        opae.transaction_id += 1
        opae.deposit_currency = line.currency
        opae.deposit_amount = line.amount_currency
        opae.bonification_currency = opae.deposit_currency
        opae.country_code = opae.payment.user_id.company_id.partner_id.country.code
        opae.toto_postal_account_number = line.bank_id.post_number or ''
        opae.titi_postal_account_number = opae.toto_postal_account_number
        opae.toto_iban = line.bank_id.iban or ''
        opae.toto_iban = opae.toto_iban.upper()
        if line.info_partner:
            opae.titi_name = line.info_partner.split('\n')[0] or ''
            opae.titi_street = line.info_partner.split('\n')[1] or ''
            opae.titi_npa = line.info_partner.split('\n')[2].split()[0] or ''
            opae.titi_city = line.info_partner.split('\n')[2][len(opae.titi_npa):]
        else:
            opae.titi_name = ''
            opae.titi_street = ''
            opae.titi_npa = ''
            opae.titi_city = ''
        opae.titi_add_designation = ''
        opae.toto_name = opae.titi_name
        opae.toto_street = opae.titi_street
        opae.toto_npa = opae.titi_npa
        opae.toto_city = opae.titi_city
        opae.toto_add_designation = opae.titi_add_designation
        if line.communication and line.communication2:
            opae.communication = line.communication + ' ' + line.communication2
        else:
            opae.communication = line.communication
        
        if len(opae.communication) <= 35:
            opae.communication_bloc_1 = opae.communication
            opae.communication_bloc_2 = ''
            opae.communication_bloc_3 = ''
            opae.communication_bloc_4 = ''
        elif len (opae.communication) <= 70:
            opae.communication_bloc_1 = opae.communication[:34]
            opae.communication_bloc_2 = opae.communication[35:]
            opae.communication_bloc_3 = ''
            opae.communication_bloc_4 = ''
        elif len (communication) <= 105:
            opae.communication_bloc_1 = opae.communication[:34]
            opae.communication_bloc_2 = opae.communication[35:69]
            opae.communication_bloc_3 = opae.communication[70:]
            opae.communication_bloc_4 = ''
        elif len (communication) <= 140:
            opae.communication_bloc_1 = opae.communication[:34]
            opae.communication_bloc_2 = opae.communication[35:69]
            opae.communication_bloc_3 = opae.communication[70:104]
            opae.communication_bloc_4 = opae.communication[105:]
        else:
            opae.communication_bloc_1 = opae.communication[:34]
            opae.communication_bloc_2 = opae.communication[35:69]
            opae.communication_bloc_3 = opae.communication[70:104]
            opae.communication_bloc_4 = opae.communication[105:139]
        
        opae.tata_name = line.info_owner.split('\n')[0]
        opae.tata_street = line.info_owner.split('\n')[1]
        opae.tata_npa = line.info_owner.split('\n')[2].split()[0]
        opae.tata_city = line.info_owner.split('\n')[2][len(opae.tata_npa):]
        opae.tata_add_designation = ''
        opae.bic = line.bank_id.bank and line.bank_id.bank.bic or ''
        opae.titi_bank_npa = line.bank_id.bank and line.bank_id.bank.zip or ''
        opae.titi_bank_name = line.bank_id.bank and line.bank_id.bank.name or ''
        opae.titi_bank_add_designation = ''
        opae.titi_bank_street = payment.mode.bank_id.bank and payment.mode.bank_id.bank.street or ''
        opae.titi_bank_city = line.bank_id.bank and line.bank_id.bank.city or ''
        opae.titi_add_designation = ''
        if opae.transaction_type == 'bvrpost' or opae.transaction_type == 'bvrbank':
            opae.modulo_11_digit = '  '
            #pdb.set_trace()
            opae.bvr_adherent_num = line.bank_id.bvr_adherent_num or line.bank_id.bvr_number or ''
            opae.reference = line.communication
            opae.sender_reference = ' ' * 35
        if not opae.check_header:
            opae.data += create_opae_header(opae,obj,cr,uid,data,context,transaction_type='00') + '\n'
            opae.transaction_id += 1
        
        opae.data += create_opae(opae, obj, cr, uid, data, context) +'\n'
        
    opae.transaction_id += 1
    opae.data += create_opae_footer(opae,obj,cr,uid,data,context)
            
    opae_data = base64.encodestring(opae.data.encode('latin1'))
    return {'opae': opae_data}

def create_opae(opae, obj, cr, uid, data, context):
    
    
    if opae.transaction_type == 'bvrpost' or opae.transaction_type == 'bvrbank':
        opae_string = create_opae_header(opae,obj,cr,uid,data,context,transaction_type='28')[:50]
        
    if opae.transaction_type == 'bvpost':
        opae_string = create_opae_header(opae,obj,cr,uid,data,context,transaction_type='22')[:50]
        
    if opae.transaction_type == 'bvbank':
        opae_string = create_opae_header(opae,obj,cr,uid,data,context,transaction_type='27')[:50]
    
    if opae.transaction_type == 'bvrpost' or opae.transaction_type == 'bvrbank' or opae.transaction_type == 'bvpost'or opae.transaction_type == 'bvbank':
        opae_string += opae.deposit_currency.code
        amount = str(int(round(opae.pool.get('res.currency').round(cr,uid,opae.line.currency,opae.line.amount_currency),2)*100))
        opae_string += '0'*(13-len(amount)) + amount + ' ' + opae.bonification_currency.name
    
        
    if opae.deposit_currency.code in opae.currencies:
        opae.currencies[opae.deposit_currency.code]['used'] += 1
        opae.currencies[opae.deposit_currency.code]['total_amount'] += int(amount)
    
    else:
        opae.currencies[opae.deposit_currency.code] = {'used':1,'total_amount':int(amount)}
    
#    if opae.transaction_type == 'bvrpost' or opae.transaction_type == 'bvrbank' or opae.transaction_type == 'bvpost' and not opae.country_code in ['CH','LI']:
#        raise wizard.except_wizard(('Error'), ('Country not supported by OPAE\n' \
#                 'Country code: %s\n') % (opae.country_code))
    opae_string += opae.country_code
        
    if opae.transaction_type == 'bvbank':
        if 8>len(opae.bic)!=0:
            raise wizard.except_wizard(('Error'),('Error in bic.\nIf iban is present, just delete bic'))
        
        opae_string += ' '*(15-len(opae.bic)) + opae.bic
        
    if opae.transaction_type == 'bvpost':
        if opae.titi_postal_account_number:
            first = opae.titi_postal_account_number[:2]
            second = opae.titi_postal_account_number[3:-2]
            third = opae.titi_postal_account_number[-1:]
            second = '0'*(6-len(second))+second
            opae_string += first+second+third
    
        else:
            raise wizard.except_wizard(('Error'), ('Missing postal account number'))
    
        opae_string += ' '*6
        
    if opae.transaction_type == 'bvbank' and not opae.toto_iban and not opae.toto_postal_account_number:
        raise wizard.except_wizard(('Error'),('Missing IBAN or Postal account number'))
    
    if opae.transaction_type == 'bvpost' or opae.transaction_type == 'bvbank':
        if opae.transaction_type == 'bvbank' and not opae.toto_iban:
            if opae.toto_postal_account_number:
                temp=opae.toto_postal_account_number.split('-')
                temp2 = ''
                for i in temp:
                    temp2 += i
                opae_string +=temp2[:2]+'0'*(9-len(temp2))+temp2[2:]
        else:
            opae_string += opae.toto_iban + ' '*(35-len(opae.toto_iban))
            
    if opae.transaction_type == 'bvbank':
        opae_string += ' '*(35-len(opae.titi_bank_name)) + opae.titi_bank_name 
        opae_string += ' '*(35-len(opae.titi_bank_add_designation)) + opae.titi_bank_add_designation
        opae_string += ' '*(35-len(opae.titi_bank_street)) + opae.titi_bank_street 
        opae_string += opae.titi_bank_npa + ' ' * (10-len(opae.titi_bank_npa)) 
        opae_string += ' '*(25-len(opae.titi_bank_city)) + opae.titi_bank_city
        
    if opae.transaction_type == 'bvpost':
        opae_string += ' '*(35-len(opae.titi_name)) + opae.titi_name
        opae_string += ' '*(35-len(opae.titi_add_designation)) + opae.titi_add_designation
        opae_string += ' '*(35-len(opae.titi_street)) +opae.titi_street
        
        if len(opae.titi_npa) != 4 and not opae.titi_npa == '':
            raise wizard.except_wizard(('Error'), ('Wrong NPA'))
        
        opae_string += opae.titi_npa or ' '*4
        opae_string += ' '*6
        opae_string += ' '*(25-len(opae.titi_city)) + opae.titi_city
        
    if opae.transaction_type == 'bvpost' or opae.transaction_type == 'bvbank':
        opae_string += ' '*(35-len(opae.toto_name)) + opae.toto_name
        opae_string += ' '*(35-len(opae.toto_add_designation)) +opae.toto_add_designation
        opae_string += ' '*(35-len(opae.toto_street)) + opae.toto_street
        
        if len(opae.toto_npa) != 4 and not opae.toto_npa == '':
            raise wizard.except_wizard(('Error'), ('Wrong NPA'))
        
        opae_string += opae.toto_npa or ' '*4
        opae_string += ' '*6
        opae_string += ' '*(25-len(opae.toto_city)) +opae.toto_city
        opae_string += ' '*(35-len(opae.communication_bloc_1)) + opae.communication_bloc_1
        opae_string += ' '*(35-len(opae.communication_bloc_2)) + opae.communication_bloc_2
        
        if not opae.communication_bloc_3:
            opae.communication_bloc_3 = ' '*35
        
        opae_string += ' '*(35-len(opae.communication_bloc_3)) + opae.communication_bloc_3
        
        if not opae.communication_bloc_4:
            opae.communication_bloc_4 = ' '*35
        opae_string += ' '*(35-len(opae.communication_bloc_4)) + opae.communication_bloc_4
        opae_string += ' '*4
        opae_string += ' '*(35-len(opae.tata_name)) + opae.tata_name
        opae_string += ' '*(35-len(opae.tata_add_designation)) + opae.tata_add_designation
        opae_string += ' '*(35-len(opae.tata_street)) + opae.tata_street
        
        if len(opae.tata_npa) != 4 and not opae.tata_npa == '':
            raise wizard.except_wizard(('Error'), ('Wrong NPA'))
        
        opae_string += opae.tata_npa or ' '*4
        opae_string += ' '*6
        opae_string += ' '*(25-len(opae.tata_city)) + opae.tata_city
        opae_string += ' '*14    
            
    if opae.transaction_type == 'bvrpost' or opae.transaction_type == 'bvrbank':
        opae_string += opae.modulo_11_digit
                
        bvr_ad_num = opae.bvr_adherent_num.split('-')
        print bvr_ad_num
        if len(bvr_ad_num) == 1:
            if not bvr_ad_num[0]:
                raise wizard.except_wizard(('Error'), ('Please enter a BVR adherent number 1'))
            if len(bvr_ad_num[0])!=5:
                raise wizard.except_wizard(('Error'), ('Please enter BVR adherent number with -'))
            opae_string += '0000' + bvr_ad_num
        
        elif len(bvr_ad_num) == 3:
            if len(bvr_ad_num[1]) > 6 or len(bvr_ad_num[0]) > 2:
                raise wizard.except_wizard(('Error'),('Invalid BVR adherent number 2'))

            opae_string += '0'*(2-len(bvr_ad_num[0])) + bvr_ad_num[0] + '0'*(6-len(bvr_ad_num[1])) + bvr_ad_num[1] + bvr_ad_num[2]
        
        else:
            raise wizard.except_wizard(('Error'), ('Invalid BVR adherent number 3'))
        
        opae_string += opae.reference
        opae_string += opae.sender_reference
        opae_string += ' '*555
    return opae_string + ' '*(700-len(opae_string))

def create_opae_header(opae, obj, cr, uid, data, context, transaction_type=-1):
    opae_string = '036'
    if opae.maturity_date < DateTime.strptime(str(DateTime.now())[:10],'%Y-%m-%d'):
        raise wizard.except_wizard(('Warning'),('Payment date must be at least today\nToday used instead.'))
        opae.maturity_date = DateTime.strptime(str(DateTime.now())[:10],'%Y-%m-%d')
        opae_string += str(opae.maturity_date.year)[-2:]
    
    if not opae.maturity_date:
        raise wizard.except_wizard(('Error'), ('Missing maturity date \n' \
                    'for the payment line: %s\n') % (opae.line._id))
    
    if len(str(opae.maturity_date.month)) == 1:
        opae_string += '0' + str(opae.maturity_date.month)
    
    else:
        opae_string += str(opae.maturity_date.month)
    
    if len(str(opae.maturity_date.day)) == 1:
        opae_string += '0' + str(opae.maturity_date.day)
    
    else:
        opae_string += str(opae.maturity_date.day)
    
    opae_string += '0' * 5 + '1'
    
    if not opae.debit_account_number:
        raise wizard.except_wizard(('Error'), ('Missing debit account number \n' \
                     'for payment: %s\n') % (opae.payment._id))
    
    while len(opae.debit_account_number[2:-1]) < 6:
        opae.debit_account_number = opae.debit_account_number[:2] + '0' + opae.debit_account_number[2:]
    opae_string += opae.debit_account_number
    
    while len(opae.debit_tax_account_number[2:-1]) < 6:
        opae.debit_tax_account_number = opae.debit_tax_account_number[:2] + '0' + opae.debit_tax_account_number[2:]
    opae_string += opae.debit_tax_account_number
    
    if len(str(opae.line.currency._id)) < 2:
        order_id = '0' + str(opae.line.currency._id)
    else:
        order_id = opae.line.currency._id
        
    opae_string += order_id    
    if not transaction_type == -1:
        if not type(transaction_type) == str:
            raise wizard.except_wizard(('Error'), ('OPAE type must be string'))
        if not transaction_type in ['00','22','27','28','97']:
            raise wizard.except_wizard(('Error'), ('Type doesn\'t exists or isn\'t supported yet.'))
        
    else:
        raise wizard.except_wizard(('Error'),('problème de type d\'enregistrement à la position 36 du header'))
    
    opae_string += transaction_type
    
    transaction_id = str(opae.transaction_id)
    transaction_id = '0' * (6-len(transaction_id)) + transaction_id
        
    opae_string += transaction_id + '0' * 7
    opae_string += ' ' * 650
    
    opae.check_header = True
    return opae_string
    
def create_opae_footer(opae, obj, cr, uid, data, context):
    opae_string = ''
    opae_string += create_opae_header(opae,obj,cr,uid,data,context,transaction_type='97')[:50]
    
    if len(opae.currencies) > 15:
        wizard.except_wizard(('Error'),('There are too many currencies used in this payment order.\nMaximum authorised by OPAE : 15\nCurrent payment order contains %s currencies') % (len(opae.currencies)))
    
    for currency in opae.currencies:
        opae_string += currency
        used = str(opae.currencies[currency]['used'])
        
        while len(used) < 6:
            used = '0' + used
        
        opae_string += used
        total_amount = str(opae.currencies[currency]['total_amount'])
        
        while len(total_amount) < 13:
            total_amount = '0' + total_amount
        
        opae_string += total_amount
    
    for i in range (15-len(opae.currencies)):
        opae_string += '0' * 22
    
    opae_string += ' '*320    
    return opae_string
        


class wizard_opae_create(wizard.interface):
    states = {
        'init' : {
            'actions' : [_prepare_opae],
            'result' : {'type' : 'form',
                'arch' : FORM,
                'fields' : FIELDS,
                'state' : [('end', 'OK', 'gtk-ok', True)]
            }
        },
    }

wizard_opae_create('account.opae_create')
# vim:expanopaeb:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
