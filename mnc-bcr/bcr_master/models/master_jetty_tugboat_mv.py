from odoo import api, fields, models, _

class MasterTugboat(models.Model):
    _name = 'master.tugboat'
    _description = 'Master Tugboat'

    name = fields.Char(string='Nama Tugboat', required=True)
    active = fields.Boolean(string='Active', default=True)
    #code = fields.Char(string='Code')


class MasterMV(models.Model):
    _name = 'master.mv'
    _description = 'Master Mother Vessel'

    name = fields.Char(string='Nama MV', required=True)
    active = fields.Boolean(string='Active', default=True)
    #code = fields.Char(string='Code')


class MasterJetty(models.Model):
    _name = 'master.jetty'
    _description = 'Master Jetty'

    name = fields.Char(string='Nama Jetty', required=True)
    active = fields.Boolean(string='Active', default=True)
    #code = fields.Char(string='Code')