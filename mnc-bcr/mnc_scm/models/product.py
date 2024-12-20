from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_product_scm = fields.Boolean('Product SCM', default=False)


class Respartner(models.Model):
    _inherit = 'res.partner'

    fao = fields.Char('FAO')
