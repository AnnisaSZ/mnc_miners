# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class PerdinSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    duration_before_travel = fields.Integer(
        string='Duration Before Travel'
    )

    @api.model
    def get_values(self):
        res = super(PerdinSetting, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(duration_before_travel=params.get_param('duration_before_travel'))
        return res

    def set_values(self):
        super(PerdinSetting, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('duration_before_travel', self.duration_before_travel)
