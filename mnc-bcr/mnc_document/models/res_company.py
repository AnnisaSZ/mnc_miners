from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    is_lahan = fields.Boolean(
        string='Lahan',
    )
