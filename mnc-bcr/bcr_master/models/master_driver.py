from odoo import api, fields, models, _


class MasterDriver(models.Model):
    _name = 'master.driver'
    _description = 'Master Driver'

    name = fields.Char(string='Driver Name', required=True, )
    code = fields.Char(string='Driver Code', required=True, )
    no_telp = fields.Char(string='Nomor Telepon', required=True, )
    active = fields.Boolean(string='Active', default=True)
