from odoo import models, api, fields
from datetime import datetime, date


class ReportFISTemplate(models.AbstractModel):
    _name = 'report.mnc_fis.report_fis'
    _description = "MNC FIS Template Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        datas = self.env['report.fis'].search([('id', 'in',docids)])
        return {'doc_ids': docids,
                'docs': datas,
                'data': data,
                'print_date': fields.Datetime.context_timestamp(self, fields.Datetime.now()), 
                }
