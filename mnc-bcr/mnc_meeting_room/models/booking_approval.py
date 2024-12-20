from odoo import models, fields


class MnceiMeetingApproval(models.Model):
    _name = 'mncei.meeting.approval'
    _description = 'MNCEI Meeting Approval'
    _order = 'id asc'
    _rec_name = 'booking_id'

    booking_id = fields.Many2one('mncei.booking.meeting', string='Booked', ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', store=True)
    email = fields.Char(string='Email', related='user_id.login', store=True)
    approve_date = fields.Datetime('Timestamp')
    is_email_sent = fields.Boolean('Email Sent')
