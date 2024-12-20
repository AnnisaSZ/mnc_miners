# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from datetime import datetime, timedelta


class RequestRepairWizard(models.TransientModel):
    _name = "request.repair.wizard"
    _description = "Request Repair Wizard"

    breakdown_id = fields.Many2one('fleet.breakdown', 'Breakdown Number')
    repair_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
    ], string='Type Repair', store=True)

    def do_request(self):
        if self.breakdown_id:
            repair_id = self.breakdown_id.with_context(repair_type=self.repair_type).action_request_repair()
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': repair_id.id,
                'res_model': 'repair.maintenance',
                'view_id': self.env.ref('mnc_maintenance.repair_maintenance_form').id
            }
