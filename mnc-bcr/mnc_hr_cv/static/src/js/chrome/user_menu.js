odoo.define('mnc_hr_cv.UserMenu', function (require) {
"use strict";

var UserMenu = require('web.UserMenu');
var session = require('web.session');

UserMenu.include({
    /**
     * @private
     */
    _onMenuEmployee: function () {
        var self = this;
        this.trigger_up('clear_uncommitted_changes', {
            callback: function () {
                self._rpc({
                    model: "mncei.employee",
                    method: "action_my_datas"
                })
                .then(function (result) {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'mncei.employee',
                        res_id: result,
                        views: [[false, 'form']],
                        target: 'new'
                    });
                });
            },
        });
    },
});

return UserMenu;

});
