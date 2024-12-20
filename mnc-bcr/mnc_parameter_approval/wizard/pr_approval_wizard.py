# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError
from odoo import http


class MncPrApprovalWizard(models.TransientModel):
    """MNC Document Approval Wizard."""
    _inherit = "purchase.requisition.approval.wizard"

    finance_dept_params_ids = fields.Many2many(
        'mncei.department', string='Finance Department', copy=False)
