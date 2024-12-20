from odoo import models, fields

class arsipdokumen(models.Model):
    _name = 'arsipdokumenform'
    _description = 'Arsip Dokumen Form'
    _rec_name = 'title' 

    title = fields.Char(string='Document Title', store=True, size=45, required=True)
    document_owner = fields.Many2one('mncei.department', store=True, string='Document Owner', required=True)
    company = fields.Many2one('res.company', store=True, string='Perusahaan', required=True)
    pic = fields.Many2one('mncei.employee', string='PIC', store=True, required=True)
    file_dokumen = fields.Binary(
        string='File', store=True
    )
    description = fields.Text(string='Description', size=125, store=True, required=True)
    release_date = fields.Date(string='Release Date', store=True, required=True)


    