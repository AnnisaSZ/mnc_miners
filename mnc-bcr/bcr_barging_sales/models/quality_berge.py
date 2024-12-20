from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, date

import logging

_logger = logging.getLogger(__name__)


class QualityBerge(models.Model):
    _name = "quality.berge"
    _description = 'Quality Berge'
    _rec_name = "shipping_id"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    shipping_id = fields.Many2one('sales.shipping', 'Shipping', required=True, store=True)
    mv_id = fields.Many2one('master.mv', string='MV Name', store=True)
    berge_detail_id = fields.Many2one('master.barge', string='Barge Name', store=True)
    product_id = fields.Many2one('product.template', string="Product Spec", store=True, required=True, domain="[('is_marketing', '=', True)]", tracking=True)
    berge_lineup_id = fields.Many2one('barge.lineup', string="Barge", store=True, required=True, domain="[('shipping_id', '=', shipping_id)]")
    berge_id = fields.Many2one('master.barge', string='Barge Name', store=True)
    provisional_quantity = fields.Float('Provisional Qty', store=True)
    laycan_start = fields.Date('Laycane Start', store=True, required=True)
    laycan_end = fields.Date('Laycane End', store=True, required=True)
    attachment = fields.Binary('Attachments')
    filename_attachment = fields.Char('Name Attachments', store=True)

    @api.constrains('laycan_start', 'laycan_end')
    def _check_duration_laycan(self):
        for qualtiy_barge in self:
            if qualtiy_barge.shipping_id.contract_type == 'Spot':
                if qualtiy_barge.laycan_start and qualtiy_barge.laycan_end:
                    diff_date = qualtiy_barge.laycan_end - qualtiy_barge.laycan_start
                    if diff_date.days > 7 or diff_date.days < 3:
                        raise ValidationError(_("Laycan Date Max 7 Days or Min 3 Days Duration"))

    # Blending
    blending_plan_ids = fields.One2many('blending.plan', 'quality_barge_id', string='Blending Plan', store=True)

    # Result
    volume = fields.Float('Volume', compute='_calc_total_blending_plan', store=True)
    blend_percentage = fields.Float('%', compute='_calc_total_blending_plan', store=True)
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
            self.mv_id = shipping_id.mv_id
            self.product_id = shipping_id.product_id
            self.laycan_start = shipping_id.laycan_start
            self.laycan_end = shipping_id.laycan_end
        else:
            self.mv_id = False
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
            qualtiy_barge.volume = sum(line.volume for line in qualtiy_barge.blending_plan_ids) or 0
            qualtiy_barge.blend_percentage = sum(line.blend_percentage for line in qualtiy_barge.blending_plan_ids) or 0
            qualtiy_barge.tm_ar = sum(line.tm_ar for line in qualtiy_barge.blending_plan_ids) or 0
            qualtiy_barge.im_adb = sum(line.im_adb for line in qualtiy_barge.blending_plan_ids) or 0
            qualtiy_barge.ash_adb = sum(line.ash_adb for line in qualtiy_barge.blending_plan_ids) or 0
            qualtiy_barge.fc_adb = sum(line.fc_adb for line in qualtiy_barge.blending_plan_ids) or 0
            qualtiy_barge.vm_adb = sum(line.vm_adb for line in qualtiy_barge.blending_plan_ids) or 0
            qualtiy_barge.ts = sum(line.ts for line in qualtiy_barge.blending_plan_ids) or 0
            qualtiy_barge.cv_ar = sum(line.cv_ar for line in qualtiy_barge.blending_plan_ids) or 0
            qualtiy_barge.cv_adb = sum(line.cv_adb for line in qualtiy_barge.blending_plan_ids) or 0


class BlendingPlan(models.Model):
    _name = "blending.plan"
    _description = 'Blending Plan'

    quality_barge_id = fields.Many2one('quality.berge', string='Quality Barge', store=True)
    area_id = fields.Many2one('master.area', string='Area', required=True, store=True)
    seam_id = fields.Many2one('master.seam', string='Seam Code', required=True, store=True, domain="[('area_id', '=', area_id)]")
    volume = fields.Float('Volume', store=True, required=True)
    blend_percentage = fields.Float('%', store=True)
    tm_ar = fields.Float('TM AR', store=True, required=True)
    im_adb = fields.Float('IM ADB', store=True, required=True)
    ash_adb = fields.Float('ASH ADB', store=True, required=True)
    fc_adb = fields.Float('FC ADB', store=True, required=True)
    vm_adb = fields.Float('VM ADB', store=True, required=True)
    ts = fields.Float('TS', store=True, required=True)
    cv_ar = fields.Float('CV AR', store=True, required=True)
    cv_adb = fields.Float('CV ADB', store=True, required=True)
