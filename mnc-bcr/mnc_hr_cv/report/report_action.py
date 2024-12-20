# -*- coding: utf-8 -*-

from odoo import models, fields, api
from functools import lru_cache


class ReportEmployeeCV(models.AbstractModel):
    _name = 'report.mnc_hr_cv.report_cv_energy'
    _description = 'Report CV Employee'

    # Get User Print
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mncei.employee'].browse(docids)
        docs.update({'write_uid': self.env.uid})
        return {
            'doc_ids': docids,
            'doc_model': 'mncei.employee',
            'docs': docs,
            'data': data,
        }
