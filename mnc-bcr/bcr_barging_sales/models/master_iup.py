from odoo import fields, models


class MasterBisnisUnit(models.Model):
    _inherit = 'master.bisnis.unit'

    jetty_code = fields.Char("Jetty Code", store=True)