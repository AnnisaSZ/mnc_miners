from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    mncei_employee_id = fields.Many2one(
        'mncei.employee',
        string='Employee', store=True
    )
    mncei_dept_id = fields.Many2one(
        'mncei.department',
        string='Div/Dept', related='mncei_employee_id.department', store=True
    )

    @api.constrains('mncei_employee_id')
    def check_related_employee(self):
        for user in self:
            if user.mncei_employee_id:
                user_ids = self.search([('mncei_employee_id', '=', user.mncei_employee_id.id)])
                if len(user_ids) > 1:
                    raise ValidationError(_("Employee sudah di relasikan dengan user lain."))
