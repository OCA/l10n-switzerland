This roadmap summarizes follow-up actions discussed in
`OCA/l10n-switzerland#754 <https://github.com/OCA/l10n-switzerland/pull/754>`_.

Short-term (merge-safe, keep architecture stable)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Keep ``l10n_ch_pain_base`` close to legacy architecture for 16.0 migration.
- Avoid moving PAIN flavor declarations from feature modules into base only to satisfy tests.
- Keep base tests minimal and focused on base behavior; validate flavor-specific behavior in
  dedicated modules.
- Ensure CI is stable (including copier/CI profile alignment if conflicting modules require
  dedicated handling).

Mid-term refactor
~~~~~~~~~~~~~~~~~

- Review conditional logic in shared block generators that branches on ``pain_flavor`` and decide
  what should remain in base vs. move to extension modules.
- Revisit module split and responsibilities:

  - ``l10n_ch_pain_base``: common/shared generation logic.
  - ``l10n_ch_pain_credit_transfer``: credit-transfer specific behavior.
  - ``l10n_ch_pain_direct_debit``: confirm if still needed in current architecture.

- Reduce duplicated Swiss-specific logic where practical while preserving backward compatibility.

Swiss standard update (time-bound)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Prepare support for Swiss credit transfer ``pain.001.001.09.ch.03``.
- Plan deprecation path for ``pain.001.001.03.ch.02`` (announced acceptance window ends around
  Nov 2026).
- Validate generated XML with official SIX validators and real bank acceptance tests.
- Address format differences required by new standards, especially postal address handling and
  structured remittance/QRR compatibility.

Implementation checklist
~~~~~~~~~~~~~~~~~~~~~~~~

- [x] Keep migration PR scope limited and merge 16.0 base migration.
- [ ] Open a dedicated refactor PR for shared vs module-specific PAIN logic.
- [ ] Open a dedicated standards PR for ``pain.001.001.09.ch.03`` support.
- [ ] Track rollout status in this roadmap and link follow-up PRs/issues.
