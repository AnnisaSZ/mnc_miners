# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _


class MncInputEmail(models.TransientModel):
    """MNC Document Approval Wizard."""
    _name = "mnc.input.email.wizard"
    _description = "Mnc Input Email Wizard"

    # def get_legal_id(self):
    #     return self.env['mncei.doc'].browse(self._context.get('active_id')).id

    legal_id = fields.Many2one(
        'mncei.doc',
        string='Legal ID'
    )
    perizinan_id = fields.Many2one('mncei.perizinan', 'Perizinan')
    laporan_id = fields.Many2one('mncei.lap.wajib', 'Laporan')
    line_ids = fields.One2many(
        'mnc.input.email.line.wizard',
        'input_id',
        string='Emails List',
    )

    def submit(self):
        for input_id in self:
            if input_id.line_ids:
                result = []
                # Add New
                for line in input_id.line_ids:
                    result.append(line.email)
                # Add Existing
                if input_id.legal_id:
                    if input_id.legal_id.email_reminder:
                        result.append(input_id.legal_id.email_reminder)
                    temp_res = ','.join(result)
                    input_id.legal_id.write({'email_reminder': temp_res})
                elif input_id.perizinan_id:
                    if input_id.perizinan_id.email_reminder:
                        result.append(input_id.perizinan_id.email_reminder)
                    temp_res = ','.join(result)
                    input_id.perizinan_id.write({'email_reminder': temp_res})
                elif input_id.laporan_id:
                    if input_id.laporan_id.email_reminder:
                        result.append(input_id.laporan_id.email_reminder)
                    temp_res = ','.join(result)
                    input_id.laporan_id.write({'email_reminder': temp_res})
        return


class MncInputEmailLine(models.TransientModel):
    """MNC Document Approval Wizard."""
    _name = "mnc.input.email.line.wizard"
    _description = "Mnc Input Email Line Wizard"

    input_id = fields.Many2one(
        'mnc.input.email.wizard',
        string='Input ID',
    )
    email = fields.Char(
        string='Email',
    )
