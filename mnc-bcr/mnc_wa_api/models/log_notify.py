from odoo import models, fields, api, _

import logging

TIMEOUT = 20

_logger = logging.getLogger(__name__)


class QontakChannel(models.Model):
    _name = "qontak.log"