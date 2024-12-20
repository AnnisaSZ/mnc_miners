from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from itertools import groupby
from ..models.hourly_production import get_times_float

import logging

_logger = logging.getLogger(__name__)


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


class ShiftProductivity(models.Model):
    _name = "fleet.shiftly.prod"
    _rec_name = "code_seq"
    _description = "Shift Production"

    code_seq = fields.Char('No.', store=True, default="#", required=True)
    name = fields.Char('Name', compute='_compute_name')
    date = fields.Date('Date', store=True, required=True)
    unit_equip_id = fields.Many2one('fleet.equipment.unit', string='Unit Equipment', store=True, required=True)
    equipment_group_id = fields.Many2one('fleet.equipment.group', string='Equipment Group', related='unit_equip_id.equipment_group_id', store=True)
    sub_kontraktor_id = fields.Many2one('fleet.sub.kontraktor', string='Sub Kontraktor', related='unit_equip_id.sub_kontraktor_id', store=True)
    shift_id = fields.Many2one('master.shiftmode', string='Shift Mode', related='unit_equip_id.shift_mode_id', store=True)
    shift_line_id = fields.Many2one('master.shiftmode.line', string='Shift', domain="[('shift_mode_id', '=', shift_id)]", required=True)
    hm_awal = fields.Float('HM Awal', store=True, required=True)
    hm_akhir = fields.Float('HM Akhir', store=True, required=True)
    hm_total = fields.Float('HM Total', store=True, required=True)
    wh_total = fields.Float('WH Total', compute='_get_calc_wh', store=True)
    lost_total = fields.Float('Total Losttime', store=True)
    operator_id = fields.Many2one('fleet.master.operator', string='Operator', store=True, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Close'),
    ], string='Status', default='draft', store=True, tracking=True)
    # operation
    line_ids = fields.One2many('fleet.shiftly.line', 'shiftly_id', string="Detail Operation")
    line_lost_ids = fields.One2many('fleet.shiftly.lost', 'shiftly_id', string="Losttime")
    breakdown_ids = fields.One2many('fleet.breakdown', 'shiftly_id', string="Breakdown")
    # flagging
    is_dt = fields.Boolean("DT")
    is_ex = fields.Boolean("EXA")
    is_ot = fields.Boolean("OT")

    def calc_worked_hours_shift(self, shift_line):
        total_worked = shift_line.end - shift_line.start
        return total_worked

    def calc_losttime_hourly(self, hourly_line):
        total_bd = 0
        breakdown_id = self.env['fleet.breakdown'].search([
            ('date', '=', self.date),
            ('shift_line_id', '=', self.shift_line_id.id),
            ('unit_equip_id', '=', self.unit_equip_id.id),
        ])
        if breakdown_id:
            if breakdown_id.rfu:
                print("========BD001=======")
                start_time = get_times_float(breakdown_id.start_bd, breakdown_id.date)
                end_time = get_times_float(breakdown_id.rfu, breakdown_id.date)
                total_bd += (end_time - start_time).total_seconds() / 3600
            else:
                print("========BD002=======")
                if self.shift_line_id.start > self.shift_line_id.end:
                    start_time = get_times_float(self.shift_line_id.start, self.date)
                    end_time = get_times_float(self.shift_line_id.end, self.date, next_days=True)
                else:
                    start_time = get_times_float(self.shift_line_id.start, self.date)
                    end_time = get_times_float(self.shift_line_id.end, self.date)
                total_bd += (end_time - start_time).total_seconds() / 3600
        return total_bd

    def _get_operation(self, line_ids):
        temp_detail_operations = []
        temp_losttime = []
        hourly_line_ids_sorted = sorted(line_ids, key=lambda m: m.material_id.id)
        total_losttime_engine_off = 0
        for material_id, grouped_lines in groupby(hourly_line_ids_sorted, key=lambda m: m.material_id.id):
            grouped_lines = list(grouped_lines)
            total_volume = 0
            total_ritase = 0
            total_wh_shift = 0
            total_losttime = 0
            for lines in grouped_lines:
                total_volume += lines.volume
                total_ritase += lines.ritase
                total_wh_shift += self.calc_worked_hours_shift(lines.shift_line_id)
                total_losttime += self.calc_losttime_hourly(lines)
                # Losttime
                hourly_id = lines.hourly_id
                if hourly_id.unit_equip_id == self.unit_equip_id:
                    temp_losttime = []
                    total_losttime_engine_off = 0
                    for lost in hourly_id.line_lost_ids:
                        if not any(lost.id != lost_id.hourly_lost_id.id for lost_id in self.line_lost_ids):
                            temp_losttime.append((0, 0, {
                                'hourly_lost_id': lost.id,
                                'start': lost.start,
                                'end': lost.end,
                                'losttime_id': lost.losttime_id.id,
                                'is_remarks': lost.is_remarks,
                                'rca_id': lost.rca_id.id,
                            }))
                            if lost.losttime_id.engine == False:
                                print(">>>END:", lost.end)
                                print(">>>START:", lost.start)
                                total_losttime_engine_off += lost.end - lost.start
                total_losttime_engine_off += total_losttime
            temp_detail_operations.append((0, 0, {
                'material_id': material_id,
                'shift_line_id': self.shift_line_id.id,
                'ritase': (total_ritase / len(lines)),
                'volume': total_volume,
                # 'working_hour': (total_wh_shift / len(grouped_lines)) - (total_losttime / len(grouped_lines)),
            }))
        return temp_detail_operations, temp_losttime, total_losttime_engine_off

    @api.depends('shift_line_id', 'date')
    def _get_calc_wh(self):
        for shift_prod in self:
            total = 0.0
            if shift_prod.shift_line_id:
                if shift_prod.shift_line_id.start > shift_prod.shift_line_id.end:
                    start_time = get_times_float(shift_prod.shift_line_id.start, shift_prod.date)
                    end_time = get_times_float(shift_prod.shift_line_id.end, shift_prod.date, next_days=True)
                else:
                    start_time = get_times_float(shift_prod.shift_line_id.start, shift_prod.date)
                    end_time = get_times_float(shift_prod.shift_line_id.end, shift_prod.date)
                res_total = (end_time - start_time).total_seconds() / 3600
                total = res_total
                print(total)
            shift_prod.wh_total = total

    @api.onchange('hm_akhir', 'hm_awal')
    def calc_hm_total(self):
        if self.hm_akhir and self.hm_awal:
            calc_total = self.hm_akhir - self.hm_awal
            self.hm_total = calc_total if calc_total >= 0 else 0

    @api.onchange('unit_equip_id', 'unit_equip_id.interface_id', 'shift_line_id', 'hm_total')
    def change_interface(self):
        if self.shift_line_id.shift_mode_id != self.shift_id:
            self.shift_line_id = False
        # Detail Operations
        hourly_line_ids = self.env['fleet.hourly.line'].search([('dumptruck_id', '=', self.unit_equip_id.id), ('shift_line_id', '=', self.shift_line_id.id), ('date', '=', self.date)])
        # Losttime checked
        hourly_id = self.env['fleet.hourly.prod'].search([('unit_equip_id', '=', self.unit_equip_id.id), ('shift_line_id', '=', self.shift_line_id.id), ('date', '=', self.date)], limit=1)
        temp_detail_operations = []
        temp_losttime = []
        total_losttime_engine_off = 0
        # Set Null
        self.line_ids = False
        self.line_lost_ids = False
        # Get Datas
        if hourly_line_ids:
            # Check Grouping
            temp_detail_operations, temp_losttime, total_losttime_engine_off = self._get_operation(hourly_line_ids)
            self.operator_id = False
        # Losttime
        if hourly_id:
            temp_losttime = []
            # Operations
            temp_detail_operations, temp_losttime, total_losttime_engine_off = self._get_operation(hourly_id.line_ids)
            self.operator_id = hourly_id.operator_id
        total_wh = self._get_calc_wh()
        # print(self.calc_detail_operation(temp_detail_operations, self.wh_total, total_losttime_engine_off, self.hm_total))
        self.line_ids = self.calc_detail_operation(temp_detail_operations, self.wh_total, total_losttime_engine_off, self.hm_total)
        self.line_lost_ids = temp_losttime
        self.lost_total = total_losttime_engine_off
        # Interface Units
        if self.unit_equip_id.interface_id:
            if self.unit_equip_id.interface_id.name == 'DT':
                self.is_dt = True
                self.is_ex = False
                self.is_ot = False
            if self.unit_equip_id.interface_id.name == 'EX':
                self.is_dt = False
                self.is_ex = True
                self.is_ot = False
            if self.unit_equip_id.interface_id.name == 'OT':
                self.is_dt = False
                self.is_ex = False
                self.is_ot = True

    def calc_detail_operation(self, datas, total_wh, total_lost, hm_total):
        total_volume = sum(item[2]['volume'] for item in datas)
        for data in datas:
            if total_volume:
                data[2]['hm'] = data[2]['volume'] / total_volume * hm_total
                data[2]['working_hour'] = data[2]['volume'] / total_volume * (total_wh - total_lost)
        return datas

    @api.depends('date', 'unit_equip_id', 'operator_id')
    def _compute_name(self):
        for hourly in self:
            name = f"[{hourly.date}] [{hourly.operator_id.name}] {hourly.unit_equip_id.fuel_unit_id.kode_unit}"
            hourly.name = name

    def action_close(self):
        self.write({
            'state': 'close',
        })
        if any(breakdown_id.state == 'draft' for breakdown_id in self.breakdown_ids):
            default = {
                'date': fields.Date.today(),
                'unit_equip_id': self.unit_equip_id.id,
                'operator_id': self.operator_id.id,
            }
            res_id = self.copy(default)
            for breakdown_id in self.breakdown_ids.filtered(lambda x: x.state == 'draft'):
                breakdown_id.copy({'shiftly_id': res_id.id})
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
            'default_hourly_id': self.id
        }
        # Search BD
        unit_ids = self.unit_equip_id.ids
        # for line in self.line_ids:
        #     unit_ids.append(line.dumptruck_id.id)
        # unit_ids.append(self.unit_equip_id.id)
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
        res = super(ShiftProductivity, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('shift.production')
        sequence_code = res.combination_sequence(seq)
        res.update({"code_seq": sequence_code})
        return res


class ShiftlyLine(models.Model):
    _name = "fleet.shiftly.line"
    _description = "Shiftly Production Line"

    shiftly_id = fields.Many2one('fleet.shiftly.prod', string='Shift Production', store=True)
    hourly_line_id = fields.Many2one('fleet.hourly.line', string='Hourly Line', store=True)
    shift_line_id = fields.Many2one('master.shiftmode.line', string='Shift')
    from_location_id = fields.Many2one('fleet.master.location', string='From', store=True)
    to_location_id = fields.Many2one('fleet.master.location', string='To', store=True)
    material_id = fields.Many2one('fleet.material', string='Material', store=True)
    activity_id = fields.Many2one('fleet.activity', string='Activity', store=True)
    process_id = fields.Many2one('fleet.process', string='Process', store=True)
    unit_loader_id = fields.Many2one('fleet.equipment.unit', string='Loader', store=True)
    ritase = fields.Integer('Ritase', store=True)
    is_volume = fields.Boolean('Manual Volume', store=True)
    volume = fields.Float('Volume', store=True)
    distance = fields.Float('Distance', store=True)
    hm = fields.Float('HM', store=True)
    working_hour = fields.Float('WH', store=True)

    @api.constrains('from_location_id', 'material_id', 'activity_id', 'process_id')
    def _check_values(self):
        for line in self:
            if not line.from_location_id:
                raise ValidationError(_("Please Input From Location"))
            if not line.material_id:
                raise ValidationError(_("Please Input Material"))
            if not line.activity_id:
                raise ValidationError(_("Please Input Activity"))
            if not line.process_id:
                raise ValidationError(_("Please Input Process"))


class ShiftlyLosttime(models.Model):
    _name = "fleet.shiftly.lost"
    _description = "Shiftly LostTime"

    shiftly_id = fields.Many2one('fleet.shiftly.prod', string='Shift Production', store=True)
    hourly_lost_id = fields.Many2one('fleet.hourly.lost', string='Hourly Losttime', store=True)
    start = fields.Float('Start', store=True, required=True)
    end = fields.Float('End', store=True, required=True)
    losttime_id = fields.Many2one('fleet.losttime', string='Losttime', store=True, required=True)
    is_remarks = fields.Boolean('Is Remarks', related='losttime_id.is_remarks')
    rca_id = fields.Many2one('fleet.losttime.line', string='RCA', store=True)
