from odoo import api, fields, models, _

class MasterBisnisUnit(models.Model):
    _inherit = 'master.bisnis.unit'

    nama_ktt = fields.Char(string='Nama KTT')
    ktt = fields.Char(string='Jabatan')
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    no_izin_iup = fields.Char(string='No. Izin IUP')
    tanggal_izin_iup = fields.Date(string='Tanggal Izin IUP')
    port = fields.Char(string='Port')

class MasterMV(models.Model):
    _inherit = 'master.mv'

    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')