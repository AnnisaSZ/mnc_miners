from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError
import ast


class MnceiPurchaseRequest(models.Model):
    _inherit = 'mncei.purchase.requisition'

    head_dept_params_ids = fields.Many2many(
        'mncei.jabatan', 'head_dept_params_rel', 'params_id', 'head_dept_id',
        string='Jabatan Head Department', compute='_get_params_approval', copy=False
    )
    # Department
    direksi_params_ids = fields.Many2many(
        'mncei.department', 'direksi_params_rel', 'params_id', 'direksi_id',
        string='Jabatan Direksi', compute='_get_params_approval', copy=False
    )
    hrga_dept_params_ids = fields.Many2many(
        'mncei.department', 'hrga_dept_pr_rel', 'params_id', 'hrga_dept_id',
        string='HR Dept', compute='_get_params_approval', copy=False)
    ga_dept_params_ids = fields.Many2many(
        'mncei.department', 'ga_dept_pr_rel', 'params_id', 'ga_dept_id',
        string='GA Department', compute='_get_params_approval', copy=False)
    it_dept_params_ids = fields.Many2many(
        'mncei.department', 'it_dept_pr_rel', 'params_id', 'it_dept_id',
        string='IT Department', compute='_get_params_approval', copy=False)
    finance_dept_params_ids = fields.Many2many(
        'mncei.department', 'finance_dept_pr_rel', 'params_id', 'finance_dept_id',
        string='Finance Department', compute='_get_params_approval', copy=False)
    procurement_dept_params_ids = fields.Many2many(
        'mncei.department', 'procurement_dept_pr_rel', 'params_id', 'procurement_dept_id',
        string='Finance Department', compute='_get_params_approval', copy=False)

    @api.depends('order_by_id', 'department_id')
    def _get_params_approval(self):
        for pr in self:
            params_obj = self.env['ir.config_parameter']
            pr.head_dept_params_ids = False
            pr.direksi_params_ids = False
            pr.hrga_dept_params_ids = False
            pr.ga_dept_params_ids = False
            pr.it_dept_params_ids = False
            pr.finance_dept_params_ids = False
            pr.procurement_dept_params_ids = False
            # Set Value
            head_dept_params = ast.literal_eval(params_obj.sudo().get_param('head_dept_id') or '[]')
            direksi_params_ids = ast.literal_eval(params_obj.sudo().get_param('bod_dept_id') or '[]')
            hrga_dept_params_ids = ast.literal_eval(params_obj.sudo().get_param('hrga_dept_id') or '[]')
            ga_dept_params_ids = ast.literal_eval(params_obj.sudo().get_param('ga_dept_id') or '[]')
            it_dept_params_ids = ast.literal_eval(params_obj.sudo().get_param('it_dept_id') or '[]')
            finance_dept_params_ids = ast.literal_eval(params_obj.sudo().get_param('finance_dept_id') or '[]')
            procurement_dept_params_ids = ast.literal_eval(params_obj.sudo().get_param('procurement_dept_id') or '[]')
            # if head_dept_params:
            pr.head_dept_params_ids = [(6, 0, head_dept_params)]
            pr.direksi_params_ids = [(6, 0, direksi_params_ids)]
            pr.hrga_dept_params_ids = [(6, 0, hrga_dept_params_ids)]
            pr.ga_dept_params_ids = [(6, 0, ga_dept_params_ids)]
            pr.it_dept_params_ids = [(6, 0, it_dept_params_ids)]
            pr.finance_dept_params_ids = [(6, 0, finance_dept_params_ids)]
            pr.procurement_dept_params_ids = [(6, 0, procurement_dept_params_ids)]
