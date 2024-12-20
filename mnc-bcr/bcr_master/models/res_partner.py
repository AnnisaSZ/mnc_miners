from odoo import fields, api, models, _

import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # MASTER BUYER
    is_buyer = fields.Boolean('Is a Buyer', default=False)
    kode_buyer = fields.Char('Kode Buyer', readonly=True)
    keterangan = fields.Text(string='Keterangan')
    fax_no = fields.Char('Fax No')

    _sql_constraints = [('unique_kontraktor', 'unique(name,tipe_kontraktor,bisnis_unit_id)',
                        'Nama + Tipe Kontraktor + Bisnis Unit must be unique !')]

# MASTER KONTRAKTOR
    is_kontraktor = fields.Boolean('Is a Contractor', default=False)
    kode_kontraktor = fields.Char('Kode Contractor', readonly=True)
    tipe_kontraktor = fields.Selection([('kontraktor_hauling', 'Kontraktor Hauling'),
                                        ('kontraktor_produksi', 'Kontraktor Produksi'),
                                        ('kontraktor_barging', 'Kontraktor Barging'),
                                        ], string="Tipe Kontraktor")
    bisnis_unit_id = fields.Many2one('master.bisnis.unit', string='Bisnis Unit')

    #
    # keterangan -> sudah ada di comment ( notes )

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)

        if self.is_buyer == True:
            seq = self.env['ir.sequence'].next_by_code('master.buyer')
            res.update({"kode_buyer": seq})

        if self.is_kontraktor == True:
            seq = self.env['ir.sequence'].next_by_code('master.contractor')
            res.update({"kode_kontraktor": seq})

        return res

    @api.onchange('is_buyer')
    def _onchange_is_buyer(self):
        if self.is_buyer:
            self.is_kontraktor = False
        if self.kode_buyer == True:
            if self.kode_buyer == False:
                self.kode_buyer = self.env['ir.sequence'].next_by_code('master.buyer')
            else:
                _logger.info('sudah pernah ada kode_buyer sebelumnya %s' % self.kode_buyer)

    @api.onchange('is_kontraktor')
    def _onchange_is_kontraktor(self):
        if self.is_kontraktor:
            self.is_buyer = False

        if self.kode_kontraktor == True:
            if self.kode_kontraktor == False:
                self.kode_kontraktor = self.env['ir.sequence'].next_by_code('master.contractor')
            else:
                _logger.info('sudah pernah ada kode_contractor sebelumnya %s' % self.kode_kontraktor)


