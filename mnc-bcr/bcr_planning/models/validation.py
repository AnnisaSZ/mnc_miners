from odoo import api, fields, models, _

class ValidationPlan(models.Model):
    _inherit = 'validation.plan'

    validation_planning_hauling_id = fields.Many2one('planning.hauling', string='Planning Hauling')
    validation_planning_production_id = fields.Many2one('planning.production', string='Planning Production')
    validation_planning_barging_id = fields.Many2one('planning.barging', string='Planning Barging')
    validation_act_hauling_id = fields.Many2one('act.hauling', string='Hauling')
    validation_act_production_id = fields.Many2one('act.production', string='Production')
    validation_act_barging_id = fields.Many2one('act.barging', string='Barging')
    validation_act_delay_id = fields.Many2one('act.delay', string='Delay')
    validation_act_stockroom_id = fields.Many2one('act.stockroom', string='Stock Room')
    validation_fuel_kendaraan_alat_id = fields.Many2one('fuel.kendaraan.alat', string='Fuel Kendaraan Alat')
    validation_fuel_dump_truck_id = fields.Many2one('fuel.dump.truck', string='Fuel Dump Truck')
    validation_fuel_excavator_id = fields.Many2one('fuel.excavator', string='Fuel Excavator')
