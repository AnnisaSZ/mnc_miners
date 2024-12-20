# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError



class ReportOrderRequest(models.AbstractModel):
    _name = 'report.mnc_scm.report_orf'
    _description = 'Reports Order Request'

    # Get User Print
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['order.request'].browse(docids)
        if docs.state == 'approve':
        # docs.update({'write_uid': self.env.uid})
            return {
                'doc_ids': docids,
                'doc_model': 'order.request',
                'docs': docs,
                'data': data,
            }
        else:
            raise ValidationError(_("Document Not Fully Approved!"))
        
