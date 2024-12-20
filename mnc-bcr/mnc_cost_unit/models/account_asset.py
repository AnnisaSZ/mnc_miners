from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    unit_id = fields.Many2one('master.fuel.unit', 'Unit', store=True)
