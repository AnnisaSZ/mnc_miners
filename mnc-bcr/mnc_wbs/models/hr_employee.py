from odoo import fields, models, api, _


class ResEmployee(models.Model):
    _inherit = 'mncei.employee'

    auditor_1_ids = fields.Many2many('wbs.auditor', 'auditor_1_ids')
    auditor_2_ids = fields.Many2many('wbs.auditor', 'auditor_2_ids')
    auditor_3_ids = fields.Many2many('wbs.auditor', 'auditor_3_ids')
    list_employee_wbs_ids = fields.Many2many('wbs.report.bod', 'list_employee_wbs_ids')

    wbs_employee_ids = fields.One2many('wbs.report.emp', 'employee_id', copy=False)
