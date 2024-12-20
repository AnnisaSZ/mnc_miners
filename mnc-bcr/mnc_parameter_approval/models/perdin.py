from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError
import ast


class perjalanandinasModels(models.Model):
    _inherit = 'perjalanan.dinas.requestion.module'

    # Add Params
    head_dept_params_ids = fields.Many2many(
        'mncei.jabatan', 'head_dept_params_rel', 'params_id', 'head_dept_id',
        string='Jabatan Head Department', compute='_get_params_approval', copy=False
    )
    spv_params_ids = fields.Many2many(
        'mncei.jabatan', 'head_dept_params_rel', 'params_id', 'spv_params_id',
        string='Jabatan Head Department', compute='_get_params_approval', copy=False
    )
    # Department
    direksi_params_ids = fields.Many2many(
        'mncei.department', 'direksi_params_rel', 'params_id', 'direksi_params_id',
        string='Jabatan Head Department', compute='_get_params_approval', copy=False
    )
    hrga_dept_params_ids = fields.Many2many(
        'mncei.department', 'hrga_dept_perdin_rel', 'params_id', 'hrga_dept_id',
        string='HR Dept', copy=False)
    ga_dept_params_ids = fields.Many2many(
        'mncei.department', 'ga_dept_perdin_rel', 'params_id', 'ga_dept_id',
        string='GA Department', copy=False)
    # direksi_dept_params_ids = fields.Many2many(
    #     'mncei.department', 'direksi_dept_perdin_rel', 'params_id', 'direksi_dept_id',
    #     string='Direksi', copy=False)
    # Setting Approval
    res_config_approval_id = fields.Many2one('res.config.approval', string="Config Approval", compute='_get_config_approval')

    @api.depends('perusahaan')
    def _get_config_approval(self):
        for perdin in self:
            perdin.res_config_approval_id = False
            if perdin.perusahaan:
                config_id = self.env['res.config.approval'].search([('company_id', '=', perdin.perusahaan.id), ('model_type', '=', 'perdin')], limit=1)
                valid_warning = _("Please input configuration approval in %s") % (perdin.perusahaan.name)
                if not config_id and perdin.state == 'draft':
                    raise ValidationError(_(valid_warning))
                elif config_id:
                    perdin.res_config_approval_id = config_id.id

    @api.onchange('res_config_approval_id')
    def set_approval(self):
        if self.res_config_approval_id:
            self.head_ga_id = self.res_config_approval_id.ga_id
            self.hrga_id = self.res_config_approval_id.hr_id
            self.head_hrga_id = self.res_config_approval_id.head_hrga_id
            self.direksi_id = self.res_config_approval_id.direksi1_id
            self.direksi_optional_id = self.res_config_approval_id.direksi2_id

    @api.depends('nama_karyawan', 'department_id')
    def _get_params_approval(self):
        for perdin in self:
            params_obj = self.env['ir.config_parameter']
            perdin.head_dept_params_ids = False
            perdin.spv_params_ids = False
            perdin.hrga_dept_params_ids = False
            perdin.ga_dept_params_ids = False
            perdin.direksi_params_ids = False
            head_dept_params = ast.literal_eval(params_obj.sudo().get_param('head_dept_id') or '[]')
            spv_params_ids = ast.literal_eval(params_obj.sudo().get_param('spv_id') or '[]')
            hrga_dept_params_ids = ast.literal_eval(params_obj.sudo().get_param('hrga_dept_id') or '[]')
            ga_dept_params_ids = ast.literal_eval(params_obj.sudo().get_param('ga_dept_id') or '[]')
            direksi_params_ids = ast.literal_eval(params_obj.sudo().get_param('bod_dept_id') or '[]')
            # if head_dept_params:
            perdin.head_dept_params_ids = [(6, 0, head_dept_params)]
            perdin.spv_params_ids = [(6, 0, spv_params_ids)]
            perdin.hrga_dept_params_ids = [(6, 0, hrga_dept_params_ids)]
            perdin.ga_dept_params_ids = [(6, 0, ga_dept_params_ids)]
            perdin.direksi_params_ids = [(6, 0, direksi_params_ids)]

    mncei_dept_id = fields.Many2one(
        'mncei.department',
        string='Div/Dept', related='requestor_id.mncei_dept_id', store=True
    )
    def _compute_is_hr_uid(self):
        for record in self:
            if self.env.user.mncei_dept_id.id in record.hrga_dept_params_ids.ids:
                record.is_hr_uid = True
            else:
                record.is_hr_uid = False

    # Inherit Fields
    is_hr_uid = fields.Boolean(string="Is GA User", default=True, compute='_compute_is_hr_uid')
    head_dept_id = fields.Many2one('res.users', string='Head Department', store=True, required=True)

    def action_declaration(self):
        if self.state == 'approve':
            self.update({
                'is_declaration': True,
            })
        return
