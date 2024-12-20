from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class asetkategoriModels(models.Model):
    _name = 'asetkategori.module'
    _description = 'Category ASSET'

    id_kategori = fields.Integer(
        string='ID Kategori', related='id', store=True
    )
    kategori_aset = fields.Char(
        string='Kategori Aset', store=True, required=True
    )
    code = fields.Char('Kode', store=True, required=True)
    status = fields.Selection(
        [
            ('aktif', 'Aktif'),
            ('nonaktif', 'Non Aktif')
        ], default='aktif', store=True, string='Status', required=True)
    categ_line_ids = fields.One2many(
        'sub.categ.aset',
        'aset_id',
        string='Sub Kategori', store=True
    )

    def name_get(self):
        result = []
        for kategori_aset in self:
            name = kategori_aset.kategori_aset
            result.append((kategori_aset.id, name))
        return result

    @api.constrains('code')
    def check_code(self):
        for categ in self:
            categ_ids = self.search([('code', '=', categ.code)])
            if len(categ_ids) > 1:
                raise ValidationError(_("Kode Kategori tidak boleh sama"))


class SubCategAset(models.Model):
    _name = 'sub.categ.aset'
    _description = 'Sub Kategori Aset'

    aset_id = fields.Many2one(
        'asetkategori.module',
        string='Kategori Aset', store=True, required=True
    )
    name = fields.Char(
        string='Nama Sub Kategori', store=True, required=True
    )
    code = fields.Char(
        string='Kode Sub Aset', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Aktif'),
            ('nonaktif', 'Non Aktif')
        ], default='aktif', store=True, string='Status', required=True)
    sub_categ_line_ids = fields.One2many(
        'sub.categ.aset.line',
        'parent_id',
        string='Sub Kategori Lines', store=True
    )

    @api.constrains('code')
    def check_code(self):
        for sub in self:
            sub_ids = self.search([('code', '=', sub.code), ('aset_id', '=', sub.aset_id.id)])
            if len(sub_ids) > 1:
                raise ValidationError(_("Kode Sub Kategori tidak boleh sama"))


class SubCategAsetLine(models.Model):
    _name = 'sub.categ.aset.line'
    _description = 'Sub Kategori Aset Line'

    parent_id = fields.Many2one(
        'sub.categ.aset',
        string='Sub Kategori',
    )
    name = fields.Char(
        string='Keterangan',
    )
    code = fields.Char('Kode', store=True, required=True)
    status = fields.Selection(
        [
            ('aktif', 'Aktif'),
            ('nonaktif', 'Non Aktif')
        ], default='aktif', store=True, string='Status', required=True)
