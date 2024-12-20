from odoo import api, fields, models, _

class MasterBarge(models.Model):
    _name = 'master.barge'
    _description = 'Master Barge'
    _rec_name = 'kode_barge'

    MARKET_LIST =[
        ('domestic', 'Domestic Market'),
        ('export', 'Export Market'),
    ]

    kode_barge = fields.Char(string='Barge Code', required=True, readonly=True, default='#')
    nama_barge = fields.Char(string='Barge Name', required=True)
    market = fields.Selection(selection=MARKET_LIST, string='Market', default='domestic', required=True)
    # tugboat = fields.Many2one('master.tugboat', string='TugBoat Name')
    # mv_boat = fields.Many2one('master.mv', string='Mother Vessel')
    # jetty = fields.Many2one('master.jetty', string='Jetty')
    active = fields.Boolean(string='Active', default=True)


    @api.model
    def create(self, vals):
        res = super(MasterBarge, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('master.barge')
        res.update({"kode_barge": seq})
        return res

