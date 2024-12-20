from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class PushNotification(models.Model):
    _inherit = "push.notification"

    res_id = fields.Integer('Res ID', store=True)
