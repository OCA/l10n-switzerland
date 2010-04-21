# -*- encoding: utf-8 -*-
#
#  opae_wizard.py
#  l10n_ch
#
#  Created by J. Bove
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
### Complete rewriting of this code should be done
import wizard
import pooler
from mx import DateTime
import pdb
import base64
"""Code under developpement not functional YET"""

FORM = """<?xml version="1.0"?>
<form string="OPAE file creation - Results">
<separator colspan="4" string="Clic on 'Save as' to save the OPAE file :" />
    <field name="opae"/>
</form>"""

FIELDS = {
        'opae': {
        'string': 'DTA File',
        'type': 'binary',
        'readonly': True,
    },
}

class OPAELine(object):
    """OPAE Line contain in OPAE File"""
    def __init__(self):
        self.sector = ''
        self.data = ''
        self.compo = {}
        

    ## @param self The object pointer.
    ## @payment the current payment order
    ## @line the current line
    def get_date(self, payment, line):
        """Return the right OPAE Line date"""
        if payment.date_prefered == 'due' and line.ml_maturity_date :
            return DateTime.strptime(line.ml_maturity_date, '%Y-%m-%d')
        if  payment.date_prefered == 'fixed' and payment.date_planned :
            return DateTime.strptime(payment.date_planned, '%Y-%M-%d')
        return DateTime.today()
        
        
    def set_communication(self, linebr):
        "Split line comment in 4 block of 35 chars"
        raw_comment = ''
        if linebr.communication and linebr.communication2:
             raw_comment = line.communication + ' ' + line.communication2
        else:
             raw_comment = line.communication 
        for i in xrange(0,140,35) :
            self.compo['communication_bloc_'+str(i/35+1)] = raw_comment[i:i+35]
            
    def set_address(self, prefix, addresses):
        for addr in address:
            if addr.type=='default':
                op_line.compo[prefix+'_street'] = addr.street and addr.street or u''
                op_line.compo[prefix+'_street'] += u' '
                op_line.compo[prefix+'_street'] += addr.street2 and addr.street2 or u''
                op_line.compo[prefix+'_street'].replace(u"\n",u' ')
                op_line.compo[prefix+'_street'] = op_line.compo['add_street'][0:34]
                op_line.compo[prefix+'_npa'] = addr.zip or u''
                op_line.compo[prefix+'_city'] =  addr.city or u''
                
        
        
class OPAE(object):
    "OPAE File representation"
    ##code equivalence between 
    ## OpenERP and Postfinance
    CODEEQUIV = {
        'bvrpost' : '28',
        'bvrbank' : '28',
        'bvpost'  : '22',
        'bvbank'  : '27', 
        '00'      : '00',
        '97'      : '97'
     
     }

    
    def __init__(self, cursor, uid, data, pool, context=None):
        ## Openerp Pooler
        self.pool = pool
        ## Psycopg cursor
        self.cursor = cursor
        ## OpenERP user id 
        self.uid = uid
        ## OpenERP wizard data
        self.wizdata = data
        # OpenERP current context 
        self.context = context
        pay_id = data['ids']
        if isinstance(pay_id, list) :
            pay_id = pay_id[0]
        ## Current payment order
        self.payment_order = self.pool.get('payment.order').browse(
                                                                    cursor, 
                                                                    uid, 
                                                                    pay_id
                                                                   )
        ## OPAE string component                                                           
        self.compo =  {}
        ## Boolean that will be set to true it OPAE header was generated
        self.has_header = False
        ## Currency dict used for footer computation
        ## for more information look chapter 4.12 enregistrement total
        self.currencies = {}
        ## OPAE lines form of dict
        self.lines = []
        self.numers = {}
        ## Enregistrement de test a ne pas confondre avec secteur de controle
        self.header = ''
        if not self.payment_order.mode :
            raise wizard.except_wizard(_('Error'),
            _('No Payment mode define'))
        self.debit_account_number = self.payment_order.mode.\
                                    bank_id.bvr_number.replace(u'-',u'')
        ## header line representation                            
        self.headline = OPAELine()
        self.headline.compo['line_date'] = self.payment_order.date_planned
        self.headline.compo['debit_account_number'] = self.debit_account_number
        self.headline.compo['bonification_currency'] = None
        self.headline.compo['transaction_type'] = '00'
        self.headline.compo['transaction_id'] = 0
        ### array of unicode string that will be used for joined
        ##  see PEP for details
        self.result_array = []
        
       
        
        
        
        
    def get_lines_order_num(self, date, currency):
        key = (str(date), currency)
        if self.numers.has_key(key) :
            self.numers[key] += 1
            to_return =  self.numers[key]
            if to_return > 99 :
                raise wizard.except_wizard(_('Error'),
                    _('Order can not exced 99 lines per date and currency'))
            return unicode(to_return).rjust(2,'0')
        else :
            self.numers[key] = 1
            return '01'
                
        


    
    def parse_payment_lines(self):
        """Compute the OPAE file output"""
        # 'Destinataire' and 'beneficiare' differences are
        # destinataire has his own post account
        # beneficiare has is account trought a bank that use a postal account
        # All term can be retrieved in 
        # Postfinance Tech spech "Enregistrement OPAE"
        counter = 0
        for line in self.payment.line_ids:
            counter += 1
            ## we have an unique id per OPAE line
            op_line = OPAELine()
            self.lines.append(op_line)
            ## we set limit execution date see chapter 4.2 date d'echeance
            op_line.compo['line_date'] = op_line.get_date(self.payment, line)
            ## we set the destination account 
            ##  see chapter 4.2 numero de compte de débit
            op_line.compo['debit_account_number'] = self.payment_order.mode.\
                                    bank_id.bvr_number.replace(u'-',u'')
            ## chapter 4.2 numero de compte de debit des taxes
            op_line.compo['debit_tax_account_number'] = op_line.compo['debit_account_number']
            
            ## We define line order number chapter 4.2 numero d'ordre
            op_line.compo['order_number'] = self.get_lines_order_num(
                                                  op_line.compo['line_date'],
                                                  line.currency.code
                                                )
            state = line.bank_id.state or self.payment_order.mode.bank_id.state
            ## chapter 4.2 genre de transaction
            op_line.compo['transaction_type'] = state
            ## chapter 4.2 no courant de transaction
            op_line.compo['transaction_id'] = counter
            ## chapter 4.x Code ISO Monnaie de Depot 
            op_line.compo['deposit_currency'] = line.currency.code
            ## chap 4.x montant du depot
            op_line.compo['deposit_amount'] = line.amount_currency
            ## chap 4.x Code ISO Monnaie de bonnification
            op_line.compo['bonification_currency'] = line.currency.code
            ## chap 4.x code ISO pays
            op_line.compo['country_code'] = self.payment_order.user_id.company_id.\
                partner_id.country.code
            ## chapter 4.x No de compte postal du destinataire
            op_line.compo['dest_postal_account_number'] = line.bank_id.post_number or u''
            ## chapter 4.x No de compte postal du beneficiaire
            op_line.compo['benef_postal_account_number'] = line.bank_id.post_number or u''
            ## chapter 4.x No IBAN du destinaire/beneficiaire
            op_line.compo['dest_iban'] = line.bank_id.iban or u''
            ## chapter 4.x No IBAN du destinaire/beneficiaire
            op_line.compo['benef_iban'] = line.bank_id.iban or u''
            ## adresse du beneficiaire/destinataire
            op_line.compo['dest_iban' ] =  op_line.compo['dest_iban'].upper()
            op_line.compo['add_name'] = ''
            op_line.compo['add_street'] = ''
            op_line.compo['add_npa'] = ''
            op_line.compo['add_city'] = ''
            if line.partner_id:
                partner = line.partner_id
                op_line.compo['add_name'] = partner.name
                op_line.set_address('add', partner.address)
                
            op_line.compo['add_designation'] = ''
            op_line.set_communication(line)
            ## principal correspond to the source of payment
            op_line.compo['principal_name'] = ''
            op_line.compo['principal_street'] = ''
            op_line.compo['principal_npa'] = ''
            op_line.compo['principal_city'] = ''
            if line.order_id.mode.bank_id.partner_id :
                partner = line.order_id.mode.bank_id.partner_id
                op_line.compo['principal_name'] = partner.name
                op_line.set_address('principal', partner.address)
            op_line.compo['principal_designation'] = ''
            op_line.compo['bic'] = line.bank_id.bank and line.bank_id.bank.bic or ''
                        
            op_line.compo['benef_bank_npa'] = line.bank_id.bank and line.bank_id.bank.zip or ''
            op_line.compo['benef_bank_name'] = line.bank_id.bank and line.bank_id.bank.name or ''
            op_line.compo['benef_bank_add_designation'] = ''
            op_line.compo['benef_bank_street'] = self.payment_order.mode.bank_id.bank and self.payment_order.mode.bank_id.bank.street or ''
            op_line.compo['benef_bank_city'] = line.bank_id.bank and line.bank_id.bank.city or ''
            op_line.compo['benef_add_designation'] = ''
            op_line.compo['modulo_11_digit'] = '  '
            op_line.compo['bvr_adherent_num'] = line.bank_id.bvr_adherent_num or line.bank_id.bvr_number or ''
            op_line.compo['reference'] = line.communication
            op_line.compo['sender_reference'] = ' ' * 35
        
    def compute(self):
        """Compute the OPAE file output"""
        self.header = self.create_control_sector(self.headline)+' '*650  
        self.result_array.append(self.header)  
        for parsed_line in self.lines :
            pass
        
            
            


def _prepare_opae(obj, cursor, uid, data, context):
    pool = pooler.get_pool(cursor.dbname)
    opae = OPAE(cursor, uid, data, pool, context)
    opae.parse_payment_lines()
    opae.compute()
    return {'opae': opae.get_result_64()}

def create_opae(opae, obj, cursor, uid, data, context):
    
    
    if opae.transaction_type == 'bvrpost' or opae.transaction_type == 'bvrbank':
        opae_string = create_opae_header(opae,obj,cursor,uid,data,context,transaction_type='28')[:50]
        
    if opae.transaction_type == 'bvpost':
        opae_string = create_opae_header(opae,obj,cursor,uid,data,context,transaction_type='22')[:50]
        
    if opae.transaction_type == 'bvbank':
        opae_string = create_opae_header(opae,obj,cursor,uid,data,context,transaction_type='27')[:50]
    
    if opae.transaction_type == 'bvrpost' or opae.transaction_type == 'bvrbank' or opae.transaction_type == 'bvpost'or opae.transaction_type == 'bvbank':
        opae_string += opae.deposit_currency.code
        amount = str(int(round(opae.pool.get('res.currency').round(cursor,uid,opae.line.currency,opae.line.amount_currency),2)*100))
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
        if opae.benef_postal_account_number:
            first = opae.benef_postal_account_number[:2]
            second = opae.benef_postal_account_number[3:-2]
            third = opae.benef_postal_account_number[-1:]
            second = '0'*(6-len(second))+second
            opae_string += first+second+third
    
        else:
            raise wizard.except_wizard(('Error'), ('Missing postal account number'))
    
        opae_string += ' '*6
        
    if opae.transaction_type == 'bvbank' and not opae.dest_iban and not opae.dest_postal_account_number:
        raise wizard.except_wizard(('Error'),('Missing IBAN or Postal account number'))
    
    if opae.transaction_type == 'bvpost' or opae.transaction_type == 'bvbank':
        if opae.transaction_type == 'bvbank' and not opae.dest_iban:
            if opae.dest_postal_account_number:
                temp=opae.dest_postal_account_number.split('-')
                temp2 = ''
                for i in temp:
                    temp2 += i
                opae_string +=temp2[:2]+'0'*(9-len(temp2))+temp2[2:]
        else:
            opae_string += opae.dest_iban + ' '*(35-len(opae.dest_iban))
            
    if opae.transaction_type == 'bvbank':
        opae_string += ' '*(35-len(opae.benef_bank_name)) + opae.benef_bank_name 
        opae_string += ' '*(35-len(opae.benef_bank_add_designation)) + opae.benef_bank_add_designation
        opae_string += ' '*(35-len(opae.benef_bank_street)) + opae.benef_bank_street 
        opae_string += opae.benef_bank_npa + ' ' * (10-len(opae.benef_bank_npa)) 
        opae_string += ' '*(25-len(opae.benef_bank_city)) + opae.benef_bank_city
        
    if opae.transaction_type == 'bvpost':
        opae_string += ' '*(35-len(opae.benef_name)) + opae.benef_name
        opae_string += ' '*(35-len(opae.benef_add_designation)) + opae.benef_add_designation
        opae_string += ' '*(35-len(opae.benef_street)) +opae.benef_street
        
        if len(opae.benef_npa) != 4 and not opae.benef_npa == '':
            raise wizard.except_wizard(('Error'), ('Wrong NPA'))
        
        opae_string += opae.benef_npa or ' '*4
        opae_string += ' '*6
        opae_string += ' '*(25-len(opae.benef_city)) + opae.benef_city
        
    if opae.transaction_type == 'bvpost' or opae.transaction_type == 'bvbank':
        opae_string += ' '*(35-len(opae.dest_name)) + opae.dest_name
        opae_string += ' '*(35-len(opae.dest_add_designation)) +opae.dest_add_designation
        opae_string += ' '*(35-len(opae.dest_street)) + opae.dest_street
        
        if len(opae.dest_npa) != 4 and not opae.dest_npa == '':
            raise wizard.except_wizard(('Error'), ('Wrong NPA'))
        
        opae_string += opae.dest_npa or ' '*4
        opae_string += ' '*6
        opae_string += ' '*(25-len(opae.dest_city)) +opae.dest_city
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

    def create_control_sector(self, opae_line):
        vals = line.compo
        opae_string =[] 
        ## chapter 4.2 secteur de controle -> identificateur de fichier
        opae_string.appends('036')
        if not vals.get('line_date', False) :
            raise wizard.except_wizard(
                                        ('Error'), 
                                        ('Missing date planned  \n' \
                                        'for the payment order line: %s\n')
                                        )
        planned_date =  DateTime.strptime(self.payment_order.date_planned, '%Y-%M-%d')
        if planned_date < DateTime.today():
            raise wizard.except_wizard(
                                        ('Warning'),
                                        ('Payment date must be at least today\n \
                                           Today used instead.')
                                       )    
        ## chapter 4.2 secteur de controle -> date decheance
        opae_string.append(planned_date.strftime("%y%m%d"))
        ## chapter 4.2 secteur de controle -> reserve + element de commande fix val
        opae_string.append('0'* 5 + '1')
        ## chapter 4.2 secteur de controle -> No de compte de debit

        opae_string.append(vals['debit_account_number'].rjust(6,'0'))
        ## chapter 4.2 secteur de controle -> N0 de compte de debit de tax
        opae_string.append(vals['debit_account_number'].rjust(6,'0'))
        opae_string.append(
                            self.get_lines_order_num(
                                                    planned_date, 
                                                    vals['bonification_currency']
                                                    )
                           )
        
  
        try:
            opae_string.append(self.CODEEQUIV[vals['transaction_type']])
        except Exception, e:
            raise wizard.except_wizard(('Error'), ('Type doesn\'t exists or isn\'t supported yet.'))
        
        transaction_id = unicode(vals['transaction_id'].rjust(6,'0'))
        opae_string.append(transaction_id)
        opae_string.append('0' * 7)
        return u''.join(opae_string)
    
def create_opae_footer(opae, obj, cursor, uid, data, context):
    opae_string = ''
    opae_string += create_opae_header(opae,obj,cursor,uid,data,context,transaction_type='97')[:50]
    
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