# -*- coding: utf-8 -*-

from odoo import models, fields, api
from functools import lru_cache


class ReportPurchaseRequisition(models.AbstractModel):
    _name = 'report.mnc_purchase_request.report_purchase_requisition_new'
    _description = 'Purchase Requisition Report'

    # Get User Print
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mncei.purchase.requisition'].browse(docids)
        docs.update({'write_uid': self.env.uid})
        return {
            'doc_ids': docids,
            'doc_model': 'mncei.purchase.requisition',
            'docs': docs,
            'data': data,
        }
