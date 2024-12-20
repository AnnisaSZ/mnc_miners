from odoo import fields, models


class ValidationPlan(models.Model):
    _inherit = 'validation.plan'

    validation_sales_plan_id = fields.Many2one('sales.plan', string='Sales Plan')
    validation_quality_barge_id = fields.Many2one('quality.barge', string='Quality Barge')
