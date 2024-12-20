from odoo import api, fields, models, _


class MasterArea(models.Model):
    _name = 'master.area'
    _description = 'Master Area'

    name = fields.Char(string='Area Name', required=True, )
    code = fields.Char(string='Area Code', required=True, )
    bisnis_unit_id = fields.Many2one('master.bisnis.unit')
    active = fields.Boolean(string='Active', default=True)


class MasterBisnisUnit(models.Model):
    _name = 'master.bisnis.unit'
    _description = 'Master Bisnis Unit'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    seq_code = fields.Char(string='Seq Code')
    lokasi_site = fields.Many2one('stock.location', "Lokasi Site")
    active = fields.Boolean(string='Active', default=True)



