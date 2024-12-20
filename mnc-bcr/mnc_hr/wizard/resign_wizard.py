# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError
from odoo import http


class EmployeeResign(models.TransientModel):
    """MNC Approval Wizard."""
    _name = "employee.resign.wizard"
    _description = "Employee Resign Reason"

    employee_ids = fields.Many2many('mncei.employee', 'employee_resign_rel', 'employee_id', 'resign_id', string="Employees")
    tgl_resign = fields.Date('Tanggal Resign', store=True)
    reason_resign = fields.Text('Alasan Resign', store=True)
    clearin_sheet_file = fields.Binary('Clearin Sheet', store=True)
    clearin_sheet_filename = fields.Char('Clearin Sheet', store=True)

    revisi_notes = fields.Text("Revisi Notes")

    def action_confirm(self):
        employee_id = self.env['mncei.employee'].browse(self._context.get('active_id'))
        for employee in employee_id:
            if employee.is_ikatan_dinas:
                if employee.dinas_end >= fields.Date.today():
                    raise ValidationError(_("Employee masih memiliki ikatan dinas."))
            employee.write({
                'active': False,
                'tgl_resign': self.tgl_resign,
                'reason_resign': self.reason_resign,
                'clearin_sheet_file': self.clearin_sheet_file,
                'clearin_sheet_filename': self.clearin_sheet_filename,
            })
        return

    def action_revise(self):
        employee_id = self.env['mncei.employee'].browse(self._context.get('active_id'))
        if employee_id:
            if not self.revisi_notes:
                raise ValidationError(_("Tolong input hal yang untuk direvisi."))
            employee_id.write({
                'state': 'draft',
                'is_revise': True,
                'revisi_notes': self.revisi_notes,
            })
        return
