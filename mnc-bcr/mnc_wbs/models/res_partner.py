from odoo import fields, models, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    other = fields.Char(string='Other Company',)
