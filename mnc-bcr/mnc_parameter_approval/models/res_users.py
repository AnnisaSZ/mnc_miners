from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    jabatan_id = fields.Many2one(
        'mncei.jabatan',
        string='Jabatan', related='mncei_employee_id.jabatan', store=True
    )
