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
    res_config_approval_id = fields.Many2one('res.config.approval', string="Config Approval", compute='_get_config_approval')

    @api.depends('company_id')
    def _get_config_approval(self):
        for training in self:
            training.res_config_approval_id = False
            if training.company_id:
                config_id = self.env['res.config.approval'].search([('company_id', '=', training.company_id.id), ('model_type', '=', 'training')], limit=1)
                valid_warning = _("Please input configuration approval in %s") % (training.company_id.name)
                if not config_id and training.state == 'draft':
                    raise ValidationError(_(valid_warning))
                elif config_id:
                    training.res_config_approval_id = config_id.id

    @api.onchange('res_config_approval_id')
    def set_approval(self):
        if self.res_config_approval_id:
            self.spv_hr_id = self.res_config_approval_id.hr_id
            self.head_hrga_id = self.res_config_approval_id.head_hrga_id
            self.accounting_dept_id = self.res_config_approval_id.accounting_id
            self.direksi1_id = self.res_config_approval_id.direksi1_id
            self.direksi2_id = self.res_config_approval_id.direksi2_id

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
