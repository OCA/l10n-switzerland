# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io
import logging
import re
import threading
from email.utils import parseaddr

from PIL import Image
from quickpac import (
    ApiClient,
    BarcodeApi,
    Communication,
    Configuration,
    Dimensions,
    GenerateLabelCustomer,
    GenerateLabelDefinition,
    GenerateLabelEnvelope,
    GenerateLabelFileInfos,
    GenerateLabelResponse,
    Item,
    LabelData,
    LabelDataProvider,
    LabelDataProviderSending,
    Notification,
    Recipient,
    ServiceCodeAttributes,
    ZIPAllResponse,
    ZIPApi,
    ZIPIsCurrentResponse,
)

from odoo import _
from odoo.exceptions import UserError

from .helpers import (
    get_image_resolution,
    get_label_layout,
    get_language,
    get_logo,
    get_output_format,
    sanitize_string,
)

_logger = logging.getLogger("Quickpac API")

_compile_itemid = re.compile(r"[^0-9A-Za-z+\-_]")
_compile_itemnum = re.compile(r"[^0-9]")


def _get_errors_from_response(response):
    """Manage to get potential errors from a Response

    :param response: GenerateLabelResponse,ZIPAllResponse,ZIPIsCurrentResponse
    :return: list of string (formatted messages prefixing the type or empty)
    """
    if not response:
        return
    errors = []
    messages = []

    if isinstance(response, GenerateLabelResponse):
        items = response.envelope.data.provider.sending.item
        for item in items:
            if item.errors:
                errors.extend(item.errors)
    if isinstance(response, (ZIPAllResponse, ZIPIsCurrentResponse)):
        if response.errors:
            errors.extend(response.errors)

    for error in errors:
        message = error.code + " - " + error.message
        messages.append(message)

    return messages


def _get_warnings_from_response(response):
    """Manage to get potential warnings from a Response

    :param response: GenerateLabelResponse,ZIPAllResponse,ZIPIsCurrentResponse
    :return: list of string (formatted messages prefixing the type or empty)
    """
    if not response:
        return
    warnings = []
    messages = []

    if isinstance(response, GenerateLabelResponse):
        items = response.envelope.data.provider.sending.item
        for item in items:
            if item.warnings:
                warnings.extend(item.warnings)
    if isinstance(response, (ZIPAllResponse, ZIPIsCurrentResponse)):
        if response.warnings:
            warnings.extend(response.warnings)

    for warning in warnings:
        message = warning.code + " - " + warning.message
        messages.append(message)

    return messages


def process_response(response):
    """Process the response to find anything to be processed before rendering
    Such as errors, specific codes, etc.

    :param response: GenerateLabelResponse,ZIPAllResponse,ZIPIsCurrentResponse
    :raise: UserError
    """
    if not response:
        return
    errors = _get_errors_from_response(response)
    if errors:
        for error in errors:
            _logger.error(error)
        raise UserError(",\t".join(errors))
    warnings = _get_warnings_from_response(response)
    if warnings:
        for warning in warnings:
            _logger.warning(warning)
        raise UserError(",\t".join(warnings))


class QuickpacWebService(object):
    """Connector with Quickpac for labels using their API

    Specification available here:
    https://api.quickpac.ch/swagger/index.html

    Allows to interact with the OpenAPI generated implementation
    """

    access_token = False
    access_token_expiry = False
    _lock = threading.Lock()

    def __init__(self, company):
        self.company = company
        assert self.company.quickpac_username
        assert self.company.quickpac_password
        configuration = Configuration()
        configuration.username = self.company.quickpac_username
        configuration.password = self.company.quickpac_password
        api_client = ApiClient(configuration)
        self.zip_api = ZIPApi(api_client)
        self.barcode_api = BarcodeApi(api_client)

    def _get_recipient_partner(self, picking):
        if picking.picking_type_id.code == "outgoing":
            return picking.partner_id
        elif picking.picking_type_id.code == "incoming":
            location_dest = picking.location_dest_id
            return (
                location_dest.partner_id
                or location_dest.company_id.partner_id
                or picking.env.user.company_id.partner_id
            )

    def _generate_picking_itemid(self, picking, pack_no):
        """Allowed characters are alphanumeric plus `+`, `-` and `_`
        Last `+` separates picking name and package number (if any)

        :param picking: a picking record
        :param pack_num: the current packing number
        :return string: itemid
        """
        name = _compile_itemid.sub("", picking.name)
        if pack_no:
            pack_no = _compile_itemid.sub("", pack_no)
        codes = [name, pack_no]
        return "+".join(c for c in codes if c)

    def _generate_tracking_number(self, picking, pack_num):
        """Generate the tracking reference for the last 8 digits
        of tracking number of the label.

        2 first digits for a pack counter
        6 last digits for the picking name

        e.g. 03000042 for 3rd pack of picking OUT/19000042

        :param picking: a picking record
        :param pack_num: the current packing number
        :return string: the tracking number
        """
        picking_num = _compile_itemnum.sub("", picking.name)
        return "%02d%s" % (pack_num, picking_num[-6:].zfill(6))

    def _prepare_label_definition(self, picking):
        """Define how the label will look like

        :param picking: a picking record
        :return: GenerateLabelDefinition
        """
        label_layout = get_label_layout(picking)
        output_format = get_output_format(picking)
        image_resolution = get_image_resolution(picking)

        error_missing = _(
            "You need to configure %s. You can set a default"
            "value in Settings/Configuration/Carriers/Quickpac."
            " You can also set it on delivery method or on the picking."
        )
        if not label_layout:
            raise UserError(
                _("Layout not set") + "\n" + error_missing % _("label layout")
            )
        if not output_format:
            raise UserError(
                _("Output format not set") + "\n" + error_missing % _("output format")
            )
        if not image_resolution:
            raise UserError(
                _("Resolution not set") + "\n" + error_missing % _("resolution")
            )

        label_definition = GenerateLabelDefinition(
            print_addresses="RecipientAndCustomer",
            image_file_type=output_format,
            image_resolution=image_resolution,
            print_preview=False,
            label_layout=label_layout,
        )
        return label_definition

    def _prepare_customer(self, picking):
        """Define the Quickpac direct client

        :param picking: a picking record
        :param company: The company sending the goods
        :return: GenerateLabelCustomer
        """
        company = picking.company_id
        if picking.picking_type_id.code == "outgoing":
            partner = company.partner_id
        elif picking.picking_type_id.code == "incoming":
            partner = picking.partner_id

        customer = GenerateLabelCustomer(
            name1=partner.name,
            street=partner.street,
            zip=partner.zip,
            city=partner.city,
            country=partner.country_id.code,
        )
        if picking.picking_type_id.code == "outgoing" and company.quickpac_office:
            customer.po_box = company.quickpac_office

        if partner.parent_id and partner.parent_id.name != partner.name:
            customer.name2 = customer.name1
            customer.name1 = partner.parent_id.name

        logo = get_logo(picking)
        if logo:
            bytes_logo = base64.b64decode(logo.decode())
            logo_image = Image.open(io.BytesIO(bytes_logo))
            logo_format = logo_image.format
            customer.logo = logo.decode()
            customer.logo_format = logo_format

        return customer

    def _prepare_file_infos(self, picking, company):
        """Define the sender informations

        :param picking: a picking record
        :param company: The company sending the goods
        :return: GenerateLabelFileInfos
        """
        customer = self._prepare_customer(picking)
        file_infos = GenerateLabelFileInfos(
            mode="Label",
            franking_license=company.quickpac_franking_license,
            customer=customer,
        )
        return file_infos

    def _prepare_recipient(self, picking):
        """Create a Recipient for a partner from a picking

        :param picking: a picking record
        :return: Recipient
        """
        partner = self._get_recipient_partner(picking)
        partner_name = partner.name or partner.parent_id.name
        email = parseaddr(partner.email)[1]
        recipient = Recipient(
            name1=sanitize_string(partner.name),
            street=sanitize_string(partner.street),
            zip=partner.zip,
            city=partner.city,
            e_mail=email or None,
        )

        if partner.country_id.code:
            recipient.country = partner.country_id.code.upper()
        if partner.street2:
            recipient.address_suffix = sanitize_string(partner.street2)

        parent_id = partner.parent_id
        if parent_id and parent_id.name != partner_name:
            recipient.name2 = sanitize_string(parent_id.name)
            recipient.personally_addressed = False

        # Phone and / or mobile should only be displayed if instruction to
        # Notify delivery by telephone is set
        is_phone_required = [
            option for option in picking.option_ids if option.code == "ZAW3213"
        ]
        if is_phone_required:
            phone = partner.phone or parent_id and parent_id.phone
            if phone:
                recipient.phone = phone

            mobile = partner.mobile or parent_id and parent_id.mobile
            if mobile:
                recipient.mobile = mobile

        return recipient

    def _prepare_attributes(self, picking, pack_counter=None, pack_total=None):
        """Define specific attributes for a delivery

        :param picking: a picking record
        :param pack_counter: the current package index
        :param pack_total: the total packages number
        :return: ServiceCodeAttributes
        """
        services = [
            code
            for codes in (
                option.code.split(",")
                for option in picking.option_ids
                if option.tmpl_option_id.quickpac_type
                in ("basic", "additional", "delivery")
            )
            for code in codes
        ]
        if not services:
            raise UserError(_("Missing required delivery option on picking."))

        dimensions = Dimensions(weight=picking.shipping_weight)
        attributes = ServiceCodeAttributes(przl=services, dimensions=dimensions)
        return attributes

    def _prepare_notification(self, picking):
        """Define how and who will be notified

        :param picking: a picking record
        :return: Notification
        """
        communication = Communication(
            email=picking.partner_id.email or None,
            mobile=(picking.partner_id.mobile or picking.partner_id.phone or None),
        )
        notification = Notification(
            communication=communication,
            service="441",
            language=get_language(picking.partner_id.lang),
            type=1 if communication.mobile else 0,
        )
        return notification

    def _prepare_items(self, picking, packages=None):
        """Return a list of item made from the picking/packages

        :param picking: a picking record
        :param packages: a packages record
        :return: a list of Item
        """
        company = picking.company_id
        items = []
        pack_counter = 1

        def add_item(package=None, attributes=None):
            assert picking or package
            itemid = self._generate_picking_itemid(
                picking, package.name if package else picking.name
            )
            item_number = None
            if company.quickpac_tracking_format == "picking_num":
                if not package:
                    # start with 9 to garentee uniqueness and use 7 digits
                    # of picking number
                    picking_num = _compile_itemnum.sub("", picking.name)
                    item_number = "9%s" % picking_num[-7:].zfill(7)
                else:
                    item_number = self._generate_tracking_number(picking, pack_counter)

            recipient = self._prepare_recipient(picking)
            attributes = attributes or self._prepare_attributes(picking)
            notifications = self._prepare_notification(picking)
            item = Item(
                item_id=itemid,
                ident_code=item_number,
                recipient=recipient,
                attributes=attributes,
                notification=[notifications],
            )
            items.append(item)

        if not packages:
            add_item()

        pack_total = len(packages)
        for pack in packages:
            attributes = self._prepare_attributes(picking, pack_counter, pack_total)
            add_item(package=pack, attributes=attributes)
            pack_counter += 1

        return items

    def _prepare_data(self, picking, company, packages=None):
        """Define packages data inside this shipment

        :param picking: The picking to process
        :param company: The company sending the goods
        :param packages: a packages record
        :return: LabelData
        """
        items = self._prepare_items(picking, packages)
        sending = LabelDataProviderSending(item=items)
        provider = LabelDataProvider(sending=sending)
        data = LabelData(provider=provider)
        return data

    def _prepare_envelope(self, picking, company, packages=None):
        """Define the main object that contains everything

        :param picking: The picking to process
        :param company: The company sending the goods
        :param packages: a packages record
        :return: GenerateLabelEnvelope
        """
        file_infos = self._prepare_file_infos(picking, company)
        label_definition = self._prepare_label_definition(picking)
        data = self._prepare_data(picking, company, packages)
        envelope = GenerateLabelEnvelope(
            label_definition=label_definition, file_infos=file_infos, data=data
        )
        return envelope

    def get_valid_zipcodes(self):
        """Return all valid zipcodes managed by Quickpac

        :raise: UserError if any errors occurs
        """
        zipcode_all_response = None
        try:
            zipcode_all_response = self.zip_api.z_ip_get_all_zip_codes_get()
            zipcode_models = zipcode_all_response.zip_codes
            return [zip.zip_code for zip in zipcode_models]
        except Exception:
            return []
        finally:
            process_response(zipcode_all_response)

    def is_deliverable_zipcode(self, zipcode):
        """Check whether or not the deliverability of this zipcodes

        :param zipcode: zipcode to check
        :raise: UserError if any errors occurs
        """
        zipcode_response = None
        try:
            zipcode_response = self.zip_api.z_ip_is_deliverable_zip_code_get(
                zip_code=zipcode
            )
            return bool(zipcode_response.deliverable)
        except Exception:
            return False
        finally:
            process_response(zipcode_response)

    def generate_label(self, picking, packages):
        """Generate a label for a picking

        :param picking: picking browse record
        :param packages: list of browse records of packages to filter on
        :return: {
            value: [{item_id: pack id
                     binary: file returned by API
                     tracking_number: id number for tracking
                     file_type: str of file type
                     }
                    ]
            errors: list of error message if any
            warnings: list of warning message if any
        }

        """
        lang = get_language(self.company.partner_id.lang)
        envelope = self._prepare_envelope(picking, self.company, packages)
        body = {"Language": lang, "Envelope": envelope}
        response = self.barcode_api.barcode_generate_label_post(body=body)
        process_response(response)
        items = response.envelope.data.provider.sending.item
        label_definition = response.envelope.label_definition
        file_type = label_definition.image_file_type.lower()
        labels = []
        for item in items:
            binary = base64.b64encode(bytes(item.label, "utf-8"))
            res = {
                "success": True,
                "errors": [],
                "value": {
                    "item_id": item.item_id,
                    "binary": binary,
                    "tracking_number": item.ident_code,
                    "file_type": file_type,
                },
            }
            labels.append(res)
        return labels
