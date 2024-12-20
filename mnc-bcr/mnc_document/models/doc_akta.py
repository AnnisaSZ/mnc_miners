from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class MnceiBaseDokumenAkta(models.Model):
    _name = "mncei.doc.akta"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Dokumen Akta"
    _order = 'id desc'

    jenis_akta = fields.Selection([
        ('pendirian', 'Pendirian'),
        ('perubahan', 'Perubahan')
    ], default='pendirian', required=True, store=True, string='Akta Type', tracking=True)
    no_akta = fields.Char('Akta Number', store=True, required=True, size=30, tracking=True)
    date_akta = fields.Date('Akta Date', store=True, required=True, tracking=True)
    release_date = fields.Date('Release Date', store=True, default=fields.Date.today(), required=True, tracking=True)
    name = fields.Char('Document Name', store=True, size=50)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id, store=True, required=True)
    notaris = fields.Char('Notary', store=True, required=True, size=50, tracking=True)
    description = fields.Text('Description', store=True, required=True, size=100)
    penyimpanan = fields.Text('Hardcopy Location', store=True, required=False, size=50)
    pic_id = fields.Many2one('res.users', 'PIC', default=lambda self: self.env.user, store=True, required=True, copy=False)
    phone = fields.Char("Phone", size=16, store=True, required=True, help="Nomor telepon penanggung jawab dokumen")
    document_status = fields.Many2one('mncei.doc.status', 'State', tracking=True, store=True, required=True, domain="[('state', '=', 'active'), ('is_akta', '=', True)]")
    remaks = fields.Text('Remarks', store=True, required=True, size=100, tracking=True)
    # ============= Location =============
    location_doc_id = fields.Many2one('mncei.hardcopy.loc', store=True, required=True, size=250)
    rak = fields.Selection([
        ('Rak_1', 'Rak 1'),
        ('Rak_2', 'Rak 2'),
        ('Rak_3', 'Rak 3'),
        ('Rak_4', 'Rak 4'),
        ('Rak_5', 'Rak 5')
    ], default='Rak_1', required=True, store=True, string='Partition', tracking=True)
    url_penyimpanan = fields.Text('URL Location', store=True, size=50)
    # ============= SK Info ================
    sk_number = fields.Char(string='SK Number', store=True)
    sk_date = fields.Date('SK Date', store=True)

    def name_get(self):
        result = []
        for doc_akta in self:
            name = doc_akta.no_akta
            result.append((doc_akta.id, name))
        return result
