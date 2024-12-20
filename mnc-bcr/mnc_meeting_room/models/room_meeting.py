from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MnceiMeetingRoom(models.Model):
    _name = 'mncei.room.meeting'
    _description = 'MNCEI Room Meeting'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', store=True, required=True)
    capacity = fields.Integer('Capacity Room', store=True, default=1, required=True)
    floor = fields.Integer('Floor', store=True, default=21, required=True)
    floor_id = fields.Many2one('mncei.floor.meeting', string='Floor', store=True, required=True, ondelete='cascade', domain="[('status', '=', 'active')]")
    location = fields.Char('Location/Building', store=True, required=True)
    ga_uid = fields.Many2many('res.users', string='GA', store=True, required=True)
    secretay_uid = fields.Many2one('res.users', string='Secretary', store=True)
    facilty_ids = fields.One2many('mncei.facility.meeting', 'room_id', string='Facilty', required=True)
    is_merge = fields.Boolean('Room Combine', store=True)
    room_ids = fields.Many2many('mncei.room.meeting', 'room_combine_rel', 'room_id', 'combine_id', string="Room Meeting", store=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], default='active', store=True, required=True)

    def name_get(self):
        result = []
        for room in self:
            name = _("%s /Lt.%s") % (room.name, room.floor_id.name)
            result.append((room.id, name))
        return result

    @api.onchange('room_ids', 'room_ids.capacity')
    def calculate_capacity(self):
        if self.room_ids and self.is_merge:
            self.capacity = sum(line.capacity for line in self.room_ids) or 0

    def booking_meeting(self, domain):
        return self.env['mncei.booking.meeting'].search(domain)

    @api.onchange('ga_uid', 'secretay_uid')
    def change_approval(self):
        domain = [('room_id', '=', self._origin.id), ('state', '=', 'waiting')]
        if self.ga_uid:
            domain.append(('is_ga', '=', True))
            booking_ids = self.booking_meeting(domain)
            if booking_ids:
                for booking_id in booking_ids:
                    booking_id.approver_ids = [(6, 0, self.ga_uid.ids)]
        if self.secretay_uid:
            domain.append(('is_secretary', '=', True))
            booking_ids = self.booking_meeting(domain)
            if booking_ids:
                for booking_id in booking_ids:
                    booking_id.approver_ids = [(6, 0, self.secretay_uid.ids)]


class MnceiMeetingFacility(models.Model):
    _name = 'mncei.facility.meeting'
    _description = 'MNCEI Meeting Facilty'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', store=True, required=True)
    unit = fields.Integer('Units', default=1, store=True, required=True)
    room_id = fields.Many2one('mncei.room.meeting')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], default='active', store=True, required=True)


class MnceiMeetingFloor(models.Model):
    _name = 'mncei.floor.meeting'
    _description = 'MNCEI Meeting Floor'

    name = fields.Char('Name')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], default='active', store=True, required=True)
