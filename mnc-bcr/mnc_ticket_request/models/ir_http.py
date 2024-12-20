# -*- coding: utf-8 -*-
# Part of CLuedoo. See LICENSE file for full copyright and licensing details.
from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        user = request.env.user
        result = super(IrHttp, self).session_info()
        result.update({
            'department_id': user.mncei_dept_id.id or False
        })
        result.get('user_context').update({
            'department_id': user.mncei_dept_id.id or False
        })
        return result
