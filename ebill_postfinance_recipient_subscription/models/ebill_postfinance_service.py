# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
import datetime
import io
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class EbillPostfinanceService(models.Model):
    _inherit = "ebill.postfinance.service"

    def get_ebill_recipient_subscription_status_bulk(self, bill_recipient_id):
        service = self._get_service()
        res = service.get_ebill_recipient_subscription_status_bulk(bill_recipient_id)
        return res

    def initiate_ebill_recipient_subscription(self, recipient_email):
        service = self._get_service()
        res = service.initiate_ebill_recipient_subscription(recipient_email)
        return res

    def confirm_ebill_recipient_subscription(self, initiation_token, activation_code):
        service = self._get_service()
        res = service.confirm_ebill_recipient_subscription(
            initiation_token, activation_code
        )
        return res

    def _get_ebill_transmit_method(self):
        return (
            self.env["transmit.method"]
            .sudo()
            .search([("code", "=", "postfinance")], limit=1)
        )

    def _ensure_partner_and_contract(self, ebill_recipient_info):
        partner_id = ebill_recipient_info.get("partner_id") or None
        email = (ebill_recipient_info.get("email") or "").strip() or None
        ebill_account_id = (
            ebill_recipient_info.get("ebill_account_id") or ""
        ).strip() or None
        name = ebill_recipient_info.get("name")
        street = (ebill_recipient_info.get("street") or "").strip() or None
        zip_code = (ebill_recipient_info.get("zip") or "").strip() or None
        city = (ebill_recipient_info.get("city") or "").strip() or None

        if not (partner_id or email) or not ebill_account_id:
            raise ValueError("partner_id or email and ebill_account_id is required")

        if partner_id:
            domain = [("id", "=", partner_id)]
        else:
            domain = [("email", "=", email)]

        partner = self.env["res.partner"].sudo().search(domain, limit=1)
        if not partner:
            vals = {"name": name, "email": email}
            if street:
                vals["street"] = street
            if zip_code:
                vals["zip"] = zip_code
            if city:
                vals["city"] = city
            partner = self.env["res.partner"].sudo().create(vals)

        transmit_method = self._get_ebill_transmit_method()
        contract = partner.sudo().get_active_contract(transmit_method)

        if not contract:
            contract = (
                self.env["ebill.payment.contract"]
                .sudo()
                .create(
                    {
                        "partner_id": partner.id,
                        "transmit_method_id": transmit_method.id,
                        "state": "open",
                        "postfinance_service_id": self.id,
                        "postfinance_billerid": ebill_account_id,
                    }
                )
            )

        return partner, contract

    def _cancel_contract_by_recipient(self, recipient_id):
        Contract = self.env["ebill.payment.contract"].sudo()

        contracts_to_close = Contract.search(
            [
                ("postfinance_billerid", "=", recipient_id),
                ("postfinance_service_id", "=", self.id),
                ("state", "=", "open"),
            ]
        )

        if not contracts_to_close:
            _logger.warning(
                "eBill deregistration: No active contract found for RecipientID %s. "
                "No action taken.",
                recipient_id,
            )
            return

        for contract in contracts_to_close:
            contract.write({"state": "cancel", "date_end": datetime.date.today()})
            _logger.info(
                "Closed eBill contract ID %s for partner %s (RecipientID: %s).",
                contract.id,
                contract.partner_id.name,
                recipient_id,
            )

    @api.model
    def _cron_process_registration_protocols(self):
        _logger.info("Starting eBill registration protocol cron job...")

        try:
            ebill_service = self._get_ebill_service_instance()
            registrations_lists = ebill_service.get_registration_protocol_list(True)

            if not registrations_lists:
                _logger.info("Nothing could be find to be imported")
                return

            unique_registrations = []
            seen_keys = set()

            for reg_item in registrations_lists:
                key = (reg_item.CreateDate, reg_item.FileType)
                if key not in seen_keys:
                    unique_registrations.append(reg_item)
                    seen_keys.add(key)

            for registration in unique_registrations:
                try:
                    files = ebill_service.get_registration_protocol(
                        registration.CreateDate, True
                    )
                    for file in files:
                        data_bytes = file.Data
                        decoded_data = data_bytes.decode("utf-8")
                        data_file = io.StringIO(decoded_data)
                        csv_reader = csv.DictReader(data_file, delimiter=";")

                        for line in csv_reader:
                            subscription_type = line.get("SUBSCRIPTIONTYPE", "").strip()
                            email = line.get("EMAIL", "").strip()
                            recipient_id = line.get("RECIPIENTID", "").strip()

                            if not recipient_id:
                                _logger.warning(
                                    "Skipping line in %s: No RECIPIENTID found. "
                                    "Line: %s",
                                    file.Filename,
                                    line,
                                )
                                continue

                            if subscription_type in ("1", "2"):
                                ebill_recipient_info = {
                                    "email": email,
                                    "ebill_account_id": recipient_id,
                                    "name": " ".join(
                                        filter(
                                            None,
                                            [
                                                line.get("GIVENNAME", "").strip(),
                                                line.get("FAMILYNAME", "").strip(),
                                            ],
                                        )
                                    ),
                                    "street": line.get("ADDRESS", "").strip(),
                                    "zip": line.get("ZIP", "").strip(),
                                    "city": line.get("CITY", "").strip(),
                                }

                                if not email:
                                    _logger.warning(
                                        "Skipping subscription for RecipientID "
                                        "%s: No EMAIL found.",
                                        recipient_id,
                                    )
                                    continue

                                (
                                    partner,
                                    contract,
                                ) = ebill_service._ensure_partner_and_contract(
                                    ebill_recipient_info
                                )

                                _logger.info(
                                    "Cron: Ensured contract (ID: %s) for "
                                    "partner %s (ID: %s) with EbillAccountID %s.",
                                    contract.id,
                                    partner.email,
                                    partner.id,
                                    contract.postfinance_billerid,
                                )

                            elif subscription_type == "3":
                                ebill_service._cancel_contract_by_recipient(
                                    recipient_id
                                )
                                _logger.info(
                                    "Processing end of contract for "
                                    "RecipientID %s (Type: %s)",
                                    recipient_id,
                                    subscription_type,
                                )

                except Exception as e:
                    _logger.error(
                        "eBill registration cron: "
                        "Failed to get protocol file for date %s: %s",
                        registration.CreateDate,
                        e,
                        exc_info=True,
                    )
                continue
        except Exception as e:
            _logger.error(
                "CRITICAL eBill registration cron failed completely: %s",
                e,
                exc_info=True,
            )

        _logger.info("Finished eBill registration protocol cron job.")

    @api.model
    def _get_ebill_service_instance(self):
        biller_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ebill_postfinance.biller_id")
        )
        return (
            self.env["ebill.postfinance.service"]
            .sudo()
            .search([("biller_id", "=", biller_id)], limit=1)
        )
