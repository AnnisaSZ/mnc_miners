from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


class MncPeriodereminder(models.Model):
    _name = "mncei.periode.reminder"
    _description = "Periode Timeline reminder"
    _order = 'id desc'

    date_reminder = fields.Date("Date", store=True)
    document_id = fields.Many2one('mncei.doc', 'Document', store=True, ondelete='cascade')
    perizinan_id = fields.Many2one('mncei.perizinan', 'Perizinan', store=True, ondelete='cascade')
    laporan_id = fields.Many2one('mncei.lap.wajib', 'Laporan', store=True, ondelete='cascade')
    is_done = fields.Boolean('Done', store=True)

    def name_get(self):
        result = []
        for period_time in self:
            name = 'Periode'
            if period_time.document_id:
                name = period_time.document_id.document_number
            if period_time.perizinan_id:
                name = period_time.perizinan_id.license_number
            if period_time.laporan_id:
                name = period_time.laporan_id.doc_number
            result.append((period_time.id, name))
        return result


class MncMailReminder(models.Model):
    _name = "mncei.mail.reminder"
    _description = "Mail Reminder"

    document_id = fields.Many2one('mncei.doc', 'Document', store=True, ondelete='cascade')
    perizinan_id = fields.Many2one('mncei.perizinan', 'Perizinan', store=True, ondelete='cascade')
    laporan_id = fields.Many2one('mncei.lap.wajib', 'Laporan', store=True, ondelete='cascade')
    email = fields.Char(
        string='Email', store=True)
    remaks = fields.Text(
        string='Remaks', store=True, default='/'
    )

    def name_get(self):
        result = []
        for mail in self:
            name = 'Email Reminder'
            if mail.document_id:
                name = mail.document_id.document_number
            if mail.perizinan_id:
                name = mail.perizinan_id.license_number
            if mail.laporan_id:
                name = mail.laporan_id.doc_number
            result.append((mail.id, name))
        return result
