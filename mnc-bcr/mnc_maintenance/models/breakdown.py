from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class FleetBreakdown(models.Model):
    _inherit = "fleet.breakdown"

    repair_id = fields.Many2one('repair.maintenance', string="Repair", store=True)
    date_rfu = fields.Datetime(
        string='Date RFU', store=True
    )

    def get_warehouse_datas(self, company):
        bisnis_unit_id = self.env['master.bisnis.unit'].search([('bu_company_id', '=', company.id)], limit=1)
        warehouse_id = self.env['stock.warehouse'].search([
            ('is_sparepart', '=', True),
            ('bisnis_unit_id', '=', bisnis_unit_id.id),
        ])
        if warehouse_id:
            picking_type_out = warehouse_id.out_type_id
            data = {
                'warehouse_id': warehouse_id.id,
                'picking_type_id': picking_type_out.id,
                'location_src_id': picking_type_out.default_location_src_id.id,
                'location_dest_id': picking_type_out.default_location_dest_id.id,
            }
            return data
        else:
            raise ValidationError(_("Please create warehouse datas in your company"))

    def _preapre_datas(self):
        context = self._context
        repair_type = context.get('repair_type')
        warehouse_data = self.get_warehouse_datas(self.unit_equip_id.company_id)
        data = {
            'no_repair': '/',
            'date': fields.Date.today(),
            'scheduled_date': fields.Datetime.now(),
            'breakdown_id': self.id,
            'unit_equip_id': self.unit_equip_id.id,
            'wh_company_id': self.unit_equip_id.company_id.id,
            'warehouse_id': warehouse_data['warehouse_id'],
            'picking_type_id': warehouse_data['picking_type_id'],
            'location_id': warehouse_data['location_src_id'],
            'location_dest_id': warehouse_data['location_dest_id'],
            'state': 'request',
            'notes': self.remarks,
        }
        if repair_type:
            if repair_type == 'internal':
                data['is_internal'] = True
            elif repair_type == 'external':
                data['is_external'] = True
        return data

    def action_request_repair(self):
        context = self._context
        repair_type = context.get('repair_type')
        # Create Datas
        repair_obj = self.env['repair.maintenance']
        repair_id = repair_obj.create(self._preapre_datas())
        if repair_type == 'internal':
            picking = repair_id.create_picking()
            repair_id.write({'picking_id': picking.id})
        self.write({'repair_id': repair_id.id})
        return repair_id

    def action_open_request(self):
        return {
            'name': _("Request Repair"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'request.repair.wizard',
            'view_id': self.env.ref('mnc_maintenance.request_repair_wizard_form').id,
            'context': {
                'default_breakdown_id': self.id,
                'default_repair_type': 'internal',
            },
        }

    def action_open_repair(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.repair_id.id,
            'res_model': 'repair.maintenance',
            'view_id': self.env.ref('mnc_maintenance.repair_maintenance_form').id
        }
