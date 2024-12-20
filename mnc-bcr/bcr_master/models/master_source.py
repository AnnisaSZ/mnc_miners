from odoo import api, fields, models, _


class MasterSource(models.Model):
    _name = 'master.source'
    _description = 'Master Source'

    name = fields.Char(string='Source Name', required=True, )
    code = fields.Char(string='Source Code', required=True, )
    seam_coal_id = fields.Many2one('seam.coal', )
    area_code = fields.Many2one('master.area', required=True, )
    bisnis_unit_name = fields.Char(related='area_code.bisnis_unit_id.name', string='Bisnis Unit Name',  store=True, readonly=True)
    active = fields.Boolean(string='Active', default=True)


class SeamCoal(models.Model):
    _name = 'seam.coal'
    _description = 'Seam Coal'

    name = fields.Char(string='Seam Coal Name', required=True, )
    code = fields.Char(string='Seam Coal Code', )
    active = fields.Boolean(string='Active', default=True)
