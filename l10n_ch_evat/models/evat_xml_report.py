# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import pprint
import base64
import logging
from StringIO import StringIO
from contextlib import closing
from lxml import etree
from lxml.builder import ElementMaker
from collections import namedtuple
from datetime import datetime
from odoo import models, fields, _, api
from odoo.modules import get_module_resource


_logger = logging.getLogger(__name__)


TARGET_MOVES_SELECTION = [('posted', 'Posted entries'),
                          ('all', 'All entries')]

ECH_NS = {
    'eCH-0217': 'http://www.ech.ch/xmlns/eCH-0217/1',
    'eCH-0097': 'http://www.ech.ch/xmlns/eCH-0097/3',
    'eCH-0058': 'http://www.ech.ch/xmlns/eCH-0058/5',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}


CODE_TAGS = {
    '220': 'vat_tag_220',
    '221': 'vat_tag_221',
    '225': 'vat_tag_225',
    '230': 'vat_tag_230',
    '235': 'vat_tag_235',
    '280': 'vat_tag_280',
    '301': 'vat_tag_301_a',
    '302': 'vat_tag_302_a',
    '311': 'vat_tag_311_a',
    '341': 'vat_tag_341_a',
    '342': 'vat_tag_342_a',
    '381': 'vat_tag_381_a',
    '382': 'vat_tag_382_a',
    '400': 'vat_tag_400',
    '405': 'vat_tag_405',
    '410': 'vat_tag_410',
    '415': 'vat_tag_415',
    '420': 'vat_tag_420',
    'dedouanement': 'vat_tag_dedouanement',
}


ELEMENT_CODE_MAPPING = {
    'totalConsideration': '200',
    'suppliesToForeignCountries': '220',
    'suppliesAbroad': '221',
    'transferNotificationProcedure': '225',
    'suppliesExemptFromTax': '230',
    'reductionOfConsideration': '235',
    'variousDeduction': '280',
    # 'opted': '205', not existing in Odoo
    'suppliesPerTaxRate': ['301', '302', '311', '341', '342'],
    'acquisitionTax': ['381', '382'],
    'inputTaxMaterialAndServices': '400',
    'inputTaxInvestments': '405',
    'subsequentInputTaxDeduction': '410',
    'inputTaxCorrections': '415',
    'inputTaxReductions': '420',
    # 'subsidies': '900', not existing in Odoo
    # 'donations': '910', not existing in Odoo
}


Code = namedtuple('Code', ['tag', 'balance', 'taxes'])


class EvatXmlReport(models.Model):

    _name = 'evat.xml.report'

    name = fields.Char(required=True)
    start_date = fields.Date()
    end_date = fields.Date()
    generation_date = fields.Date(readonly=True)
    target_moves = fields.Selection(TARGET_MOVES_SELECTION, required=True)
    state = fields.Selection([('draft', 'Draft'), ('generated', 'Generated')],
                             default='draft', required=True)
    # TODO translate labels (Caution legal)
    type_of_submission = fields.Selection([('1', 'Premier dépôt'),
                                           ('2', 'Décompte rectificatif'),
                                           ('3', 'Concordance annuelle')],
                                          required=True)
    company_id = fields.Many2one('res.company',
                                 default=lambda l: l.env.user.company_id)

    # Technical helpers

    @api.multi
    def _extend_domain(self, domain):
        base_domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]
        if self.target_moves == 'posted':
            base_domain.append(('move_id.state', '=', 'posted'))
        base_domain.extend(domain)
        return base_domain

    @api.model
    def _format_turnovers(self, turnovers_per_rate):
        res = []
        for rate, turnover in turnovers_per_rate.iteritems():
            res.append({
                'taxRate': rate,
                'turnover': turnover,
            })
        return res

    @api.model
    def _sum_turnovers(self, turnovers_per_rate):
        amount = 0
        for rate, turnover in turnovers_per_rate.iteritems():
            amount += rate / 100 * turnover
        return amount

    @api.multi
    def _get_balance_from_tax_tag(self, tax_tag, domain_on_tax_line=False):
        if isinstance(tax_tag, basestring):
            tax_tag = self.env.ref(tax_tag, raise_if_not_found=False)
        if not tax_tag:
            return 0
        if domain_on_tax_line:
            domain = [('tax_line_id.tag_ids', 'in', tax_tag.ids)]
        else:
            domain = [('tax_ids.tag_ids', 'in', tax_tag.ids)]
        move_lines = self.env['account.move.line'].search(
            self._extend_domain(domain)
        )
        amount = 0
        for ml in move_lines:
            amount -= ml.balance
        return amount

    @api.multi
    def _get_balance_from_tax(self, tax):
        if isinstance(tax, basestring):
            tax = self.env.ref(tax, raise_if_not_found=False)
        if not tax:
            return 0
        domain = [
            ('tax_ids', 'in', tax.ids)
        ]
        move_lines = self.env['account.move.line'].search(
            self._extend_domain(domain)
        )
        amount = 0
        for ml in move_lines:
            amount -= ml.balance
        return amount

    @api.multi
    def _build_codes_balances_dict(self):
        balances = {}
        for code, xml_tag in CODE_TAGS.iteritems():
            tax_tag = self.env.ref('l10n_ch.%s' % xml_tag,
                                   raise_if_not_found=False)
            if not tax_tag:
                continue
            if code in ['400', '405', '410', '415', '420']:
                balance = -self._get_balance_from_tax_tag(
                    tax_tag, domain_on_tax_line=True)
            else:
                balance = self._get_balance_from_tax_tag(tax_tag)
            taxes = self.env['account.tax'].search([
                ('tag_ids', 'in', [tax_tag.id])])
            balances[code] = Code(tax_tag, balance, taxes)
        return balances

    @api.multi
    def _get_turnovers_per_rate(self, codes_balances, codes_to_extract):
        taxes = self.env['account.tax']
        for code in codes_to_extract:
            taxes |= codes_balances.get(code).taxes
        rates = set(taxes.mapped('amount'))
        # TODO Ignore taxes with negative rate or throw error ?
        turnovers_per_rate = {r: 0 for r in rates if r > 0}
        for tax in taxes:
            if tax.amount > 0:
                turnovers_per_rate[tax.amount] += self._get_balance_from_tax(
                    tax)
        return turnovers_per_rate

    @api.model
    def _safe_balance(self, codes_dict, key):
        return codes_dict.get(key) and codes_dict.get(key).balance or 0

    # Business oriented methods

    # Complete XML report

    @api.multi
    def generate_xml_report(self):
        _logger.info('Generating XML E-VAT Report')
        codes_balances = self._build_codes_balances_dict()
        xml_dict = {
            'VATDeclaration': {
                'generalInformation': self._get_generalInformation(),
                'turnoverComputation': self._get_turnoverComputation(
                    codes_balances),
                'effectiveReportingMethod':
                    self._get_effectiveReportingMethod(codes_balances),
                'payableTax': self._get_payableTax(codes_balances),
                'otherFlowsOfFunds': self._get_otherFlowsOfFunds(
                    codes_balances),
            }
        }
        pprint.pprint('')
        pprint.pprint(codes_balances)
        pprint.pprint(xml_dict)

        xml_vatdeclaration = self._translate_to_xml(xml_dict)
        print(etree.tostring(xml_vatdeclaration, pretty_print=True))
        self.validate_with_xsd(xml_vatdeclaration)
        res = self.write_to_file(xml_vatdeclaration)
        self.write({
            'state': 'generated',
            'generation_date': fields.Date.today()
        })
        _logger.info('XML E-VAT Report successfully generated')
        # TODO Refresh the form view ?
        return res

    # generalInformation section

    @api.multi
    def _get_generalInformation(self):
        return {
            'uid': self._get_uid(),
            'organisationName': self.company_id.name,
            'generationTime': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'reportingPeriodFrom': self.start_date,
            'reportingPeriodTill': self.end_date,
            'typeOfSubmission': self.type_of_submission,
            'formOfReporting': '1',  # TODO Check with FCI if right
            'businessReferenceId': 'a',  # TODO Check with FCI
            'sendingApplication': self._get_sendingApplication(),
        }

    @api.multi
    def _get_uid(self):
        # TODO do we want a check ?
        uidOrganisationIdCategorie = 'CHE'
        # split VAT or MWST from and get only number
        uidOrganisationId = self.company_id.vat.split(' ')[0].split('CHE-')[-1]
        return {
            'uidOrganisationIdCategorie': uidOrganisationIdCategorie,
            'uidOrganisationId': uidOrganisationId,
        }

    @api.multi
    def _get_sendingApplication(self):
        # TODO What do we really need here ?
        module = self.env['ir.module.module'].search([
                ('name', '=', 'l10n_ch_evat')])
        return {
            'manufacturer': 'Camptocamp, OCA',
            'product': "Odoo %s" % module.name,
            'productVersion': module.latest_version,
        }

    # turnoverComputation section

    @api.multi
    def _get_turnoverComputation(self, codes_balances):
        return {
            'totalConsideration': self._get_totalConsideration(codes_balances),
            'suppliesToForeignCountries': self._safe_balance(codes_balances,
                                                             '220'),
            'suppliesAbroad': self._safe_balance(codes_balances,
                                                 '221'),
            'transferNotificationProcedure': self._safe_balance(codes_balances,
                                                                '225'),
            'suppliesExemptFromTax': self._safe_balance(codes_balances,
                                                        '230'),
            'reductionOfConsideration': self._safe_balance(codes_balances,
                                                           '235'),
            'variousDeduction': self._get_variousDeduction(codes_balances),
        }

    @api.multi
    def _get_totalConsideration(self, codes_balances):
        amount = 0
        for tax_tag in [
            '220', '230', '301', '302', '311', '341', '342',
        ]:
            amount += self._safe_balance(codes_balances, tax_tag)
        return amount

    @api.multi
    def _get_variousDeduction(self, codes_balances):
        return {
            'amountVariousDeduction':
                self._safe_balance(codes_balances, '280'),
            'descriptionVariousDeduction': 'token',  # TODO WTF is needed here?
        }

    # effectiveReportingMethod section

    @api.multi
    def _get_effectiveReportingMethod(self, codes_balances):
        return {
            'grossOrNet': 1,
            'opted': '0',  # TODO Check with FCI
            'suppliesPerTaxRate': self._format_turnovers(
                self._get_turnovers_per_rate(
                    codes_balances, ['301', '302', '311', '341', '342'])),
            'acquisitionTax': self._format_turnovers(
                self._get_turnovers_per_rate(
                    codes_balances, ['381', '382'])),
            'inputTaxMaterialAndServices':
                self._get_inputTaxMaterialAndServices(),
            'inputTaxInvestments': self._safe_balance(codes_balances, '405'),
            'subsequentInputTaxDeduction':
                self._safe_balance(codes_balances, '410'),
            'inputTaxCorrections': self._safe_balance(codes_balances, '415'),
            'inputTaxReductions': self._safe_balance(codes_balances, '420'),
        }

    @api.multi
    def _get_inputTaxMaterialAndServices(self):
        # Here we cannot sum the balances of 400 and dedouanement
        # so we recalculate the balance with a recset of both tags
        # TODO do we really need dedouanement and not only 400 ?
        tag_400 = self.env.ref(
            'l10n_ch.vat_tag_400', raise_if_not_found=True)
        tag_ded = self.env.ref(
            'l10n_ch.vat_tag_dedouanement', raise_if_not_found=True)
        domain = [
            '|', ('tax_ids.tag_ids', 'in', [tag_ded.id]),
            ('tax_line_id.tag_ids', 'in', [tag_400.id])
        ]
        move_lines = self.env['account.move.line'].search(
            self._extend_domain(domain)
        )
        amount = 0
        for ml in move_lines:
            amount += ml.balance
        return amount

    # payableTax section

    @api.multi
    def _get_payableTax(self, codes_balances):
        # To add
        suppliesPerTaxrate = self._get_turnovers_per_rate(
                    codes_balances, ['301', '302', '311', '341', '342'])
        acquisitionTax = self._get_turnovers_per_rate(
            codes_balances, ['381', '382'])
        inputTaxCorrections = self._safe_balance(codes_balances, '415')
        inputTaxReductions = self._safe_balance(codes_balances, '420')
        # To subtract
        inputTaxMaterialAndServices = self._get_inputTaxMaterialAndServices()
        inputTaxInvestments = self._safe_balance(codes_balances, '405')
        subsequentInputTaxDeduction = self._safe_balance(codes_balances, '410')

        vat_due = sum([
            self._sum_turnovers(suppliesPerTaxrate),
            self._sum_turnovers(acquisitionTax),
            inputTaxCorrections,
            inputTaxReductions
        ]) - sum([
            inputTaxMaterialAndServices,
            inputTaxInvestments,
            subsequentInputTaxDeduction,
        ])

        return vat_due

    # otherFlowsOfFunds section

    @api.multi
    def _get_otherFlowsOfFunds(self, codes_balances):
        # Codes not existing in odoo yet
        # TODO Check with FCI
        return {
            'subsidies': self._safe_balance(codes_balances, '900'),
            'donations': self._safe_balance(codes_balances, '910'),
        }

    # XML Generation

    @api.multi
    def _translate_to_xml(self, xml_dict):

        E217 = ElementMaker(namespace=ECH_NS.get('eCH-0217'),
                            nsmap=ECH_NS)
        E097 = ElementMaker(namespace=ECH_NS.get('eCH-0097'),
                            nsmap={'eCH-0097': ECH_NS.get('eCH-0097')})
        E058 = ElementMaker(namespace=ECH_NS.get('eCH-0058'),
                            nsmap={'eCH-0058': ECH_NS.get('eCH-0058')})

        vat_declaration = E217.VATDeclaration(
            E217.generalInformation(
                E217.uid(
                    E097.uidOrganisationIdCategorie(
                        xml_dict.get('VATDeclaration').get(
                            'generalInformation').get('uid').get(
                            'uidOrganisationIdCategorie')
                    ),
                    E097.uidOrganisationId(
                        xml_dict.get('VATDeclaration').get(
                            'generalInformation').get('uid').get(
                            'uidOrganisationId')
                    )
                ),
                E217.organisationName(
                    xml_dict.get('VATDeclaration').get(
                        'generalInformation').get('organisationName')
                ),
                E217.generationTime(
                    xml_dict.get('VATDeclaration').get(
                        'generalInformation').get('generationTime')
                ),
                E217.reportingPeriodFrom(
                    xml_dict.get('VATDeclaration').get(
                        'generalInformation').get('reportingPeriodFrom')
                ),
                E217.reportingPeriodTill(
                    xml_dict.get('VATDeclaration').get(
                        'generalInformation').get('reportingPeriodTill')
                ),
                E217.typeOfSubmission(
                    xml_dict.get('VATDeclaration').get(
                        'generalInformation').get('typeOfSubmission')
                ),
                E217.formOfReporting(
                    xml_dict.get('VATDeclaration').get(
                        'generalInformation').get('formOfReporting')
                ),
                E217.businessReferenceId(
                    xml_dict.get('VATDeclaration').get(
                        'generalInformation').get('businessReferenceId')
                ),
                E217.sendingApplication(
                    E058.manufacturer(
                        xml_dict.get('VATDeclaration').get(
                            'generalInformation').get(
                            'sendingApplication').get('manufacturer')
                    ),
                    E058.product(
                        xml_dict.get('VATDeclaration').get(
                            'generalInformation').get(
                            'sendingApplication').get('product')
                    ),
                    E058.productVersion(
                        xml_dict.get('VATDeclaration').get(
                            'generalInformation').get(
                            'sendingApplication').get('productVersion')
                    ),
                ),
            ),
            E217.turnoverComputation(
                E217.totalConsideration(
                    str(xml_dict.get('VATDeclaration').get(
                        'turnoverComputation').get(
                        'totalConsideration'))
                ),
                E217.suppliesToForeignCountries(
                    str(xml_dict.get('VATDeclaration').get(
                        'turnoverComputation').get(
                        'suppliesToForeignCountries'))
                ),
                E217.suppliesAbroad(
                    str(xml_dict.get('VATDeclaration').get(
                        'turnoverComputation').get(
                        'suppliesAbroad'))
                ),
                E217.transferNotificationProcedure(
                    str(xml_dict.get('VATDeclaration').get(
                        'turnoverComputation').get(
                        'transferNotificationProcedure'))
                ),
                E217.suppliesExemptFromTax(
                    str(xml_dict.get('VATDeclaration').get(
                        'turnoverComputation').get(
                        'suppliesExemptFromTax'))
                ),
                E217.reductionOfConsideration(
                    str(xml_dict.get('VATDeclaration').get(
                        'turnoverComputation').get(
                        'reductionOfConsideration'))
                ),
                E217.variousDeduction(
                    E217.amountVariousDeduction(
                        str(xml_dict.get('VATDeclaration').get(
                            'turnoverComputation').get(
                            'variousDeduction').get(
                            'amountVariousDeduction'))
                    ),
                    E217.descriptionVariousDeduction(
                        str(xml_dict.get('VATDeclaration').get(
                            'turnoverComputation').get(
                            'variousDeduction').get(
                            'descriptionVariousDeduction'))
                    )
                )
            ),
            E217.effectiveReportingMethod(
                E217.grossOrNet(
                    str(xml_dict.get('VATDeclaration').get(
                        'effectiveReportingMethod').get(
                        'grossOrNet'))
                ),
                E217.opted(
                    str(xml_dict.get('VATDeclaration').get(
                        'effectiveReportingMethod').get(
                        'opted'))
                ),
                *[E217.suppliesPerTaxRate(
                    E217.taxRate(
                        str(sup.get('taxRate'))
                    ),
                    E217.turnover(
                        str(sup.get('turnover'))
                    )
                ) for sup in xml_dict.get('VATDeclaration').get(
                            'effectiveReportingMethod').get(
                            'suppliesPerTaxRate')
                ] + [E217.acquisitionTax(
                    E217.taxRate(
                        str(acq.get('taxRate'))
                    ),
                    E217.turnover(
                        str(acq.get('turnover'))
                    )
                ) for acq in xml_dict.get('VATDeclaration').get(
                            'effectiveReportingMethod').get(
                            'acquisitionTax')
                ] + [
                    E217.inputTaxMaterialAndServices(
                        str(xml_dict.get('VATDeclaration').get(
                            'effectiveReportingMethod').get(
                            'inputTaxMaterialAndServices'))
                    ),
                    E217.inputTaxInvestments(
                        str(xml_dict.get('VATDeclaration').get(
                            'effectiveReportingMethod').get(
                            'inputTaxInvestments'))
                    ),
                    E217.subsequentInputTaxDeduction(
                        str(xml_dict.get('VATDeclaration').get(
                            'effectiveReportingMethod').get(
                            'subsequentInputTaxDeduction'))
                    ),
                    E217.inputTaxCorrections(
                        str(xml_dict.get('VATDeclaration').get(
                            'effectiveReportingMethod').get(
                            'inputTaxCorrections'))
                    ),
                    E217.inputTaxReductions(
                        str(xml_dict.get('VATDeclaration').get(
                            'effectiveReportingMethod').get(
                            'inputTaxReductions'))
                    )
                ]
            ),
            E217.payableTax(
                "{:.2f}".format(xml_dict.get('VATDeclaration').get(
                    'payableTax'))
            ),
            E217.otherFlowsOfFunds(
                E217.subsidies(
                    str(xml_dict.get('VATDeclaration').get(
                        'otherFlowsOfFunds').get(
                        'subsidies'))
                ),
                E217.donations(
                    str(xml_dict.get('VATDeclaration').get(
                        'otherFlowsOfFunds').get(
                        'donations'))
                )
            )
        )
        # Adds xsi:schemaLocation to VATDeclaration
        vat_declaration.attrib[
            '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'
        ] = 'http://www.ech.ch/xmlns/eCH-0217/1 eCH-0217-1-0.xsd'
        return vat_declaration

    @api.multi
    def validate_with_xsd(self, xml_vatdeclaration):
        xsd_path = get_module_resource(
                'l10n_ch_evat', 'documentation', 'eCH-0217-1-0.xsd'
        )
        with open(xsd_path, 'rb') as xsd_file:
            xmlschema_doc = etree.fromstring(' '.join(xsd_file.read().split()))
            xmlschema = etree.XMLSchema(xmlschema_doc)
            xmlschema.assertValid(xml_vatdeclaration)

    @api.multi
    def write_to_file(self, xml_vatdeclaration):
        with closing(StringIO()) as buf:
            buf.write(etree.tostring(xml_vatdeclaration,
                                     xml_declaration=True,
                                     pretty_print=True))
            out = base64.b64encode(buf.getvalue().encode('utf-8'))
        existing = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id)
        ])
        if existing:
            existing.unlink()
        # Create attachment
        att = self.env['ir.attachment'].create({
            'name': '%s.xml' % self.name.replace(' ', '_'),
            'res_model': self._name,
            'res_id': self.id,
            'datas': out,
            'datas_fname': '%s.xml' % self.name.replace(' ', '_'),
        })
        return {
            'type': 'ir.actions.act_url',
            'target': 'current',
            'url': '/web/content/%s/?download=true'
                   % att.id
        }
