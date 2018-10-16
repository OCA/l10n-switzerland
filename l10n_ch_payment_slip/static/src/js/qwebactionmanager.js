odoo.define('l10n_ch_payment_slip.report', function(require){
'use strict';

var ActionManager= require('web.ActionManager');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');


ActionManager.include({
    ir_actions_report: function (action, options){
        var report_url = '';

        if (action.report_type !== 'reportlab-pdf') {
            return this._super(action, options);
        }
        framework.blockUI();
        report_url = '/report/reportlab-pdf/'.concat(
            action.report_name,'/',
            action.context.active_ids.join(',')
        );
        this.getSession().get_file({
                url: report_url,
                data: {data: JSON.stringify([report_url,
                                             action.report_type,
            ])},
            error: crash_manager.rpc_error.bind(crash_manager),
            success: function() {
                if(action && options && !action.dialog){
                    options.on_close();
                }
            },
        });
        framework.unblockUI();
        return;
    }
});
});
