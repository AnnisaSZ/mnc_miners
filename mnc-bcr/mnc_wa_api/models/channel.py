from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

import logging

TIMEOUT = 20

_logger = logging.getLogger(__name__)


class QontakChannel(models.Model):
    _name = "qontak.channel"

    auth_id = fields.Many2one('qontak.auth', string="Auth")
    qontak_id = fields.Char('ID')
    target_channel = fields.Char('Target Channel')
    account_name = fields.Char('Account Name')
    account_number = fields.Char('Phone Number')
    is_active = fields.Boolean('Active')
