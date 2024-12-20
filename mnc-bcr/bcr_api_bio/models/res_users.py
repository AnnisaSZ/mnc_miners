from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_bio = fields.Boolean('Login Bio', store=True)
    bio_token = fields.Char('Bio Token', store=True)
