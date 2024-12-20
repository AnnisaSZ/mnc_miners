from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_marketing = fields.Boolean("Marketing Product's", store=True)
    # Spec
    gcv_arb = fields.Integer('GCV ARB', store=True)
    gcv_start_arb = fields.Integer('GCV ARB', store=True)
    gcv_end_arb = fields.Integer('GCV ARB', store=True)
    tm_arb_start = fields.Integer('TM ARB Start', store=True)
    tm_arb_end = fields.Integer('TM ARB End', store=True)
    im_adb = fields.Integer('IM ADB', store=True)
    ash_adb_start = fields.Integer('ASH ADB Start', store=True)
    ash_adb_end = fields.Integer('ASH ADB End', store=True)
    vm_adb = fields.Integer('VM ADB', store=True)
    fc_adb = fields.Char('FC ADB', store=True)
    sulfur_adb_start = fields.Float('Sulfur ADB Start', store=True)
    sulfur_adb_end = fields.Float('Sulfur ADB End', store=True)
    hgi = fields.Integer('HGI', store=True)
    # size = fields.Integer('Size 0-100m', store=True)

    #
    min_size = fields.Integer('Min Size', store=True)
    max_size = fields.Integer('Max Size', store=True)
    size = fields.Char('Size', store=True)

    initial_deformation = fields.Integer('Initial Deformation', store=True)
    spherical = fields.Integer('Spherical', store=True)
    hemispherical = fields.Integer('Hemispherical', store=True)
    fluid = fields.Integer('Fluid', store=True)
