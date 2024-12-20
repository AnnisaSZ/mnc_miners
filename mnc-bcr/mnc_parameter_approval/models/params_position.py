# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import ast


class PerdinSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    # Position
    spv_id = fields.Many2many('mncei.jabatan', 'spv_params_rel', 'spv_id', 'setting_id', 'Supervisor', store=True)
    head_dept_id = fields.Many2many('mncei.jabatan', 'head_dept_params_rel', 'head_dept_id', 'setting_id', 'Jabatan Head Department', store=True)
    # direksi_id = fields.Many2many('mncei.jabatan', 'direksi_params_rel', 'direksi_id', 'setting_id', 'Jabatan Direksi', store=True)
    # Department
    hrga_dept_id = fields.Many2many('mncei.department', 'hrga_dept_params_rel', 'hrga_dept_id', 'setting_id', 'HR Dept', store=True)
    accounting_dept_id = fields.Many2many('mncei.department', 'acc_dept_params_rel', 'acc_dept_id', 'setting_id', 'Accounting Dept', store=True)
    finance_dept_id = fields.Many2many('mncei.department', 'finance_dept_params_rel', 'finance_dept_id', 'setting_id', 'Finance Department', store=True)
    direksi_dept_id = fields.Many2many('mncei.department', 'direksi_dept_params_rel', 'direksi_dept_id', 'setting_id', 'Direksi Department', store=True)
    ga_dept_id = fields.Many2many('mncei.department', 'ga_dept_params_rel', 'ga_dept_id', 'setting_id', 'GA Department', store=True)
    procurement_dept_id = fields.Many2many('mncei.department', 'procurement_dept_params_rel', 'procurement_dept_id', 'setting_id', 'Procurement', store=True)
    it_dept_id = fields.Many2many('mncei.department', 'it_dept_params_rel', 'it_dept_id', 'setting_id', 'IT', store=True)
    bod_dept_id = fields.Many2many('mncei.department', 'bod_dept_params_rel', 'bod_dept_id', 'setting_id', 'BOD', store=True)
    secretary_dept_id = fields.Many2many('mncei.department', 'secretary_dept_params_rel', 'secretary_dept_id', 'setting_id', 'Secretary', store=True)

    @api.model
    def get_values(self):
        res = super(PerdinSetting, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        spv_data = ast.literal_eval(params.get_param('spv_id') or '[]')
        head_dept_data = ast.literal_eval(params.get_param('head_dept_id') or '[]')
        # direksi_id = ast.literal_eval(params.get_param('direksi_id') or '[]')
        res.update(spv_id=[(6, 0, spv_data)])
        res.update(head_dept_id=[(6, 0, head_dept_data)])
        # res.update(direksi_id=[(6, 0, direksi_id)])
        # department
        hrga_data = ast.literal_eval(params.get_param('hrga_dept_id') or '[]')
        accounting_data = ast.literal_eval(params.get_param('accounting_dept_id') or '[]')
        ga_data = ast.literal_eval(params.get_param('ga_dept_id') or '[]')
        finance_data = ast.literal_eval(params.get_param('finance_dept_id') or '[]')
        direksi_data = ast.literal_eval(params.get_param('direksi_dept_id') or '[]')
        procurement_data = ast.literal_eval(params.get_param('procurement_dept_id') or '[]')
        it_data = ast.literal_eval(params.get_param('it_dept_id') or '[]')
        bod_data = ast.literal_eval(params.get_param('bod_dept_id') or '[]')
        secretary_data = ast.literal_eval(params.get_param('secretary_dept_id') or '[]')
        res.update(hrga_dept_id=[(6, 0, hrga_data)])
        res.update(accounting_dept_id=[(6, 0, accounting_data)])
        res.update(ga_dept_id=[(6, 0, ga_data)])
        res.update(finance_dept_id=[(6, 0, finance_data)])
        res.update(direksi_dept_id=[(6, 0, direksi_data)])
        res.update(procurement_dept_id=[(6, 0, procurement_data)])
        res.update(it_dept_id=[(6, 0, it_data)])
        res.update(bod_dept_id=[(6, 0, bod_data)])
        res.update(secretary_dept_id=[(6, 0, secretary_data)])
        return res

    def set_values(self):
        super(PerdinSetting, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('spv_id', self.spv_id.ids)
        params.set_param('head_dept_id', str(self.head_dept_id.ids))
        # Department
        params.set_param('hrga_dept_id', str(self.hrga_dept_id.ids))
        params.set_param('accounting_dept_id', str(self.accounting_dept_id.ids))
        params.set_param('ga_dept_id', str(self.ga_dept_id.ids))
        params.set_param('finance_dept_id', str(self.finance_dept_id.ids))
        params.set_param('direksi_dept_id', str(self.direksi_dept_id.ids))
        params.set_param('procurement_dept_id', str(self.procurement_dept_id.ids))
        params.set_param('it_dept_id', str(self.it_dept_id.ids))
        params.set_param('bod_dept_id', str(self.bod_dept_id.ids))
        params.set_param('secretary_dept_id', str(self.secretary_dept_id.ids))
