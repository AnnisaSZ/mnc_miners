from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sub_activity_id = fields.Many2one('master.sub.activity')
    activity_name = fields.Char(related='sub_activity_id.activity_id.name', string='Activity Name', store=True, readonly=True)
