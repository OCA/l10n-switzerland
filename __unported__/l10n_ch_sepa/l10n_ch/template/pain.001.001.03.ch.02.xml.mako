<%inherit file="pain.001.001.03.xml.mako"/>

<%block name="root">
<Document xmlns="http://www.six-interbank-clearing.com/de/pain.001.001.03.ch.02.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.six-interbank-clearing.com/de/pain.001.001.03.ch.02.xsd pain.001.001.03.ch.02.xsd">
</%block>

<%block name="InitgPty">
        <InitgPty>
          <Nm>${order.user_id.company_id.name}</Nm>
          <CtctDtls>
            <Nm>OpenERP - SEPA Payments - by Camptocamp</Nm>
            <Othr>${module_version}</Othr>
          </CtctDtls>
        </InitgPty>
</%block>

<%block name="CdtrAgt">
<%doc>\
        For type 1, Creditor Agent shouldn't be delivered
</%doc>\
   <%
   line=sepa_context['line']
   invoice = line.move_line_id.invoice
   %>
   % if not invoice.partner_bank_id.state == 'bvr':
    ${parent.CdtrAgt()}
   % endif
</%block>

<%block name="PmtTpInf">
<%doc>\
        Local Instrument
            Code
             or
            Proprietary

        Proprietary is required for types 1, 2.1, 2.2
        1: CH01
        2.1: CH02
        2.2: CH03

        Code is requiered for type 7
        7: CCP

</%doc>\
   <%
   line=sepa_context['line']
   invoice = line.move_line_id.invoice
   %>
   % if invoice.partner_bank_id.state == 'bvr':
          <PmtTpInf>
              <LclInstrm>
                <Prtry>CH01</Prtry>
              </LclInstrm>
          </PmtTpInf>
   % endif
</%block>

<%block name="RmtInf">
   <%
   line=sepa_context['line']
   invoice = line.move_line_id.invoice
   %>
   % if invoice.reference_type == 'bvr':
          <RmtInf>
            <Strd>
              <CdtrRefInf>
                <Ref>${invoice.reference}</Ref>
              </CdtrRefInf>
            </Strd>
          </RmtInf>
   % endif
</%block>

<%def name="acc_id(bank_acc)">
              <Id>
                % if bank_acc.state == 'iban':
                  <IBAN>${bank_acc.iban.replace(' ', '')}</IBAN>
                % else:
                  <Othr>
                    <Id>${bank_acc.get_account_number()}</Id>
                  </Othr>
                % endif
              </Id>
</%def>
