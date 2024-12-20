from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
from itertools import groupby
from odoo.addons.resource.models.resource import Intervals

import math


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    # ============ Replace Field ============
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=False)
    # ========================================
    company_ids = fields.Many2many('res.company', string='Companies', store=True)
    is_shift = fields.Boolean('Shift', store=True)
    is_roster = fields.Boolean('Roster', store=True)
    loc_working_id = fields.Many2one(
        'mncei.lokasi.kerja', 'Working Location', store=True)
    roster_id = fields.Many2one(
        'res.roster', 'Roster', store=True)
    ttype_shift = fields.Selection([
        ('full_days', 'Full Days'),
        ('day_night', 'Day and Night'),
    ], default='day_night', string='Type Shift', store=True)

    total_days = fields.Integer('Total Days', store=True)
    start_hours = fields.Float("Start Time")
    end_hours = fields.Float("End Time")
    limit_attendance = fields.Float("Limit Absent")

    mncei_employee_id = fields.One2many('mncei.employee', 'working_time_id', string='Employee', store=True)
    total_mncei_employee = fields.Integer('Total Employee', compute='_cacl_total_employee', store=True,)

    # Detail Shift
    shift_temp_ids = fields.One2many('employee.shift.temp', 'working_time_id', string='Shift Detail')
    attendance_group_ids = fields.One2many('resource.calendar.group', 'resouce_id', string='Attendance Group', compute='_compute_wt_group', store=True)

    def prepare_data_group(self, line_id):
        datas = {
            'day_period_id': line_id.day_period_id.id,
            'start_ci': line_id.start_ci,
            'hour_from': line_id.hour_from,
            'start_co': line_id.start_co,
            'hour_to': line_id.hour_to,
            'start_overtime': line_id.start_overtime,
        }
        return datas

    @api.depends('attendance_ids')
    def _compute_wt_group(self):
        for working_time in self:
            list_of_dicts = []
            wt_ids = []
            working_time.attendance_group_ids = False
            for day_period_id, grouped_lines in groupby(working_time.attendance_ids, key=lambda x: x.day_period_id.id):
                grouped_lines = list(grouped_lines)
                for line in grouped_lines:
                    if not list_of_dicts:
                        list_of_dicts.append(self.prepare_data_group(line))
                    else:
                        is_matching = any(d.get('hour_from') == line.hour_from for d in list_of_dicts)
                        if not is_matching:
                            list_of_dicts.append(self.prepare_data_group(line))
            for my_data in list_of_dicts:
                wt_id = self.env['resource.calendar.group'].create(my_data)
                wt_ids.append(wt_id.id)
            working_time.attendance_group_ids = [(6, 0, wt_ids)]

    @api.depends('mncei_employee_id')
    def _cacl_total_employee(self):
        for resource in self:
            total = 0
            if resource.mncei_employee_id:
                total = len(resource.mncei_employee_id.ids)
            resource.total_mncei_employee = total

    def action_apply(self):
        return {
            'name': _("Apply To Employee"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'resource.calendar.wizard',
            'view_id': self.env.ref('mnc_attendance.resource_wizard_form').id,
            'context': {
                'default_company_ids': [(6, 0, self.company_ids.ids)],
                'default_resource_id': self.id,
                'default_loc_working_id': self.loc_working_id.id,
                'default_is_shift': self.is_shift,
                'working_location': self.loc_working_id.id,
                'companies': self.company_ids.ids,
            },
        }

    def action_view_employee(self, pc_ids=False):
        employee_ids = self.mncei_employee_id
        result = self.env['ir.actions.act_window']._for_xml_id('mnc_hr.mncei_emp_actions')
        # choose the view_mode accordingly
        if len(employee_ids) > 1:
            result['domain'] = [('id', 'in', employee_ids.ids)]
            result['context'] = {'create': 0, 'delete': 0, 'edit': 0}
        elif len(employee_ids) == 1:
            res = self.env.ref('mnc_hr.mncei_emp_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = employee_ids.id
            result['context'] = {'create': 0, 'delete': 0, 'edit': 0}
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    def action_open_shift(self):
        return {
            'name': _("List Shift"),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'employee.shift.temp',
            'domain': [('id', 'in', self.shift_temp_ids.ids)],
            'views': [[self.env.ref('mnc_attendance.employee_shift_tree').id, 'list']],
            'context': {'create': 0, 'delete': 0}
        }

    def action_reset_employee(self):
        for employee_id in self.mncei_employee_id:
            employee_id.write({
                'working_time_id': False,
            })

    # Override
    def _check_overlap(self, attendance_ids):
        """ attendance_ids correspond to attendance of a week,
            will check for each day of week that there are no superimpose. """
        result = []
        for attendance in attendance_ids.filtered(lambda att: not att.date_from and not att.date_to):
            # 0.000001 is added to each start hour to avoid to detect two contiguous intervals as superimposing.
            # Indeed Intervals function will join 2 intervals with the start and stop hour corresponding.
            result.append((int(attendance.dayofweek) * 24 + attendance.hour_from + 0.000001, int(attendance.dayofweek) * 24 + attendance.hour_to, attendance))

        # Add Condition if shifting @Andi
        if len(Intervals(result)) != len(result) and not self.is_shift:
            # continue
            raise ValidationError(_("Attendances can't overlap."))

    def _compute_hours_per_day(self, attendances):
        if not attendances:
            return 0

        hour_count = 0.0
        for attendance in attendances:
            hour_count += attendance.hour_to - attendance.hour_from

        if not self.is_shift:
            if self.two_weeks_calendar:
                number_of_days = len(set(attendances.filtered(lambda cal: cal.week_type == '1').mapped('dayofweek')))
                number_of_days += len(set(attendances.filtered(lambda cal: cal.week_type == '0').mapped('dayofweek')))
            else:
                number_of_days = len(set(attendances.mapped('dayofweek')))
        else:
            number_of_days = len(set(attendances.mapped('dayofweek')))

        return float_round(hour_count / float(number_of_days), precision_digits=2)


class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    name = fields.Char(required=False, compute='_get_name')
    is_shift = fields.Boolean('Is Shift', related='calendar_id.is_shift', store=True)
    day_period = fields.Selection([('morning', 'Morning'), ('afternoon', 'Afternoon'), ('night', 'Night')], required=False, default='morning')
    day_period_id = fields.Many2one(
        'res.day.period', 'Day Period', store=True)
    start_overtime = fields.Float("Start Overtime", store=True)
    start_ci = fields.Float('Start CI', required=True, store=True)
    start_co = fields.Float('Start CO', required=False, store=True)

    @api.depends('day_period_id', 'hour_from', 'hour_to')
    def _get_name(self):
        for line in self:
            start = ':'.join(line.convert_time(line.hour_from))
            end = ':'.join(line.convert_time(line.hour_to))
            name = "%s (%s-%s)" % (line.day_period_id.name, start, end)
            line.name = name

    def convert_time(self, time):
        factor = time < 0 and -1 or 1
        val = abs(time)
        # Hours
        hours = factor * int(math.floor(val))
        if hours > 0 and hours < 10:
            hours_char = '0' + str(hours)
        elif hours == 0:
            hours_char = '00'
        else:
            hours_char = str(factor * int(math.floor(val)))
        # Minutes
        minutes = int(round((val % 1) * 60))
        if minutes > 0 and minutes < 10:
            minutes_char = '0' + str(minutes)
        elif minutes == 0:
            minutes_char = '00'
        else:
            minutes_char = str(int(round((val % 1) * 60)))
        # Return Result
        return (hours_char, minutes_char)

    # Override
    @api.onchange('hour_from', 'hour_to', 'is_shift')
    def _onchange_hours(self):
        if not self.is_shift:
            # avoid negative or after midnight
            self.hour_from = min(self.hour_from, 23.99)
            self.hour_from = max(self.hour_from, 0.0)
            self.hour_to = min(self.hour_to, 23.99)
            self.hour_to = max(self.hour_to, 0.0)

            # avoid wrong order
            self.hour_to = max(self.hour_to, self.hour_from)


class ResourceCalendarGroup(models.Model):
    _name = "resource.calendar.group"
    _description = "Resouce Group"
    _rec_name = 'name'

    name = fields.Char(required=False, compute='_get_name')
    resouce_id = fields.Many2one(
        'resource.calendar', 'Working Time', store=True)
    day_period_id = fields.Many2one(
        'res.day.period', 'Day Period', store=True)
    start_overtime = fields.Float("Start Overtime", store=True)
    hour_from = fields.Float("Check In", store=True)
    hour_to = fields.Float("Check Out", store=True)
    start_ci = fields.Float('Start CI', required=True, store=True)
    start_co = fields.Float('Start CO', required=False, store=True)

    def convert_time(self, time):
        factor = time < 0 and -1 or 1
        val = abs(time)
        # Hours
        hours = factor * int(math.floor(val))
        if hours > 0 and hours < 10:
            hours_char = '0' + str(hours)
        elif hours == 0:
            hours_char = '00'
        else:
            hours_char = str(factor * int(math.floor(val)))
        # Minutes
        minutes = int(round((val % 1) * 60))
        if minutes > 0 and minutes < 10:
            minutes_char = '0' + str(minutes)
        elif minutes == 0:
            minutes_char = '00'
        else:
            minutes_char = str(int(round((val % 1) * 60)))
        # Return Result
        return (hours_char, minutes_char)

    @api.depends('day_period_id', 'hour_from', 'hour_to')
    def _get_name(self):
        for line in self:
            start = ':'.join(line.convert_time(line.hour_from))
            end = ':'.join(line.convert_time(line.hour_to))
            name = "%s (%s - %s)" % (line.day_period_id.name, start, end)
            line.name = name
