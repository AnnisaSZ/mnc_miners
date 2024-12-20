# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class TicketSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    duration_to_solve = fields.Integer(
        string='Duration To Solve'
    )
    duration_remainder = fields.Integer(
        string='Duration Auto Reminder'
    )

    @api.model
    def get_values(self):
        res = super(TicketSetting, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(duration_to_solve=params.get_param('duration_to_solve'))
        res.update(duration_remainder=params.get_param('duration_remainder'))
        return res

    def set_values(self):
        super(TicketSetting, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('duration_to_solve', self.duration_to_solve)
        params.set_param('duration_remainder', self.duration_remainder)
