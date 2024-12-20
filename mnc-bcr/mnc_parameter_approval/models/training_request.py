from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import ast

import logging

_logger = logging.getLogger(__name__)


class MnceiTrainingRequesition(models.Model):
    _inherit = 'mncei.training.requesition'

    hrga_dept_params_ids = fields.Many2many(
        'mncei.department', 'hrga_dept_tr_rel', 'params_id', 'hrga_dept_id',
        string='HR Dept', compute='_get_params_approval', copy=False)
    accounting_dept_params_ids = fields.Many2many(
        'mncei.department', 'accounting_dept_tr_rel', 'params_id', 'acc_dept_id',
        string='Accounting', compute='_get_params_approval', copy=False)
    direksi_params_ids = fields.Many2many(
        'mncei.department', 'direksi_params_tr_rel', 'params_id', 'direksi_id',
        string='Direksi', compute='_get_params_approval', copy=False
    )

    @api.depends('requestor_id')
    def _get_params_approval(self):
        for training in self:
            params_obj = self.env['ir.config_parameter']
            training.hrga_dept_params_ids = False
            training.direksi_params_ids = False
            # Set Value
            hrga_dept_params_ids = ast.literal_eval(params_obj.sudo().get_param('hrga_dept_id') or '[]')
            acc_dept_params_ids = ast.literal_eval(params_obj.sudo().get_param('accounting_dept_id') or '[]')
            direksi_params_ids = ast.literal_eval(params_obj.sudo().get_param('bod_dept_id') or '[]')
            #
            training.direksi_params_ids = [(6, 0, direksi_params_ids)]
            training.hrga_dept_params_ids = [(6, 0, hrga_dept_params_ids)]
            training.accounting_dept_params_ids = [(6, 0, acc_dept_params_ids)]
