# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
# from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _get_employee(self):
        user = self.env.user
        employee_id = user.mncei_employee_id if user.mncei_employee_id else False
        if employee_id:
            return employee_id.id
        else:
            return False

    employee_id = fields.Many2one('hr.employee', string="Not Used", required=False)
    mncei_employee_id = fields.Many2one('mncei.employee', string="Employee", default=_get_employee, required=True, index=True, store=True)
    department_id = fields.Many2one('hr.department', "Not Used Dept", compute=False, store=True)
    mncei_department_id = fields.Many2one('mncei.department', "Department", compute='_compute_mncei_department_id', store=True)

    @api.depends('mncei_employee_id')
    def _compute_user_id(self):
        for line in self:
            user_id = self.env['res.users'].search([('mncei_employee_id', '=', line.mncei_employee_id.id)], limit=1)
            line.user_id = user_id if user_id else line._default_user()

    @api.depends('mncei_employee_id')
    def _compute_mncei_department_id(self):
        for line in self:
            line.mncei_department_id = line.mncei_employee_id.department
