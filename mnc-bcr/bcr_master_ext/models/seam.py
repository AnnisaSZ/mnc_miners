from odoo import api, fields, models, _

class MasterSeam(models.Model):
    _inherit = 'master.seam'

    active = fields.Boolean(string="Archive", default=True)