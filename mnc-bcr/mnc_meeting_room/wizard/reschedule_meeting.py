# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError
from odoo import http


class RoomScheduleWizard(models.TransientModel):
    """MNC Document Approval Wizard."""
    _name = "reschedule.room.meeting"
    _description = "Mncei Reschedule Meeting Room"

    booking_id = fields.Many2one('mncei.booking.meeting',string='Booking')
    start_date = fields.Date('Start Date', store=True, required=True, default=fields.Date.today())
    end_date = fields.Date('End Date', store=True, required=True, default=fields.Date.today())
    hours_start = fields.Float('Hours Meeting Start', store=True, required=True, size=2, default=8)
    hours_end = fields.Float('Hours Meeting End', store=True, required=True, size=2, default=17)

    def action_reschedule(self):
        self._check_date_meeting(self.booking_id)
        self.booking_id.action_cancel()
        new_booking_id = self.booking_id.copy({
            'start_date': self.start_date,
            'end_date': self.end_date,
            'hours_start': self.hours_start,
            'hours_end': self.hours_end,
            'remarks': self.booking_id.remarks,
            'type_id': self.booking_id.type_id.id,
            'department_id': self.booking_id.department_id.id,
            'participant_ids': [(6, 0, self.booking_id.participant_ids.ids)],
            'name': self.booking_id.name + ' (Reschedule)',
        })
        print(new_booking_id)
        new_booking_id.action_submit()
        if new_booking_id:
            return {
                'name': _("New Booked"),
                'type': 'ir.actions.act_window',
                'res_id': new_booking_id.id,
                'target': 'current',
                'view_mode': 'form',
                'res_model': 'mncei.booking.meeting',
                'view_id': self.env.ref('mnc_meeting_room.meeting_view_form').id,
            }
        else:
            return

    def _check_date_meeting(self, meeting_id):
        booking_ids = self.env['mncei.booking.meeting'].search([('start_date', '>=', self.start_date), ('end_date', '<=', self.end_date), ('id', '!=', meeting_id.id), ('state', '!=', 'cancel')])
        if self.hours_start > 23 or self.hours_end > 23:
            raise ValidationError(_("Tolong cek kembali jam yang anda input"))
        if self.hours_start > self.hours_end:
            raise ValidationError(_("Tolong cek kembali jam yang anda input"))
        for booking_id in booking_ids:
            if booking_id:
                if self.hours_start >= booking_id.hours_start and self.hours_start <= booking_id.hours_end:
                    for room in meeting_id.room_ids:
                        if room.id in booking_id.room_ids.ids:
                            print("XXXXXXXXXXXXXXXXXXXXXx")
                            print(room.id)
                            print(booking_id)
                            raise ValidationError(_("Ruang %s sudah ada jadwal Booking oleh %s") % (room.name, booking_id.department_id.name))
        return
