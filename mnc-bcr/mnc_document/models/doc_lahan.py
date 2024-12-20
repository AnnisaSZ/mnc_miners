from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class MnceiBaseDokumenLahan(models.Model):
    _name = "mncei.doc.lahan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Dokumen Lahan"
    _order = 'id desc'

    active = fields.Boolean('Active', store=True, default=True)
    jenis_lahan = fields.Selection([
        ('shm', 'SHM'),
        ('sph', 'SPH'),
        ('aph', 'APH'),
        ('skt', 'SKT'),
        ('dll', 'Lainnya'),
    ], default='shm', required=True, store=True, string='Document Type')
    no_doc_lahan = fields.Char('Document Number', store=True, required=True, size=25)
    pemilik_lahan = fields.Char('Owner Land', store=True, required=True, size=25)
    pemilik_lahan_line_ids = fields.One2many(
        'pemilik.lahan.line',
        'lahan_id',
        string='Owner Land List', store=True
    )
    luas = fields.Float(
        string='Luas(M²)',
    )
    kabupaten_id = fields.Many2one(
        'mncei.wilayah.lahan',
        string='Regency', domain="[('type_wilayah', '=', 'kab')]", store=True, required=True, help="Kabupaten"
    )
    kecamatan_id = fields.Many2one(
        'mncei.wilayah.lahan',
        string='District', domain="[('type_wilayah', '=', 'kec'), ('kabupaten_id', '=', kabupaten_id)]", store=True, required=True, help="Kecamatan"
    )
    desa_id = fields.Many2one(
        'mncei.wilayah.lahan',
        string='Village', domain="[('type_wilayah', '=', 'desa'), ('kecamatan_id', '=', kecamatan_id)]", store=True, required=True, help="Desa"
    )
    release_date = fields.Date('Release Date', store=True, required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company', default=lambda self: self.env.user.company_id, store=True, required=True
    )
    company_land_id = fields.Many2one(
        'res.company.lahan',
        string='Company Land', required=False
    )
    description = fields.Text('Description', store=True, required=True,size=50)
    pic_id = fields.Many2one('res.users', 'PIC', default=lambda self: self.env.user, store=True, required=True, copy=False)
    phone = fields.Char("Phone", size=16, store=True, required=True, help="Nomor telepon penanggung jawab dokumen")
    document_status = fields.Many2one('mncei.doc.status', 'State', tracking=True, store=True, required=True, domain="[('state', '=', 'active'), ('is_lahan', '=', True)]")
    remaks = fields.Text('Remarks', store=True, required=True, size=100)
    # ============= Location =============
    penyimpanan = fields.Text('Hardcopy Location', store=True, required=False, size=50)
    location_doc_id = fields.Many2one('mncei.hardcopy.loc', store=True, required=True, size=250)
    rak = fields.Selection([
        ('Rak_1', 'Rak 1'),
        ('Rak_2', 'Rak 2'),
        ('Rak_3', 'Rak 3'),
        ('Rak_4', 'Rak 4'),
        ('Rak_5', 'Rak 5')
    ], default='Rak_1', required=True, store=True, string='Partition', tracking=True)
    url_penyimpanan = fields.Text('URL', store=True, size=50)

    def name_get(self):
        result = []
        for doc_lahan in self:
            name = doc_lahan.no_doc_lahan
            result.append((doc_lahan.id, name))
        return result


class ListedPemilikLahan(models.Model):
    _name = "pemilik.lahan.line"
    _description = "Pemilik Lahan"

    name = fields.Char(
        string='Owner', store=True, required=True
    )
    tahun_kepemilikan = fields.Char(
        string='Year of Ownership', store=True
    )
    lahan_id = fields.Many2one(
        'mncei.doc.lahan',
        string='Land ID', store=True, ondelete='cascade'
    )


class MnceiWilayah(models.Model):
    _name = "mncei.wilayah.lahan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Wilayah Lahan"

    name = fields.Char(
        string='Area Name', store=True, required=True
    )
    kabupaten_id = fields.Many2one(
        'mncei.wilayah.lahan',
        string='Regency ID', domain="[('type_wilayah', '=', 'kab')]", index=True, ondelete='cascade'
    )
    kecamatan_id = fields.Many2one(
        'mncei.wilayah.lahan',
        string='District ID', domain="[('type_wilayah', '=', 'kec')]", index=True, ondelete='cascade'
    )
    kecamatan_ids = fields.One2many(
        'mncei.wilayah.lahan',
        'kabupaten_id',
        string='District List'
    )
    desa_ids = fields.One2many(
        'mncei.wilayah.lahan',
        'kecamatan_id',
        string='Village List',
    )
    type_wilayah = fields.Selection([
        ('kab', 'Kabupaten'),
        ('kec', 'Kecamatan'),
        ('desa', 'Desa'),
    ], string='Types', store=True)


class ResCompanyLand(models.Model):
    _name = "res.company.lahan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Perusahaan pemilik lahan"

    name = fields.Char(
        string='Nama Perusahaan', store=True, required=True
    )
