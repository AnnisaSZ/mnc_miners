from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class MnceiSurat(models.Model):
    _name = "mncei.doc.surat"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Dokumen Surat"
    _order = 'id desc'

    name = fields.Char(string='Document Name', store=True, size=120, required=True)
    jenis_surat = fields.Selection([
        ('masuk', 'Surat Masuk'),
        ('keluar', 'Surat Keluar'),
    ], default='masuk', store=True, string="Mail Type", required=True)
    company_type_mail = fields.Selection([
        ('instansi', 'Instansi'),
        ('perorangan', 'Perorangan'),
        ('perseroan', 'Perusahaan'),
    ], default='instansi', store=True, string="Mail Company Type", required=True)
    tujuan_surat_char = fields.Char(string="Mail To", store=True)
    tujuan_surat = fields.Many2one('mncei.doc.surat.tujuan', string="Mail To", store=True)
    alamat = fields.Text(
        string='Address', size=50, required=True, store=True
    )
    tgl_surat = fields.Date(
        string='Mail Date', store=True, required=True
    )
    no_surat = fields.Char(
        string='Mail Number', store=True, size=10, required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company', required=True, store=True
    )
    description = fields.Text(
        string='Description', size=50, required=True, store=True
    )
    pic_id = fields.Many2one('res.users', 'PIC', default=lambda self: self.env.user, store=True, required=True, copy=False)
    phone = fields.Char("Phone", size=16, store=True, required=True, help="Nomor telepon penanggung jawab dokumen")
    # url_document = fields.Char("URL", size=150, store=True, help="Penyimpanan softcopy")
    release_date = fields.Date("Release Date", store=True, required=True, help="Tanggal dokumen terbit")
    document_status = fields.Many2one('mncei.doc.status', 'State', tracking=True, store=True, required=True, domain="[('state', '=', 'active'), ('is_surat', '=', True)]")
    remaks = fields.Text('Remarks', store=True, required=True, size=100, tracking=True)

    attachment = fields.Binary(string='Upload Document', store=True, attachment=True)
    attachment_filename = fields.Char(string='Filename', size=25, store=True)
    location_doc_id = fields.Many2one('mncei.hardcopy.loc', store=True, required=True, size=250)
    rak = fields.Selection([
        ('Rak_1', 'Rak 1'),
        ('Rak_2', 'Rak 2'),
        ('Rak_3', 'Rak 3'),
        ('Rak_4', 'Rak 4'),
        ('Rak_5', 'Rak 5')
    ], default='Rak_1', required=True, store=True, string='Partition', tracking=True)
    url_document = fields.Text('URL', store=True, size=50)


class MnceiSuratTujuan(models.Model):
    _name = "mncei.doc.surat.tujuan"

    name = fields.Char(
        string='Instansi Name',
    )
