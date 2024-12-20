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

    # Approval
    requestor_dept_id = fields.Many2one(
        'mncei.department',
        string='Department', related='requestor_id.mncei_dept_id', store=True
    )
    res_config_approval_id = fields.Many2one('res.config.approval', string="Config Approval", compute='_get_config_approval')

    @api.depends('company_id')
    def _get_config_approval(self):
        for pr in self:
            pr.res_config_approval_id = False
            config_id = self.env['res.config.approval'].search([('company_id', '=', pr.company_id.id), ('model_type', '=', 'purchase_request')], limit=1)
            valid_warning = _("Please input configuration approval in %s") % (pr.company_id.name)
            if not config_id and pr.state == 'draft':
                raise ValidationError(_(valid_warning))
            elif config_id:
                pr.res_config_approval_id = config_id.id

    @api.onchange('res_config_approval_id')
    def set_approval(self):
        if self.res_config_approval_id:
            self.head_ga_id = self.res_config_approval_id.ga_id
            self.head_hrga_id = self.res_config_approval_id.head_hrga_id
            self.head_finance_id = self.res_config_approval_id.head_finance_id
            self.direksi1_id = self.res_config_approval_id.direksi1_id
            self.direksi2_id = self.res_config_approval_id.direksi2_id
            self.direksi3_id = self.res_config_approval_id.direksi3_id
            self.procurement_id = self.res_config_approval_id.procurement_id

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

    # Override Method
    def action_sign_approve(self):
        self.ensure_one()
        # Check GA
        if self.is_ga_uid:
            for item_id in self.line_ids:
                if item_id.est_price <= 0:
                    raise ValidationError(_("Please Input Price in Item"))
        is_procurement = False
        if self.state == 'procurement':
            is_procurement = True
        # Signature Check
        signature_type = self.env.user.choice_signature
        upload_signature = False
        digital_signature = False
        upload_signature_fname = ''
        if signature_type == 'upload':
            upload_signature = self.env.user.upload_signature
            upload_signature_fname = self.env.user.upload_signature_fname
            if not upload_signature:
                raise ValidationError(_("Please add your signature in Click Your name in Top Right > Preference > Signature"))
        elif signature_type == 'draw':
            digital_signature = self.env.user.digital_signature
            if not digital_signature:
                raise ValidationError(_("Please add your signature in Click Your name in Top Right > Preference > Signature"))
        else:
            raise ValidationError(_("Please add your signature in Click Your name in Top Right > Preference > Signature"))

        return {
            'name': _("Sign & Approve"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'purchase.requisition.approval.wizard',
            'view_id': self.env.ref('mnc_purchase_request.mncei_pr_approval_wizard_form').id,
            'context': {
                'default_is_procurement': is_procurement,
                'default_company_id': self.company_id.id,
                'default_choice_signature': signature_type,
                'default_digital_signature': digital_signature,
                'default_upload_signature': upload_signature,
                'default_upload_signature_fname': upload_signature_fname,
                'default_finance_dept_params_ids': self.finance_dept_params_ids.ids,
                'default_user_approval_ids': [(6, 0, self.user_approval_ids.ids)]
            },
        }
