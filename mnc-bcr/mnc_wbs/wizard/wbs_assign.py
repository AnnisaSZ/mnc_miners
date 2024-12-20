# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.translate import html_translate


class WbsAssignWizard(models.TransientModel):
    """MNC Approval Wizard."""
    _name = "wbs.assign.wizard"
    _description = "WBS Result"

    notes = fields.Html('Notes', translate=html_translate)
    to_employee_ids = fields.Many2many('mncei.employee', copy=False, string="Submit To", required=True)
    wbs_head_id = fields.Many2one('wbs.report.head', copy=False)
    dir_attachment_ids = fields.One2many('wbs.assign.wizard.attach', 'wbs_assign_id', copy=False, required=True)

    def action_submit(self):
        if self.wbs_head_id:
            if not self.notes:
                raise ValidationError(_("Please input your summary audit"))
            self.wbs_head_id.write({
                'summary_audit': self.notes,
                'state': 'result_audit',
            })
        return


class WbsAssignWizardAttach(models.TransientModel):
    _name = "wbs.assign.wizard.attach"

    wbs_assign_id = fields.Many2one('wbs.assign.wizard', copy=False)
    part_dokumen = fields.Binary(
        string='Dokumen Part',
        attachment=True, store=True
    )
    part_filename = fields.Char(
        string='Filename Part', store=True
    )
