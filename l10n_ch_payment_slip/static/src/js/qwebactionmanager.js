odoo.define('l10n_ch_payment_slip.report', function (require) {
    'use strict';

    var ActionManager= require('web.ActionManager');
    var crash_manager = require('web.crash_manager');
    var framework = require('web.framework');
    var session = require('web.session');

    ActionManager.include({
        _executeReportAction: function (action, options) {
            if (action.report_type !== 'reportlab-pdf') {
                return this._super(action, options);
            }
            framework.blockUI();
            var def = $.Deferred();
            var report_url  = '/report/reportlab-pdf/'.concat(
                action.report_name, '/',
                action.context.active_ids.join(',')
            );
            var blocked = !session.get_file({
                url: report_url,
                data:{
                    data: JSON.stringify([report_url, action.report_type]),
                },
                error: crash_manager.rpc_error.bind(crash_manager),
                success: def.resolve.bind(def),
                complete: framework.unblockUI,
            });
            if (blocked) {
                // AAB: this check should be done in get_file service directly,
                // should not be the concern of the caller (and that way, get_file
                // could return a deferred)
                var message = _t('A popup window with your report was blocked. You ' +
                                 'may need to change your browser settings to allow ' +
                                 'popup windows for this page.');
                this.do_warn(_t('Warning'), message, true);
            }
            return def;
        },
    });
});
