/* Copyright 2014-2017 Compassion CH
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). */
odoo.define('l10n_ch_bank_statement_import_postfinance.reconciliation', function (require) {
    "use strict";

    var core = require('web.core');
    var qweb = core.qweb;
    var reconciliation = require('account.ReconciliationRenderer');

    // Extend the class written in module account (bank statement view)
    reconciliation.LineRenderer.include({
        start: function(){
            $('<span class="line_info_button fa fa-picture-o"/>')
                .appendTo(this.$('thead .cell_info_popover'))
                .attr("data-content", qweb.render('bank_statement_reconciliation_line_image', {'state': this._initialState}));
            return this._super();
        },
    });
});
