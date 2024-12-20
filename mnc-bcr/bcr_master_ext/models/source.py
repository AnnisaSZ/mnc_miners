from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class MasterSource(models.Model):
    _inherit = 'master.source'

    bu_company_ids = fields.Many2many('res.company', 'bu_source_rel', 'source_id', 'bu_id', string='IUP Location', store=True)
    is_barge = fields.Boolean('Is Barge', compute='_get_barge')

    @api.depends('source_group_id')
    def _get_barge(self):
        for source in self:
            if source.source_group_id.name == 'BARGE':
                source.is_barge = True
            else:
                source.is_barge = False
