from odoo import api, fields, models, _


class MasterFuelman(models.Model):
    _name = 'master.fuelman'
    _description = 'Master Fuelman'

    name = fields.Char(string='FuelMan Name', required=True, )
    code = fields.Char(string='FuelMan Code', required=True, )
    fuelman_pic = fields.Many2one('fuelman.pic', string='FuelMan PIC')

    active = fields.Boolean(string='Active', default=True)


    @api.model
    def create(self, vals):
        res = super(MasterFuelman, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('master.fuelman')
        res.update({"code": seq})
        return res


class FuelmanPic(models.Model):
    _name = 'fuelman.pic'
    _description = 'Fuelman PIC'

    name = fields.Char(string='FuelMan PIC Name')
    #code = fields.Char(string='FuelMan PIC Code')
