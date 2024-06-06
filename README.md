
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/l10n-switzerland&target_branch=14.0)
[![Pre-commit Status](https://github.com/OCA/l10n-switzerland/actions/workflows/pre-commit.yml/badge.svg?branch=14.0)](https://github.com/OCA/l10n-switzerland/actions/workflows/pre-commit.yml?query=branch%3A14.0)
[![Build Status](https://github.com/OCA/l10n-switzerland/actions/workflows/test.yml/badge.svg?branch=14.0)](https://github.com/OCA/l10n-switzerland/actions/workflows/test.yml?query=branch%3A14.0)
[![codecov](https://codecov.io/gh/OCA/l10n-switzerland/branch/14.0/graph/badge.svg)](https://codecov.io/gh/OCA/l10n-switzerland)
[![Translation Status](https://translation.odoo-community.org/widgets/l10n-switzerland-14-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/l10n-switzerland-14-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Swiss Localization

Swiss Localization Modules

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[ebill_paynet](ebill_paynet/) | 14.0.1.1.4 | [![TDu](https://github.com/TDu.png?size=30px)](https://github.com/TDu) | Paynet platform bridge implementation
[ebill_paynet_customer_free_ref](ebill_paynet_customer_free_ref/) | 14.0.1.0.2 |  | Glue module: ebill_paynet and sale_order_customer_free_ref
[ebill_postfinance](ebill_postfinance/) | 14.0.1.1.0 | [![TDu](https://github.com/TDu.png?size=30px)](https://github.com/TDu) | Postfinance eBill integration
[ebill_postfinance_server_env](ebill_postfinance_server_env/) | 14.0.1.0.0 |  | Server environment for eBill Postfinance
[ebill_postfinance_stock](ebill_postfinance_stock/) | 14.0.1.0.0 | [![TDu](https://github.com/TDu.png?size=30px)](https://github.com/TDu) | Add stock integration to Postfinance eBill
[l10n_ch_account_tags](l10n_ch_account_tags/) | 14.0.1.0.0 |  | Switzerland Account Tags
[l10n_ch_adr_report](l10n_ch_adr_report/) | 14.0.1.0.0 |  | Print Delivery report to ADR swiss configuration
[l10n_ch_base_bank](l10n_ch_base_bank/) | 14.0.1.0.3 |  | Types and number validation for swiss electronic pmnt. DTA, ESR
[l10n_ch_delivery_carrier_label_quickpac](l10n_ch_delivery_carrier_label_quickpac/) | 14.0.1.0.1 |  | Print quickpac shipping labels
[l10n_ch_invoice_reports](l10n_ch_invoice_reports/) | 14.0.1.3.0 |  | Extend invoice to add ISR/QR payment slip
[l10n_ch_isr_payment_grouping](l10n_ch_isr_payment_grouping/) | 14.0.1.0.1 |  | Extend account to ungroup ISR
[l10n_ch_isrb](l10n_ch_isrb/) | 14.0.1.0.0 |  | Switzerland - ISR with Bank
[l10n_ch_mis_reports](l10n_ch_mis_reports/) | 14.0.1.0.0 |  | Specific MIS reports for switzerland localization
[l10n_ch_pain_base](l10n_ch_pain_base/) | 14.0.1.0.0 |  | ISO 20022 base module for Switzerland
[l10n_ch_pain_credit_transfer](l10n_ch_pain_credit_transfer/) | 14.0.1.0.0 | [![ecino](https://github.com/ecino.png?size=30px)](https://github.com/ecino) | Generate ISO 20022 credit transfert (SEPA and not SEPA)
[l10n_ch_states](l10n_ch_states/) | 14.0.1.0.0 |  | Switzerland Country States
[server_env_ebill_paynet](server_env_ebill_paynet/) | 14.0.1.0.0 |  | Server environment for Ebill Paynet

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
