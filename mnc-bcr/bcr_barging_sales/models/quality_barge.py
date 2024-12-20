from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, date
from odoo.tools.safe_eval import safe_eval

import logging

_logger = logging.getLogger(__name__)


class Qualitybarge(models.Model):
    _name = "quality.barge"
    _description = 'Quality barge'
    _rec_name = "shipping_id"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Set Validation
    def set_validation(self):
        result = False
        bu_id = self.env.company.id
        if bu_id:
            ####
            validation = self.env['validation.validation'].search([
                ('model_id.model', '=', self._name),
                ('bu_company_id', '=', bu_id)], limit=1)
            vals = []

            if validation:
                for rec in validation.validation_line:
                    vals.append((0, 0, {
                        'user_id': rec.user_id.id,
                        'validation_type_id': rec.validation_type_id.id,
                    }))
            else:
                raise UserError('Validation untuk Form Quality Barge belum disetting')
            result = vals
        return result

    active = fields.Boolean('Active', store=True, default=True)
    validation_plan = fields.One2many('validation.plan', 'validation_quality_barge_id', string='Validation',
        default=lambda self: (self.set_validation()))

    shipping_id = fields.Many2one('sales.shipping', 'Shipping', required=True, store=True)
    company_id = fields.Many2one('res.company', force_save='1', string='Bisnis Unit', default=lambda self: (self.env.company.id))

    barge_detail_id = fields.Many2one('master.barge', string='Barge Name', store=True)
    product_id = fields.Many2one('product.template', string="Product Spec", store=True, required=True, domain="[('is_marketing', '=', True)]", tracking=True)
    barge_lineup_id = fields.Many2one('barge.lineup', string="Barge Lineup", store=True, required=True, domain="[('shipping_id', '=', shipping_id)]")
    # Barge
    barge_id = fields.Many2one('master.barge', related='barge_lineup_id.barge_id', string='Barge Name', store=True)
    tugboat_id = fields.Many2one('master.tugboat', related='barge_lineup_id.tugboat_id', string='Tugboat Name', store=True)
    provisional_quantity = fields.Float('Provisional Qty', store=True)
    laycan_start = fields.Date('Laycan Start', store=True, required=True)
    laycan_end = fields.Date('Laycan End', store=True, required=True)
    # Approval
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approve'),
        ('complete', 'Complete'),
    ], string='State', default='draft', readonly=True)
    is_user_approval = fields.Boolean('User Approve', compute='_compute_is_approval')
    attachment = fields.Binary('Attachments')
    filename_attachment = fields.Char('Name Attachments', store=True)
    # Carrier
    carrier = fields.Selection([
        ('mv', 'MV'),
        ('barge', 'Barge'),
    ], default='mv', string="Carrier", store=True)
    mv_id = fields.Many2one('master.mv', string='MV Name', store=True)
    # is_approver = fields.Boolean(string='is approve', compute='_set_approver')

    # ====== Approval ======
    # def _set_approver(self):
    #     for qualtiy_barge in self:
    #         approver = qualtiy_barge.validation_plan.filtered(lambda x: x.user_id.id == self.env.user.id)
    #         if approver:
    #             qualtiy_barge.is_approver = True
    #         else:
    #             qualtiy_barge.is_approver = False
    # barge_id = fields.Many2one('master.barge', string='Barge Name', store=True)

    def _compute_is_approval(self):
        for record in self:
            users = []
            for validation in record.validation_plan:
                users.append(validation.user_id.id)
            if self.env.uid in users:
                record.is_user_approval = True
            else:
                record.is_user_approval = False

    def action_submit(self):
        for qualtiy_barge in self:
            if not qualtiy_barge.attachment:
                raise ValidationError(_("Please upload attachment before submit"))
            qualtiy_barge.write({
                'state': 'waiting'
            })
        return

    def action_approve(self):
        for qualtiy_barge in self:
            users = []
            for user_validation in qualtiy_barge.validation_plan:
                users.append(user_validation.user_id.id)

            if self.env.uid in users:
                qualtiy_barge.write({
                    'state': 'complete'
                })
            else:
                raise ValidationError(_("You cann't approver"))
            return

    def action_revise(self):
        for qualtiy_barge in self:
            if qualtiy_barge.state == 'complete':
                qualtiy_barge.write({
                    'state': 'draft'
                })
        return

    @api.constrains('laycan_start', 'laycan_end')
    def _check_duration_laycan(self):
        for qualtiy_barge in self:
            if qualtiy_barge.laycan_start and qualtiy_barge.laycan_end:
                diff_date = qualtiy_barge.laycan_end - qualtiy_barge.laycan_start
                if diff_date.days > 6 or diff_date.days < 2:
                    raise ValidationError(_("Laycan Date Max 7 Days or Min 3 Days Duration"))

    # Blending
    blending_plan_ids = fields.One2many('blending.plan', 'quality_barge_id', string='Blending Plan', store=True)

    # Result
    volume = fields.Float('Volume', compute='_calc_total_blending_plan', store=True)
    blend_percentage = fields.Float('%', store=True)
    tm_ar = fields.Float('TM AR', compute='_calc_total_blending_plan', store=True)
    im_adb = fields.Float('IM ADB', compute='_calc_total_blending_plan', store=True)
    ash_adb = fields.Float('ASH ADB', compute='_calc_total_blending_plan', store=True)
    fc_adb = fields.Float('FC ADB', compute='_calc_total_blending_plan', store=True)
    vm_adb = fields.Float('VM ADB', compute='_calc_total_blending_plan', store=True)
    ts = fields.Float('TS', compute='_calc_total_blending_plan', store=True)
    cv_ar = fields.Float('CV AR', compute='_calc_total_blending_plan', store=True)
    cv_adb = fields.Float('CV ADB', compute='_calc_total_blending_plan', store=True)

    @api.onchange('shipping_id')
    def change_value_ship(self):
        if self.shipping_id:
            shipping_id = self.shipping_id
            # Set Value
            # self.carrier = shipping_id.remark_mv
            self.mv_id = shipping_id.mv_id
            # self.barge_id = shipping_id.barge_id
            self.product_id = shipping_id.product_id
            self.laycan_start = shipping_id.laycan_start
            self.laycan_end = shipping_id.laycan_end
        else:
            # self.carrier = False
            self.mv_id = False
            # self.barge_id = False
            self.product_id = False
            self.laycan_start = False
            self.laycan_end = False

    @api.onchange('barge_lineup_id')
    def change_value_barge_lineup(self):
        if self.barge_lineup_id:
            barge_lineup_id = self.barge_lineup_id
            # Set Value
            self.provisional_quantity = barge_lineup_id.provisional_quantity
        else:
            self.provisional_quantity = False

    @api.depends('blending_plan_ids')
    def _calc_total_blending_plan(self):
        for qualtiy_barge in self:
            total_volume =  sum(line.volume for line in qualtiy_barge.blending_plan_ids) or 0
            if total_volume > 0:
                qualtiy_barge.volume = total_volume
                # ========= Get TM AR =========
                volume, tm_ar = qualtiy_barge._get_datas('tm_ar')
                qualtiy_barge.tm_ar = (sum(map(lambda x, y: x * y, volume, tm_ar))/total_volume) or 0
                # ========= Get IM ADB =========
                volume, im_adb = qualtiy_barge._get_datas('im_adb')
                qualtiy_barge.im_adb = (sum(map(lambda x, y: x * y, volume, im_adb))/total_volume) or 0
                # ========= Get ASH ADB =========
                volume, ash_adb = qualtiy_barge._get_datas('ash_adb')
                qualtiy_barge.ash_adb = (sum(map(lambda x, y: x * y, volume, ash_adb))/total_volume) or 0
                # ========= Get FC ADB =========
                volume, fc_adb = qualtiy_barge._get_datas('fc_adb')
                qualtiy_barge.fc_adb = (sum(map(lambda x, y: x * y, volume, fc_adb))/total_volume) or 0
                # ========= Get FC ADB =========
                volume, vm_adb = qualtiy_barge._get_datas('vm_adb')
                qualtiy_barge.vm_adb = (sum(map(lambda x, y: x * y, volume, vm_adb))/total_volume) or 0
                # ========= Get FC ADB =========
                volume, ts = qualtiy_barge._get_datas('ts')
                qualtiy_barge.ts = (sum(map(lambda x, y: x * y, volume, ts))/total_volume) or 0
                # ========= Get CV AR =========
                volume, cv_ar = qualtiy_barge._get_datas('cv_ar')
                qualtiy_barge.cv_ar = (sum(map(lambda x, y: x * y, volume, cv_ar))/total_volume) or 0
                # =========
                # ========= Get CV ADB =========
                volume, cv_adb = qualtiy_barge._get_datas('cv_adb')
                qualtiy_barge.cv_adb = (sum(map(lambda x, y: x * y, volume, cv_adb))/total_volume) or 0
            else:
                qualtiy_barge.volume = 0
                # ========= Get TM AR =========
                qualtiy_barge.tm_ar = 0
                # =========
                qualtiy_barge.im_adb = 0
                qualtiy_barge.ash_adb = 0
                qualtiy_barge.fc_adb = 0
                qualtiy_barge.vm_adb = 0
                qualtiy_barge.ts = 0
                qualtiy_barge.cv_ar = 0
                qualtiy_barge.cv_adb = 0

    # Get Data
    def _get_datas(self, code):
        codes = _("result = line.%s") % (code)
        volume = []
        datas = []
        for line in self.blending_plan_ids:
            volume.append(line.volume)
            localdict = {
                **{
                    'line': line,
                    'result': 0
                }
            }
            try:
                safe_eval(codes, localdict, mode="exec", nocopy=True)
                datas.append(localdict['result'])
            except Exception as e:
                raise ValidationError(e)
        return volume, datas


class BlendingPlan(models.Model):
    _name = "blending.plan"
    _description = 'Blending Plan'

    quality_barge_id = fields.Many2one('quality.barge', string='Quality Barge', store=True, ondelete='cascade')
    area_id = fields.Many2one('master.area', string='PIT', required=True, store=True)
    seam_id = fields.Many2one('master.seam', string='Seam Code', required=True, store=True, domain="[('area_id', '=', area_id)]")
    volume = fields.Float('Volume', store=True, required=True)
    blend_percentage = fields.Float('%', store=True, compute='_calc_percentage')
    tm_ar = fields.Float('TM AR', store=True, required=True)
    im_adb = fields.Float('IM ADB', store=True, required=True)
    ash_adb = fields.Float('ASH ADB', store=True, required=True)
    fc_adb = fields.Float('FC ADB', store=True, required=True)
    vm_adb = fields.Float('VM ADB', store=True, required=True)
    ts = fields.Float('TS', store=True, required=True)
    cv_ar = fields.Float('CV AR', store=True, required=True)
    cv_adb = fields.Float('CV ADB', store=True, required=True)

    @api.depends('volume', 'quality_barge_id', 'quality_barge_id.blending_plan_ids')
    def _calc_percentage(self):
        for blending in self:
            total_percentage = 0
            total_volume = sum(line.volume for line in blending.quality_barge_id.blending_plan_ids) or 0
            if blending.volume:
                if total_volume != blending.volume:
                    total_percentage = ((blending.volume / total_volume) * 100) or 0
                else:
                    total_percentage = blending.volume or 0
            blending.blend_percentage = total_percentage

    @api.onchange('area_id')
    def change_seam(self):
        if self.area_id:
            self.seam_id = False
