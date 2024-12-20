from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    department_id = fields.Many2one(
        'mncei.department',
        string='Department',
    )
