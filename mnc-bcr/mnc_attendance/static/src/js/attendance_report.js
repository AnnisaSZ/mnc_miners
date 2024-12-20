odoo.define('mnc_attendance.transaction', function (require) {
    "use strict";

var ListController = require('web.ListController');
var ListView = require('web.ListView');
var viewRegistry = require('web.view_registry');
// var session = require('web.session');
var rpc = require("web.rpc");
var Dialog = require('web.Dialog');
var core = require('web.core');

var _t = core._t;

var GenerateAttendance = ListController.extend({
    buttons_template: 'AttendanceListView.buttons',
    events: _.extend({}, ListController.prototype.events, {
        'click .o_generate_attendance_xls': '_onTransactionsSync',
    }),

    _onTransactionsSync: function () {
        var self = this;
        let all_datas = self.initialState.data
        // Check if record selected or not
        if (self.controlPanelProps.actionMenus == null) {
            // Dialog.alert(self, _t("Please select data to export !"), {
            //     title: _t('Warning'),
            // });
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'attendance.report.wizard',
                views: [[false, 'form']],
                target: 'new'
            });
        } else {
            // Get record selected
            let selectedDataIds = self.controlPanelProps.actionMenus.activeIds

            // Create Excel function in python
            var def1 = rpc.query({
                model: 'hr.attendance',
                method: 'get_attachments_link',
                args: [[false], selectedDataIds]
            }).then(function (result) {
                // Download file
                self.do_action({
                    type: 'ir.actions.act_url',
                    url: result
                })
            });
        }
    }
});

var TransactionsListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: GenerateAttendance,
    }),
});

viewRegistry.add('attendance_views_tree', TransactionsListView);
});
