from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

from odoo.addons.bcr_planning_custom_sh.models.model import cek_date_lock_act, cek_date_lock_act_message

import logging

_logger = logging.getLogger(__name__)


class InheritActDelay(models.Model):
    _name = 'act.delay'
    _order = 'date_act desc'
    _inherit = ['act.delay', 'mail.thread', 'mail.activity.mixin']

    area_id = fields.Many2one('master.area', string='PIT', required=True)
    shift_id = fields.Many2one('master.shift', string='Shift', required=False)
    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', domain="[('code', 'in', ['LT-RN', 'LT-ID'])]", required=False)
    product = fields.Many2one('product.product', string='Product', required=False, default=False)
    validation_plan = fields.One2many('validation.plan', 'validation_act_delay_id', string='Validation',
                                      default=False)
    state = fields.Selection(tracking=True)
    delay_line_ids = fields.One2many('act.delay.line', 'delay_id', string='Weather Detail', store=True)

    # Total
    total_rain = fields.Float('Total Rain(Hour)', compute='_calc_total_line', store=True)
    total_slippery = fields.Float('Total Slippery(Hour)', compute='_calc_total_line', store=True)
    total_rainfall = fields.Float('Total Rainfall(mm)', compute='_calc_total_line', store=True)

    # ===================================================================================================
    @api.depends('delay_line_ids', 'delay_line_ids.rain', 'delay_line_ids.slippery', 'delay_line_ids.rainfall', 'state')
    def _calc_total_line(self):
        for delay in self:
            delay.total_rain = sum(line.rain for line in delay.delay_line_ids) or 0.0
            delay.total_slippery = sum(line.slippery for line in delay.delay_line_ids) or 0.0
            delay.total_rainfall = sum(line.rainfall for line in delay.delay_line_ids) or 0.0

    # ** Override
    # ** Because function add conditional not available for super method
    @api.onchange('sub_activity_id')
    def _onchange_sub_activity_id(self):
        if self.sub_activity_id:
            self.product = False
            if self.sub_activity_id.code == 'LT-ID':
                return {'domain': {'product': [('sub_activity_id', '=', self.sub_activity_id.id), ('default_code', 'in', ['I19', 'I20'])]}}
            else:
                return {'domain': {'product': [('sub_activity_id', '=', self.sub_activity_id.id)]}}

    # Button Submit and Revise
    def action_submit(self):
        for act_delay in self:
            if cek_date_lock_act("input", self.env.user.id, act_delay.date_act):
                raise UserError(cek_date_lock_act_message("input"))
            if act_delay.state == 'draft':
                act_delay.write({
                    'state': 'complete'
                })
            return

    def action_revise(self):
        for act_delay in self:
            if act_delay.state == 'complete':
                act_delay.write({
                    'state': 'draft'
                })
        return

    @api.constrains('volume')
    def _check_volume(self):
        for act_delay in self:
            if act_delay.volume <= 0.0:
                continue

    @api.constrains('kontraktor_id', 'bu_company_id')
    def _check_kontraktor(self):
        for act_delay in self:
            if act_delay.kontraktor_id.company_id != act_delay.bu_company_id:
                raise ValidationError(_("Bisnis Unit Not same with Kontraktor"))

    @api.constrains('area_id', 'bu_company_id')
    def _check_area(self):
        for act_delay in self:
            if act_delay.area_id.bu_company_id != act_delay.bu_company_id:
                raise ValidationError(_("Bisnis Unit Not same with PIT"))


class ActDelayLine(models.Model):
    _name = 'act.delay.line'
    _description = 'Weather Detail'

    delay_id = fields.Many2one('act.delay', string="Delay", store=True)
    kontraktor_id = fields.Many2one('res.partner', string='Kontraktor', related='delay_id.kontraktor_id')
    shift_mode_id = fields.Many2one('master.shiftmode', string='Shift Mode', related='kontraktor_id.shift_mode_id')
    shift_line_id = fields.Many2one('master.shiftmode.line', string='Shift', required=True, domain="[('shift_mode_id', '=', shift_mode_id)]")
    rain = fields.Float('Rain', store=True)
    slippery = fields.Float('Slippery', store=True)
    rainfall = fields.Float('Rainfall', store=True)

    @api.constrains('shift_line_id', 'shift_mode_id')
    def _check_shift(self):
        for delay_line in self:
            if delay_line.shift_line_id.shift_mode_id != delay_line.shift_mode_id:
                 raise ValidationError(_("Shift Not same in kontraktor"))
