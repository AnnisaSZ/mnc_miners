from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta
import pytz
import math

import logging

_logger = logging.getLogger(__name__)


class MnceiMeeting(models.Model):
    _name = 'mncei.booking.meeting'
    _description = 'MNCEI Meeting'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _company_ids_domain(self):
        print("SSSSSSSSSSSSSSSSS")
        print(fields.Date.today())
        _logger.info("XXXXXXXXXXXXXXXXXXX")
        _logger.info(fields.Date.today())
        return [('id', 'in', self.env.user.company_ids.ids)]

    name = fields.Char("Name", store=True, required=True, copy=False)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company, domain=_company_ids_domain, required=True
    )
    department_id = fields.Many2one('mncei.department', string='Department', store=True, required=True, copy=False)
    requestor_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Requestor', store=True, required=True, copy=False)
    participant_ids = fields.Many2many(
        'res.users', 'user_meeting_rel', 'user_id', 'meeting_id',
        string='Participants', store=True, copy=False
    )
    approver_ids = fields.Many2many(
        'res.users', 'user_meeting_approver_rel', 'user_approver_id', 'meeting_id',
        string='Approver', store=True
    )
    user_approval_ids = fields.One2many(
        'mncei.user.approve.meeting',
        'booking_id',
        string='User Approval', store=True
    )
    room_ids = fields.Many2many('mncei.room.meeting', string="Room Meeting", store=True)
    room_id = fields.Many2one('mncei.room.meeting', string="Room Meeting", store=True, required=True, domain="[('status', '=', 'active')]")
    capacity_room = fields.Integer('Capacity', compute='calculate_capacity')
    start_date = fields.Date('Start Date', store=True, default=fields.Date.today(), required=True)
    end_date = fields.Date('End Date', store=True, default=fields.Date.today(), required=True)
    hours_start = fields.Float('Hours Meeting Start', store=True, required=True, size=2, default=8, copy=False)
    hours_end = fields.Float('Hours Meeting End', store=True, required=True, size=2, default=17, copy=False)
    minutes_start = fields.Float('Minutes Meeting Start', store=True)
    minutes_end = fields.Float('Minutes Meeting End', store=True)
    meeting_type = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('hybrid', 'Online & Offline'),
    ], default='online', string='Type', store=True, required=True, copy=False)
    type_id = fields.Many2one('mncei.type.meeting', store=True, required=True, copy=False)
    remarks = fields.Text('Remarks', store=True, required=True, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approve'),
        ('approve', 'Approve'),
        ('cancel', 'Cancel'),
    ], default='draft', string='State', store=True, copy=False)

    start_time = fields.Datetime('Start', compute='_get_start_end_booking', store=True)
    end_time = fields.Datetime('End', compute='_get_start_end_booking', store=True)
    hours_start_act = fields.Integer('Hours Act Start', compute='_get_start_end_booking')
    minute_start_act = fields.Integer('Minute Act Start', compute='_get_start_end_booking')
    hours_end_act = fields.Integer('Hours Act End', compute='_get_start_end_booking')
    minute_end_act = fields.Integer('Hours Act End', compute='_get_start_end_booking')

    total_participant = fields.Integer('Total Participant', compute='calculate_participant')

    def _compute_is_approved(self):
        for booking in self:
            if self.env.uid in booking.approver_ids.ids:
                booking.is_approver = True
            else:
                booking.is_approver = False

    def _compute_is_requestor(self):
        for booking in self:
            if self.env.uid == booking.requestor_id.id:
                booking.is_request = True
            else:
                booking.is_request = False

    is_secretary = fields.Boolean('Secretary', copy=False)
    is_ga = fields.Boolean('GA', copy=False)
    is_approver = fields.Boolean(string="Is Approved", compute='_compute_is_approved', copy=False)
    is_request = fields.Boolean(string="Is Requestor", compute='_compute_is_requestor', copy=False)
    is_day = fields.Boolean(string="Full Day", compute='_get_start_end_booking', copy=False)

    @api.onchange('room_id')
    def change_room_meeting(self):
        if self.room_id:
            if self.room_id.is_merge:
                self.room_ids = self.room_id.room_ids
            else:
                self.room_ids = self.room_id

    def open_room_facility(self):
        return {
            'name': _("Facility"),
            'type': 'ir.actions.act_window',
            'res_id': self.room_id.id,
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'mncei.room.meeting',
            'view_id': self.env.ref('mnc_meeting_room.room_meeting_view_form').id,
            'flags': {'mode': 'readonly'},
            'context': {'edit': False, 'create': False}
        }

    # Method convert float to hours and minutes
    def float_time_convert(self, float_val):
        factor = float_val < 0 and -1 or 1
        val = abs(float_val)
        return (factor * int(math.floor(val)), int(round((val % 1) * 60)))

    def convert_hours(self, hours):
        hours = hours - 14
        if hours <= 0:
            hours = (hours + 24)
        if hours == 24:
            hours = 00
        return hours

    @api.depends('participant_ids')
    def calculate_participant(self):
        for booking in self:
            if booking.participant_ids:
                booking.total_participant = len(booking.participant_ids)
            else:
                booking.total_participant = 0

    @api.depends('room_ids')
    def calculate_capacity(self):
        for booking in self:
            if booking.room_ids:
                booking.capacity_room = sum(line.capacity for line in booking.room_ids) or 0
            else:
                booking.capacity_room = 0

    @api.depends('start_date', 'end_date', 'hours_start', 'hours_end', 'room_ids')
    def _get_start_end_booking(self):
        for booking in self:
            booking.start_time = False
            booking.end_time = False
            booking.is_day = False
            if booking.start_date != booking.end_date:
                booking.is_day = True
            # Generate to Datetime
            if booking.start_date and booking.hours_start:
                hours, minute = booking.float_time_convert(booking.hours_start)
                hours = booking.convert_hours(hours)
                # Setting Date to %Y-%m-%d %H:%M:%S
                join_date = str(booking.start_date) + ' ' + ':'.join((str(hours), str(minute), '00'))
                if hours > 10:
                    join_date = str(booking.start_date - timedelta(days=1)) + ' ' + ':'.join((str(hours), str(minute), '00'))
                start_time = datetime.strptime(join_date, "%Y-%m-%d %H:%M:%S")
                booking.start_time = start_time.astimezone(pytz.timezone(booking.requestor_id.tz)).strftime("%Y-%m-%d %H:%M:%S")
                booking.hours_start_act = booking.start_time.hour + 7
                booking.minute_start_act = minute
            if booking.end_date and booking.hours_end:
                hours_end, minute = booking.float_time_convert(booking.hours_end)
                hours_end = booking.convert_hours(hours_end)
                # Setting Date to %Y-%m-%d %H:%M:%S
                join_date = str(booking.end_date) + ' ' + ':'.join((str(hours_end), str(minute), '00'))
                if hours_end > 10:
                    join_date = str(booking.end_date - timedelta(days=1)) + ' ' + ':'.join((str(hours_end), str(minute), '00'))
                end_time = datetime.strptime(join_date, "%Y-%m-%d %H:%M:%S")
                booking.end_time = end_time.astimezone(pytz.timezone(booking.requestor_id.tz)).strftime("%Y-%m-%d %H:%M:%S")
                booking.hours_end_act = booking.end_time.hour + 7
                booking.minute_end_act = minute

    def action_submit(self):
        if self.state == 'draft':
            approver_list = []
            for room in self.room_id:
                if room.secretay_uid:
                    approver_list.append(room.secretay_uid.id)
                    if not self.is_secretary:
                        self.update({
                            'is_secretary': True
                        })
            if not approver_list:
                for room in self.room_id:
                    if room.ga_uid:
                        for ga_uid in room.ga_uid:
                            approver_list.append(ga_uid.id)
                        if not self.is_ga:
                            self.update({
                                'is_ga': True
                            })
            for approval in approver_list:
                approve_id = self.env['mncei.user.approve.meeting'].create(self.prepare_data_approval(approval))
                self.send_notification(approve_id)
            print("SSSSSSSSSSSSSSSSSSS")
            print(approver_list)
            self.update({
                'state': 'waiting',
                'approver_ids': [(6, 0, approver_list)],
            })
        return

    def action_cancel(self):
        self.update({
            'state': 'cancel'
        })
        return

    def action_approve(self):
        email_to_it = self.env.ref('mnc_meeting_room.notification_booking_zoom')
        if self.approver_ids:
            if self.is_ga:
                self.update({
                    'state': 'approve'
                })
                if self.type_id.is_online:
                    email_to_it.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': 'it.mncenergy@mncgroup.com'})
                for participant in self.participant_ids:
                    self.send_email_invitation(participant)
            else:
                approver_list = []
                for room in self.room_id:
                    approver_list.append(room.ga_uid.id)
                self.update({
                    'approver_ids': [(6, 0, approver_list)],
                    'is_ga': True
                })
        return

    def prepare_data_approval(self, user_id):
        return {
            'user_id': user_id,
            'booking_id': self.id
        }

    def send_email_invitation(self, user_id):
        template = self.env.ref('mnc_meeting_room.notification_invitation_meeting').with_context(dbname=self._cr.dbname, invited_users=user_id)
        template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user_id.login})
        return

    def send_notification(self, approver_id):
        template = self.env.ref('mnc_meeting_room.notification_booking_meeting_room_mail_template_approved')
        template.send_mail(approver_id.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': approver_id.user_id.login})
        return

    @api.constrains('start_date', 'end_date')
    def _check_date_booking(self):
        for booking in self:
            if booking.start_date < fields.Date.today():
                raise ValidationError(_("Start Date must be greater than Today"))
            if booking.end_date < booking.start_date:
                raise ValidationError(_("End Date must be greater than Start Date"))

    @api.constrains('start_date', 'end_date', 'hours_start', 'hours_end', 'room_ids')
    def _check_booking_room(self):
        for booking in self:
            booking._check_date_booking()
            if booking.hours_start > 23 or booking.hours_end > 23:
                raise ValidationError(_("Tolong cek kembali jam yang anda input"))
            if booking.hours_start > booking.hours_end:
                raise ValidationError(_("Tolong cek kembali jam yang anda input"))
            booking.check_date_booking_meeting(booking)

    def check_date_booking_meeting(self, booking):
        booking_ids = self.search_booking(booking)
        for booking_id in booking_ids:
            if booking_id:
                if not booking_id.is_day:
                    booking.check_duration_meeting(booking, booking_id)
                else:
                    # Cek dengan tgl yang sama
                    if booking.start_date == booking_id.start_date:
                        print("XXXXXXXXXXXXXXXXXXXX")
                        booking.check_duration_meeting(booking, booking_id)
                        # if booking.hours_start <= booking_id.hours_start:
                        #     if booking.hours_end > booking_id.hours_start:
                        #         for room in booking.room_ids:
                        #             if room.id in booking_id.room_ids.ids:
                        #                 raise ValidationError(_("Ruang %s sudah ada jadwal Booking oleh %s") % (room.name, booking_id.department_id.name))
                        #         # 13                     8
                        # if booking.hours_start >= booking_id.hours_start:
                        # if booking.hours_start <= booking_id.hours_start:
                        #     print("ZZZZZZZZZZZ01")
                        #     print(booking.hours_start)
                        #     print(booking_id.hours_start)
                        #     for room in booking.room_ids:
                        #         if room.id in booking_id.room_ids.ids:
                        #             raise ValidationError(_("Ruang %s sudah ada jadwal Booking oleh %s") % (room.name, booking_id.department_id.name))
                    # Cek dengan tgl beririsan
                    elif booking.end_date == booking_id.end_date or booking.end_date == booking_id.start_date or booking.start_date == booking_id.end_date:
                        booking.check_duration_meeting(booking, booking_id)
                    elif booking.end_date <= booking_id.end_date and booking.start_date >= booking_id.start_date:
                        booking.check_duration_meeting(booking, booking_id)

    def search_booking(self, booking):
        booking_ids = []
        duration_ids = self.search([('id', '!=', booking.id), ('state', '!=', 'cancel'), ('start_date', '<=', booking.start_date), ('end_date', '>=', booking.end_date)])
        start_ids = self.search([('id', '!=', booking.id), ('state', '!=', 'cancel'), ('start_date', '>=', booking.start_date), ('start_date', '<=', booking.end_date)])
        end_ids = self.search([('id', '!=', booking.id), ('state', '!=', 'cancel'), ('end_date', '>=', booking.start_date), ('end_date', '<=', booking.end_date)])
        if duration_ids:
            for duration_id in duration_ids:
                if duration_id not in booking_ids:
                    booking_ids.append(duration_id)
        if start_ids:
            for start_id in start_ids:
                if start_id not in booking_ids:
                    booking_ids.append(start_id)
        if end_ids:
            for end_id in end_ids:
                if end_id not in booking_ids:
                    booking_ids.append(end_id)
        return booking_ids

    def check_duration_meeting(self, res_id, meeting_id):
        if res_id.hours_start <= meeting_id.hours_start:
            if res_id.hours_end > meeting_id.hours_start:
                for room in res_id.room_ids:
                    if room.id in meeting_id.room_ids.ids:
                        raise ValidationError(_("Ruang %s sudah ada jadwal Booking oleh %s") % (room.name, meeting_id.department_id.name))
        if res_id.hours_start >= meeting_id.hours_start:
            if meeting_id.hours_end > res_id.hours_start:
                for room in res_id.room_ids:
                    if room.id in meeting_id.room_ids.ids:
                        raise ValidationError(_("Ruang %s sudah ada jadwal Booking oleh %s") % (room.name, meeting_id.department_id.name))

    def action_reschedule(self):
        return {
            'name': _("Reschedule"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'reschedule.room.meeting',
            'view_id': self.env.ref('mnc_meeting_room.mncei_reschedule_form').id,
            'context': {
                'default_hours_start': self.hours_start,
                'default_hours_end': self.hours_end,
                'default_start_date': self.start_date,
                'default_end_date': self.end_date,
                'default_booking_id': self.id
            }
        }


class MnceiTypeMeeting(models.Model):
    _name = 'mncei.type.meeting'
    _description = 'MNCEI Meeting Type'

    active = fields.Boolean('Active', default=True, store=True)
    name = fields.Char('Name')
    is_online = fields.Boolean('Is Online', store=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], default='active', store=True, required=True)


class MnceiUserApproveMeeting(models.Model):
    _name = 'mncei.user.approve.meeting'
    _description = 'MNCEI Meeting Approval'
    _order = 'id asc'
    _rec_name = 'booking_id'

    user_id = fields.Many2one(
        'res.users',
        string='Users',
    )
    booking_id = fields.Many2one(
        'mncei.booking.meeting',
        string='Booking', store=True
    )
    email = fields.Char('Email', related='user_id.login')
    is_email_sent = fields.Boolean('Email Sent', store=True)
