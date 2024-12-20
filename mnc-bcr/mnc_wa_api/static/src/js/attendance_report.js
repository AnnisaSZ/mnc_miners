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
            Dialog.alert(self, _t("Please select data to export !"), {
                title: _t('Warning'),
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
        // let selectedDataIds = self.controlPanelProps.actionMenus.activeIds
        // console.log(selectedDataIds)
        // let dict = [];
        // // for (let i=0; i < all_datas.length; i++){
        // //     for (let x=0; x< self.selectedRecords.length; x++){
        // //         if (all_datas[i].id == selectedDataIds[x]) {
        // //             dict.push(all_datas[i].res_id)
        // //         }
        // //     }
        // // }
        // // console.log(all_datas)
        // // const C = this.initialState.data.filter(value => this.selectedRecords.includes(value));
        // // const C = all_datas.filter(item => selectedDataIds.includes(item.id)).map(item => item.id);
        // // console.log("==== Values ====")
        // // console.log(C)
        // // console.log(dict)
        // var def1 = rpc.query({
        //     model: 'hr.attendance',
        //     method: 'get_attachments_link',
        //     args: [[false], selectedDataIds]
        // }).then(function (result) {
        //     self.do_action({
        //         type: 'ir.actions.act_url',
        //         url: result
        //     })
        // });

        // session.get_file({
        //     url: '/mnc_attendance/download',
        //     data: {data: JSON.stringify(dict),},
        //     error: (error) => this.call('crash_manager', 'rpc_error', error),
        // });
    }
});

var TransactionsListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: GenerateAttendance,
    }),
});

viewRegistry.add('attendance_views_tree', TransactionsListView);
});
