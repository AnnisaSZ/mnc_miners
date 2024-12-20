# -*- coding: utf-8 -*-
from odoo import models, fields, api
from functools import lru_cache


class ReportTrainingRequest(models.AbstractModel):
    _name = 'report.mnc_training_request.report_trainig'
    _description = 'Training Report'

    # Get User Print
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mncei.training.requesition'].browse(docids)
        docs.update({'write_uid': self.env.uid})
        return {
            'doc_ids': docids,
            'doc_model': 'mncei.training.requesition',
            'docs': docs,
            'data': data,
        }
