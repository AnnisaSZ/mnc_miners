from odoo import api, fields, models, _


class MasterUnitKendaraan(models.Model):
    _name = 'master.unit.kendaraan'
    _description = 'Master Unit Kendaraan'
    _rec_name = 'kode_unit_kendaraan'

    kode_unit_kendaraan = fields.Char(string='Kode Unit Kendaraan', required=True)
    nama_unit_kendaraan = fields.Char(string='Nama Unit Kendaraan', required=True)
    tipe_unit_kendaraan = fields.Many2one('tipe.unit.kendaraan', required=True, string='Tipe Unit Kendaraan')
    merek_unit_kendaraan = fields.Many2one('merek.unit.kendaraan', required=True, string='Merek Unit Kendaraan')
    active = fields.Boolean(string='Active', default=True)

class TipeUnitKendaraan(models.Model):
    _name = 'tipe.unit.kendaraan'
    _description = 'Tipe Unit Kendaraan'

    name = fields.Char(string='Nama Tipe Unit Kendaraan', required=True)
    active = fields.Boolean(string='Active', default=True)
    #code = fields.Char(string='Code')

class MerekUnitKendaraan(models.Model):
    _name = 'merek.unit.kendaraan'
    _description = 'Merek Unit Kendaraan'

    name = fields.Char(string='Nama Merek Unit Kendaraan', required=True)
    active = fields.Boolean(string='Active', default=True)
    #code = fields.Char(string='Code')
