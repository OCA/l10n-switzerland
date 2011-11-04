<%inherit file="pain.001.001.03.xml.mako"/>

<%block name="root">
<Document xmlns="http://www.six-interbank-clearing.com/de/pain.001.001.03.ch.02.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.six-interbank-clearing.com/de/pain.001.001.03.ch.02.xsd pain.001.001.03.ch.02.xsd">
</%block>

<%block name="InitgPty">
        <InitgPty>
          <Nm>${order.user_id.company_id.name}</Nm>
        </InitgPty>
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