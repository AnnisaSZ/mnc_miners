from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime, date

import logging

_logger = logging.getLogger(__name__)


class ValidationModels(models.Model):
    _inherit = 'validation.validation'

    planning_type = fields.Selection([
        ('yearly', 'Yearly'),
        ('monthly', 'Monthly'),
    ], string='Planning Type', store=True)
    is_planning_period = fields.Boolean('Planning Period', store=True, compute='_get_planning_period')

    @api.depends('model_id')
    def _get_planning_period(self):
        for validation in self:
            if validation.model_id.model == 'planning.opr':
                validation.is_planning_period = True
            else:
                validation.is_planning_period = False
