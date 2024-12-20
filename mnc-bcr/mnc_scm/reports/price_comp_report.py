# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError



class ReportPriceComparison(models.AbstractModel):
    _name = 'report.mnc_scm.report_pc'
    _description = 'Reports Price Comparison'

    # Get User Print
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['price.comparation'].browse(docids)
        if docs.state == 'approve' or docs.state == 'purchase':
        # docs.update({'write_uid': self.env.uid})
            return {
                'doc_ids': docids,
                'doc_model': 'price.comparation',
                'docs': docs,
                'data': data,
            }
        else:
            raise ValidationError(_("Document Not Fully Approved!"))
