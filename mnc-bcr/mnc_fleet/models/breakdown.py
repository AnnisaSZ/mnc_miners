from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging


_logger = logging.getLogger(__name__)

ROMAN_NUMBER = {
    '1': 'I',
    '2': 'II',
    '3': 'III',
    '4': 'IV',
    '5': 'V',
    '6': 'VI',
    '7': 'VII',
    '8': 'VIII',
    '9': 'IX',
    '10': 'X',
    '11': 'XI',
    '12': 'XII',
}


class FleetBreakdown(models.Model):
    _name = "fleet.breakdown"
    _description = "Fleet Breakdown"
    _rec_name = 'code_seq'

    code_seq = fields.Char('No.', store=True, default="#", required=True)
    date = fields.Date('Date', store=True, required=True)
    close_datetime = fields.Datetime('Close Date', store=True)
    revise_datetime = fields.Datetime('Last Revise Date', store=True)
    unit_equip_id = fields.Many2one('fleet.equipment.unit', string='Unit Equipment', store=True, required=True)
    shift_id = fields.Many2one('master.shiftmode', string='Shift Mode', related='unit_equip_id.shift_mode_id', store=True)
    shift_line_id = fields.Many2one('master.shiftmode.line', string='Shift', domain="[('shift_mode_id', '=', shift_id)]")
    breakdown_id = fields.Many2one('product.template', string='Breakdown Code', domain="[('sub_activity_id.code', '=', 'LT-BD')]", store=True, required=True)
    start_bd = fields.Float('Start BD', store=True, required=True)
    rfu = fields.Float('RFU', store=True, required=False)
    open_mechanical = fields.Float('Mekanik Datang', store=True)
    hm_breakdown = fields.Integer('HM Breakdown', store=True, required=True)
    hm_rfu = fields.Integer('HM RFU', store=True, required=False)
    location_id = fields.Many2one('fleet.master.location', 'Location', store=True, required=True)
    pelapor_bd = fields.Char('Pelapor BD', store=True, required=True)
    pelapor_rfu = fields.Char('Pelapor RFU', store=True, required=False)
    workorder_no = fields.Char('Workorder No.', store=True)
    remarks = fields.Text('Remarks', store=True, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Close'),
        ('revise', 'Revise'),
    ], string='Status', default='draft', store=True, tracking=True)
    # Relation to Hourly
    hourly_id = fields.Many2one('fleet.hourly.prod', string='Hourly Production', store=True)
    hourly_operational_ids = fields.Many2many('fleet.hourly.prod', string='Hourly Production', store=True)
    shiftly_id = fields.Many2one('fleet.shiftly.prod', string='Shiftly Production', store=True)
    is_revise = fields.Boolean('Revise')

    def action_close(self):
        self.write({
            'close_datetime': fields.Datetime.now(),
            'state': 'close',
        })
        return

    def action_revise(self):
        self.write({
            'revise_datetime': fields.Datetime.now(),
            'is_revise': True,
            'state': 'revise',
        })
        return

    @api.constrains('start_bd', 'rfu', 'open_mechanical')
    def _check_time_float(self):
        for breakdown in self:
            if breakdown.start_bd:
                if breakdown.start_bd > 23.983333333333334:
                    raise ValidationError(_("the time limit exceeds 23:59 hours."))
            if breakdown.rfu:
                if breakdown.rfu > 23.983333333333334:
                    raise ValidationError(_("the time limit exceeds 23:59 hours."))
            if breakdown.open_mechanical:
                if breakdown.open_mechanical > 23.983333333333334:
                    raise ValidationError(_("the time limit exceeds 23:59 hours."))

    # Method Combination
    def combination_sequence(self, sequence_code):
        code_month = ROMAN_NUMBER[str(self.date.month)]
        sequence_code = sequence_code.replace('MONTH', code_month)
        return sequence_code

    @api.model
    def create(self, vals):
        res = super(FleetBreakdown, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('break.down')
        sequence_code = res.combination_sequence(seq)
        res.update({"code_seq": sequence_code})
        return res

    @api.constrains('unit_equip_id', 'date', 'shift_line_id', 'start_bd', 'rfu')
    def _check_validation_unit(self):
        for bd in self:
            interface = bd.unit_equip_id.interface_id
            if interface.name == 'EX':
                hourly_id = self.env['fleet.hourly.prod'].search([('unit_equip_id', '=', bd.unit_equip_id.id), ('shift_line_id', '=', bd.shift_line_id.id), ('date', '=', bd.date)], limit=1)
                for line in hourly_id.line_ids:
                    if bd.start_bd and not bd.rfu:
                        validation_unit = bd.validation_unit_ready(line, bd.start_bd)
                        if validation_unit:
                            raise ValidationError(_("unit have detail operations"))
            else:
                hourly_line_ids = self.env['fleet.hourly.line'].search([('dumptruck_id', '=', bd.unit_equip_id.id), ('shift_line_id', '=', bd.shift_line_id.id), ('date', '=', bd.date)])
                if hourly_line_ids:
                    for hourly_line in hourly_line_ids:
                        if self.start_bd and not self.rfu:
                            validation_unit = self.validation_unit_ready(hourly_line, bd.start_bd)
                            if validation_unit:
                                raise ValidationError(_("unit have detail operations"))
                        else:
                            if hourly_line.time_from <= bd.start_bd and hourly_line.time_to >= bd.rfu:
                                raise ValidationError(_("unit have detail operations"))

    def validation_unit_ready(self, line_id, start_breakdown):
        if line_id.time_from <= start_breakdown and line_id.time_to >= start_breakdown:
            return True
        else:
            return False

    @api.onchange('unit_equip_id', 'date', 'shift_line_id', 'start_bd', 'rfu')
    def set_production(self):
        # Cek Tipe Unit
        if self.shift_line_id.shift_mode_id != self.shift_id:
            self.shift_line_id = False
        if self.unit_equip_id:
            interface = self.unit_equip_id.interface_id
            if interface.name == 'EX':
                hourly_id = self.env['fleet.hourly.prod'].search([('unit_equip_id', '=', self.unit_equip_id.id), ('shift_line_id', '=', self.shift_line_id.id), ('date', '=', self.date)], limit=1)
                for line in hourly_id.line_ids:
                    if self.start_bd and not self.rfu:
                        validation_unit = self.validation_unit_ready(line, self.start_bd)
                        if validation_unit:
                            return {
                                'warning': {
                                    'title': "Invalid Timerange",
                                    'message': "unit have detail operations",
                                }
                            }
            else:
                hourly_line_ids = self.env['fleet.hourly.line'].search([('dumptruck_id', '=', self.unit_equip_id.id), ('shift_line_id', '=', self.shift_line_id.id), ('date', '=', self.date)])
                if hourly_line_ids:
                    for hourly_line in hourly_line_ids:
                        if self.start_bd and not self.rfu:
                            validation_unit = self.validation_unit_ready(hourly_line, self.start_bd)
                            if validation_unit:
                                return {
                                    'warning': {
                                        'title': "Invalid Timerange",
                                        'message': "unit have detail operations",
                                    }
                                }
                        else:
                            if hourly_line.time_from <= self.start_bd and hourly_line.time_to >= self.rfu:
                                return {
                                    'warning': {
                                        'title': "Invalid Timerange",
                                        'message': "unit have detail operations",
                                    }
                                }
