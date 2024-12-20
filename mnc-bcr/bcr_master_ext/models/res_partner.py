from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    kontraktor_activity_ids = fields.Many2many(
        'master.activity', 'activity_kontraktor_rel', 'kontraktor_id', 'activity_id',
        string='Activities', store=True, copy=False)
    shift_mode_id = fields.Many2one('master.shiftmode', string='Shift Mode')

    def name_get(self):
        res = []
        for rec in self:
            if rec.is_kontraktor:
                res.append((rec.id, "%s" % (rec.name)))
            else:
                res.append((rec.id, "%s" % (rec.name)))
        return res
