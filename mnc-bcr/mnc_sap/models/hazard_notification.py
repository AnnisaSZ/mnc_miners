from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class HazardNotification(models.Model):
    _name = 'hazard.notification'
    _description = 'Hazard Notification'
    _rec_name = 'code'
    _order = 'code'

    code = fields.Char('Code', store=True, required=True)
    notification_text = fields.Text('Notification Text', store=True, required=True)
    state = fields.Boolean('Active', store=True, default=True)
    to_user = fields.Selection([
        ('pelapor', 'Pelapor'),
        ('pic', 'PIC'),
        ('hse', 'HSE')
    ], string='To User', store=True)

    def get_by_code(self, code):
        res_id = self.env['hazard.notification'].search([('code', '=', code), ('state', '=', True)], limit=1) or False
        return res_id
