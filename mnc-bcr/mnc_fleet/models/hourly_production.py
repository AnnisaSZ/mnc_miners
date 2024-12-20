from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.http import request

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


def float_to_time_str(float_val):
    # Mengonversi float menjadi detik total
    total_seconds = int(float_val * 3600)

    # Menghitung jam, menit, dan detik
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Membuat string format HH:MM:SS
    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"

    return time_str


def get_times_float(float_time, date, next_days=False):
    if next_days:
        return datetime.strptime(f"{(date + timedelta(days=1))} {float_to_time_str(float_time)}", "%Y-%m-%d %H:%M:%S")
    else:
        return datetime.strptime(f"{date} {float_to_time_str(float_time)}", "%Y-%m-%d %H:%M:%S")


def check_timerange(times_start, times_end, shift_line, date):
    if shift_line.start > shift_line.end:
        start_time = get_times_float(shift_line.start, date)
        end_time = get_times_float(shift_line.end, date, next_days=True)
        if times_start > times_end:
            act_start = get_times_float(times_start, date)
            act_end = get_times_float(times_end, date, next_days=True)
            if act_start < start_time or act_end > end_time:
                return True
            else:
                return False
        else:
            act_start = get_times_float(times_start, date)
            act_end = get_times_float(times_end, date)
            if act_start < start_time or act_end > end_time:
                return True
            else:
                return False
    else:
        start_time = get_times_float(shift_line.start, date)
        end_time = get_times_float(shift_line.end, date)
        # Act Time
        act_start = get_times_float(times_start, date)
        act_end = get_times_float(times_end, date)
        if act_start < start_time or act_end > end_time:
            return True
        else:
            return False


def check_breakdown_unit(time_start, time_end, unit_id, shift_line, date):
    bd_obj = request.env['fleet.breakdown']
    bd_id = bd_obj.search([
        ('unit_equip_id', '=', unit_id.id),
        ('shift_line_id', '=', shift_line.id),
        ('date', '=', date),
        ('state', '=', 'draft'),
    ], limit=1)
    if bd_id:
        if time_start >= bd_id.start_bd and not bd_id.rfu:
            return True
        elif time_start >= bd_id.start_bd and time_end <= bd_id.rfu:
            return True
        else:
            return False
    else:
        return False


class HourlyProductivity(models.Model):
    _name = "fleet.hourly.prod"
    _rec_name = "code_seq"
    _description = "Hourly Production"

    code_seq = fields.Char('No.', store=True, default="#", required=False)
    name = fields.Char('Name', compute='_compute_name')
    date = fields.Date('Date', store=True, required=True)
    unit_equip_id = fields.Many2one('fleet.equipment.unit', string='Unit Equipment', store=True, required=True, domain="[('interface_id.name', '=', 'EX')]")
    equipment_group_id = fields.Many2one('fleet.equipment.group', string='Equipment Group', related='unit_equip_id.equipment_group_id', store=True)
    shift_id = fields.Many2one('master.shiftmode', string='Shift Mode', related='unit_equip_id.shift_mode_id', store=True)
    shift_line_id = fields.Many2one('master.shiftmode.line', string='Shift', domain="[('shift_mode_id', '=', shift_id)]")
    operator_id = fields.Many2one('fleet.master.operator', string='Operator', store=True, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Close'),
    ], string='Status', default='draft', store=True, tracking=True)
    # operation
    line_ids = fields.One2many('fleet.hourly.line', 'hourly_id', string="Detail Operation")
    line_lost_ids = fields.One2many('fleet.hourly.lost', 'hourly_id', string="Losttime")
    breakdown_ids = fields.One2many('fleet.breakdown', 'hourly_id', string="Breakdown")
    breakdown_unit_ids = fields.Many2many('fleet.breakdown', string="Breakdown")

    @api.constrains('unit_equip_id', 'shift_line_id', 'date')
    def _check_validity_hourly_productions(self):
        """ verifies if check_in is earlier than check_out. """
        for hourly in self:
            hourly_ids = self.env['fleet.hourly.prod'].search([('unit_equip_id', '=', hourly.unit_equip_id.id), ('shift_line_id', '=', hourly.shift_line_id.id), ('date', '=', hourly.date), ('id', '!=', hourly.id)])
            if hourly_ids:
                raise ValidationError(_("Hourly with unit %s & Time %s [%s] already exist") % (hourly.unit_equip_id.number, hourly.date, hourly.shift_line_id.name))

    def action_close(self):
        if not self.line_ids:
            raise ValidationError(_("Please input detail operation"))
        self.write({
            'state': 'close',
        })
        if any(breakdown_id.state == 'draft' for breakdown_id in self.breakdown_ids):
            shift_detail = self.env['master.shiftmode.line'].search([('shift_mode_id', '=', self.shift_id.id), ('id', '!=', self.shift_line_id.id)])
            default = {
                'date': fields.Date.today(),
                'unit_equip_id': self.unit_equip_id.id,
                'operator_id': self.operator_id.id,
                'shift_id': self.shift_id.id,
                'shift_line_id': shift_detail.id if shift_detail else False,
            }
            res_id = self.copy(default)
            for breakdown_id in self.breakdown_ids.filtered(lambda x: x.state == 'draft'):
                breakdown_id.copy({'hourly_id': res_id.id})
                breakdown_id.action_close()
            datas = {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': res_id.id,
                'res_model': 'fleet.hourly.prod',
                'view_id': self.env.ref('mnc_fleet.fleet_hourly_prod_form').id,
                'context': {'form_view_initial_mode': 'edit'}
            }
            return datas

    def action_reset(self):
        self.write({
            'state': 'draft',
        })

    def action_view_breakdown(self):
        result = self.env['ir.actions.act_window']._for_xml_id('mnc_fleet.action_fleet_breakdown')
        result['context'] = {
            'create': 1,
            'delete': 0,
            'default_date': fields.Date.today(),
            'default_unit_equip_id': self.unit_equip_id.id,
            'default_shift_id': self.shift_id.id,
            'default_shift_line_id': self.shift_line_id.id,
            'default_hourly_id': self.id
        }
        unit_ids = []
        for line in self.line_ids:
            unit_ids.append(line.dumptruck_id.id)
        unit_ids.append(self.unit_equip_id.id)
        breakdown_ids = self.env['fleet.breakdown'].search([
            ('date', '=', self.date),
            ('shift_line_id', '=', self.shift_line_id.id),
            ('unit_equip_id', 'in', unit_ids),
        ])
        # choose the view_mode accordingly
        if len(breakdown_ids) >= 1:
            result['domain'] = [('id', 'in', breakdown_ids.ids)]
        elif len(breakdown_ids) < 1:
            res = self.env.ref('mnc_fleet.fleet_breakdown_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = breakdown_ids[0].id if breakdown_ids else False
        return result

    # Method Combination
    def combination_sequence(self, sequence_code):
        code_month = ROMAN_NUMBER[str(self.date.month)]
        sequence_code = sequence_code.replace('MONTH', code_month)
        return sequence_code

    @api.model
    def create(self, vals):
        res = super(HourlyProductivity, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('hourly.production')
        sequence_code = res.combination_sequence(seq)
        res.update({"code_seq": sequence_code})
        return res

    @api.constrains('line_ids', 'line_ids.time_from', 'line_ids.time_to')
    def _check_timerange_operation(self):
        for hourly_id in self:
            for line in hourly_id.line_ids:
                check_bd = check_breakdown_unit(line.time_from, line.time_to, line.dumptruck_id, line.shift_line_id, hourly_id.date)
                if check_bd:
                    raise ValidationError(_("unit %s is breakdown") % (line.dumptruck_id.number))
                if line.time_from and line.time_to:
                    check_time = check_timerange(line.time_from, line.time_to, line.shift_line_id, hourly_id.date)
                    if check_time:
                        raise ValidationError(_("time is not within the shift's time range"))


class HourlyLine(models.Model):
    _name = "fleet.hourly.line"
    _description = "Hourly Production Line"

    hourly_id = fields.Many2one('fleet.hourly.prod', string='Hourly Production', store=True)
    date = fields.Date('Date', store=True, related="hourly_id.date")
    shift_line_id = fields.Many2one('master.shiftmode.line', string='Shift', related="hourly_id.shift_line_id", store=True)
    shift_id = fields.Many2one('master.shiftmode', string='Shift Mode', related='hourly_id.shift_id')
    timerange_id = fields.Many2one('fleet.timerange', string='Time Range', store=True)
    time_from = fields.Float('From', store=True, required=True)
    time_to = fields.Float('To', store=True, required=True)
    dumptruck_id = fields.Many2one('fleet.equipment.unit', string='Dumptruck', store=True, domain="[('interface_id.name', '=', 'DT')]")
    material_id = fields.Many2one('fleet.material', string='Material', store=True, required=True)
    ritase = fields.Integer('Ritase', store=True, required=True)
    is_volume = fields.Boolean('Manual Volume', store=True)
    volume = fields.Float('Volume', compute='calc_volume', store=True)

    @api.constrains('hourly_id', 'date', 'dumptruck_id', 'time_from', 'time_to')
    def _check_detail_operational(self):
        for line in self:
            hourly_line_ids = self.env['fleet.hourly.line'].search([('dumptruck_id', '=', line.dumptruck_id.id), ('date', '=', line.date), ('id', '!=', line.id), ('time_from', '>=', line.time_from), ('time_to', '<=', line.time_to)])
            if hourly_line_ids:
                raise ValidationError(_("unit have Detail Operational"))

    @api.onchange('dumptruck_id')
    def _onchange_materials(self):
        if self.dumptruck_id and self.material_id:
            self.material_id = False
        elif not self.dumptruck_id and self.material_id:
            self.material_id = False

    @api.onchange('time_from', 'time_to', 'shift_line_id')
    def _check_timerange(self):
        if self.time_from and self.time_to:
            check_time = check_timerange(self.time_from, self.time_to, self.shift_line_id, self.date)
            if check_time:
                return {
                    'warning': {
                        'title': "Invalid Timerange",
                        'message': "time is not within the shift's time range",
                    }
                }

    @api.onchange('is_volume', 'material_id', 'ritase', 'dumptruck_id', 'dumptruck_id.line_ids')
    def _change_volume(self):
        if not self.is_volume:
            if self.material_id and self.ritase:
                for capacity in self.dumptruck_id.line_ids.filtered(lambda x: x.fleet_material_id == self.material_id):
                    self.volume = capacity.capacity_unit * self.ritase
        else:
            self.volume = 0.0

    @api.depends('is_volume', 'dumptruck_id', 'ritase')
    def calc_volume(self):
        for line in self:
            res_volume = 0.0
            if line.is_volume == False:
                if line.material_id and line.ritase:
                    for capacity in line.dumptruck_id.line_ids.filtered(lambda x: x.fleet_material_id == line.material_id):
                        res_volume = capacity.capacity_unit * line.ritase
            line.volume = res_volume


class HourlyLosttime(models.Model):
    _name = "fleet.hourly.lost"
    _description = "Hourly LostTime"

    hourly_id = fields.Many2one('fleet.hourly.prod', string='Hourly Production', store=True)
    start = fields.Float('Start', store=True)
    end = fields.Float('End', store=True)
    losttime_id = fields.Many2one('fleet.losttime', string='Losttime', store=True, required=True)
    is_remarks = fields.Boolean('Is Remarks', related='losttime_id.is_remarks')
    rca_id = fields.Many2one('fleet.losttime.line', string='RCA', store=True)
