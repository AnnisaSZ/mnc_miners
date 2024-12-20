# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.translate import html_translate


class WbsWizard(models.TransientModel):
    """MNC Approval Wizard."""
    _name = "wbs.wizard"
    _description = "WBS Result"

    notes = fields.Html('Notes', translate=html_translate)
    wbs_head_id = fields.Many2one('wbs.report.head', copy=False)
    # wbs_bod_id = fields.Many2one('wbs.report.bod', copy=False)
    result_attachment_ids = fields.Many2one('wbs.report.head.attach', copy=False)

    def button_close(self):
        return 

    def action_submit(self):
        if self.wbs_head_id:
            if not self.notes:
                raise ValidationError(_("Please input your summary audit"))
            self.wbs_head_id.write({
                'summary_audit': self.notes,
                'is_summary': True,
                'state': 'result_audit',
            })
            if self.wbs_head_id.list_emp_report_ids:
                for report_emp in self.wbs_head_id.list_emp_report_ids:
                    report_emp.write({'state': 'result_audit'})
            wbs_bod = self.wbs_head_id.list_dir_report_id
            wbs_bod.change_state_to_close()
        return
