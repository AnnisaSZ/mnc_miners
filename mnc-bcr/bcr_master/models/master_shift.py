from odoo import api, fields, models, _


class MasterShift(models.Model):
    _name = 'master.shift'
    _description = 'Master Shift'

    name = fields.Char(string='Shift Name', required=True, )
    code = fields.Char(string='Shift Code', required=True, )
    area_code = fields.Many2one('master.area', required=True, )
    bisnis_unit_name = fields.Char(related='area_code.bisnis_unit_id.name', string='Bisnis Unit Name', store=True,
                                readonly=True)
    active = fields.Boolean(string='Active', default=True)
