from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


# Please Delete Constraint in SQL Database
# "ALTER TABLE hr_leave_allocation DROP CONSTRAINT hr_leave_allocation_type_value;"
class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    acttive = fields.Boolean("Active", store=True, default=True)
    mode_company_ids = fields.Many2many(
        'res.company', store=True, string='Companies', readonly=False, domain=_company_ids_domain,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    mode_department_ids = fields.Many2many(
        'mncei.department', store=True, string='Departments', readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    loc_working_id = fields.Many2one(
        'mncei.lokasi.kerja', 'Working Location', store=True,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    employee_id = fields.Many2one(
        'hr.employee', required=False)
    mncei_employee_id = fields.Many2one('mncei.employee', string="Employee", default=False, ondelete='cascade',
        index=True, store=True, states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    period_start = fields.Date('Start Date', store=True,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    period_end = fields.Date('End Date', store=True,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    holiday_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department')],
        string='Allocation Mode', readonly=True, required=True, invisible=True, default='employee',
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help="Allow to create requests in batchs:\n- By Employee: for a specific employee"
             "\n- By Company: all employees of the specified company"
             "\n- By Department: all employees of the specified department"
             "\n- By Employee Tag: all employees of the specific employee group category")
    mncei_holiday_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department')],
        string='Allocation Mode', readonly=True, required=True, default='employee',
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help='By Employee: Allocation/Request for individual Employee, By Employee Tag: Allocation/Request for group of employees in category')
    responsible_id = fields.Many2one('res.users', 'Responsible',
        related='holiday_status_id.responsible_id')
    is_approver = fields.Boolean('Approver', compute='_compute_is_approved')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Waiting Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
        ], string='Status', readonly=True, tracking=True, copy=False, default='confirm',
        help="The status is set to 'To Submit', when an allocation request is created." +
        "\nThe status is 'To Approve', when an allocation request is confirmed by user." +
        "\nThe status is 'Refused', when an allocation request is refused by manager." +
        "\nThe status is 'Approved', when an allocation request is approved by manager.")

    _sql_constraints = [
        ('duration_check', "CHECK ( number_of_days >= 0 )", "The number of days must be greater than 0."),
        ('number_per_interval_check', "CHECK(number_per_interval > 0)", "The number per interval should be greater than 0"),
        ('interval_number_check', "CHECK(interval_number > 0)", "The interval number should be greater than 0"),
    ]

    def _compute_is_approved(self):
        for record in self:
            # if record.user_responsible_ids.ids in self.env.uid:
            if self.env.uid in record.holiday_status_id.user_responsible_ids.ids:
                record.is_approver = True
            else:
                record.is_approver = False

    @api.onchange('mncei_holiday_type')
    def change_holiday(self):
        if self.mncei_holiday_type:
            if self.mncei_holiday_type == 'employee':
                self.holiday_type = 'employee'
            if self.mncei_holiday_type == 'company':
                self.holiday_type = 'company'
            if self.mncei_holiday_type == 'department':
                self.holiday_type = 'department'

    def action_approve(self):
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Allocation request must be confirmed ("To Approve") in order to approve it.'))

        # current_employee = self.env.user.mncei_employee_id

        # self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})
        self.action_validate()
        # self.activity_update()
        # return super(HolidaysAllocation, self).action_approve()

    # Overwrite Function
    def action_validate(self):
        # current_employee = self.env.user.mncei_employee_id
        for holiday in self:
            # if holiday.state not in ['confirm', 'validate1']:
            #     raise UserError(_('Allocation request must be confirmed in order to approve it.'))

            holiday.write({'state': 'validate'})
            holiday._action_validate_create_childs()
        # self.activity_update()
        return

    def _action_validate_create_childs(self):
        childs = self.env['hr.leave.allocation']
        if self.state == 'validate' and self.holiday_type in ['department', 'company']:
            # if self.holiday_type in ['department', 'company']:
            domain = [('lokasi_kerja', '=', self.loc_working_id.id)]
            if self.holiday_type == 'department':
                domain += [('department', 'in', self.mode_department_ids.ids)]
            else:
                domain += [('company', 'in', self.mode_company_ids.ids)]
            employees = self.env['mncei.employee'].search(domain)

            for employee in employees:
                childs += self.with_context(
                    mail_notify_force_send=False,
                    mail_activity_automation_skip=True
                ).create(self._prepare_holiday_values(employee))
            # TODO is it necessary to interleave the calls?
            childs.action_approve()
            if childs and self.validation_type == 'both':
                childs.action_validate()
        return childs

    @api.depends('mncei_employee_id', 'holiday_status_id')
    def _compute_leaves(self):
        for allocation in self:
            leave_type = allocation.holiday_status_id.with_context(mncei_employee_id=allocation.mncei_employee_id.id)
            allocation.max_leaves = leave_type.max_leaves
            allocation.leaves_taken = leave_type.leaves_taken

    def _prepare_holiday_values(self, employee):
        self.ensure_one()
        values = {
            'name': self.name,
            'holiday_type': 'employee',
            'holiday_status_id': self.holiday_status_id.id,
            'loc_working_id': self.loc_working_id.id,
            'notes': self.notes,
            'number_of_days': self.number_of_days,
            'parent_id': self.id,
            'mncei_employee_id': employee.id,
            'loc_working_id': self.loc_working_id.id,
            'period_start': self.period_start,
            'period_end': self.period_end,
            'allocation_type': self.allocation_type,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'interval_unit': self.interval_unit,
            'interval_number': self.interval_number,
            'number_per_interval': self.number_per_interval,
            'unit_per_interval': self.unit_per_interval,
        }
        return values

    @api.depends('holiday_type')
    def _compute_from_holiday_type(self):
        for allocation in self:
            if allocation.holiday_type == 'employee':
                if not allocation.employee_id:
                    allocation.employee_id = self.env.user.employee_id
                allocation.mode_company_id = False
                allocation.category_id = False
            if allocation.holiday_type == 'company':
                allocation.employee_id = False
                if not allocation.mode_company_id:
                    allocation.mode_company_id = self.env.company
                allocation.category_id = False
            elif allocation.holiday_type == 'department':
                allocation.employee_id = False
                allocation.mode_company_id = False
                allocation.category_id = False
            # elif allocation.holiday_type == 'category':
            #     allocation.employee_id = False
            #     allocation.mode_company_id = False
            elif not allocation.employee_id and not allocation._origin.employee_id:
                allocation.employee_id = self.env.context.get('default_employee_id') or self.env.user.employee_id

    @api.depends('holiday_type', 'employee_id')
    def _compute_department_id(self):
        for allocation in self:
            if allocation.holiday_type == 'employee':
                allocation.department_id = allocation.employee_id.department_id
            elif allocation.holiday_type == 'department':
                if not allocation.department_id:
                    allocation.department_id = self.env.user.employee_id.department_id
            # elif allocation.holiday_type == 'category':
            #     allocation.department_id = False

    def name_get(self):
        res = []
        for allocation in self:
            if allocation.holiday_type == 'company':
                target = allocation.mode_company_id.name
            elif allocation.holiday_type == 'department':
                target = allocation.department_id.name
            # elif allocation.holiday_type == 'category':
            #     target = allocation.category_id.name
            else:
                target = allocation.mncei_employee_id.sudo().nama_lengkap

            res.append(
                (allocation.id,
                 _("Allocation of %(allocation_name)s : %(duration).2f %(duration_type)s to %(person)s",
                   allocation_name=allocation.holiday_status_id.sudo().name,
                   duration=allocation.number_of_hours_display if allocation.type_request_unit == 'hour' else allocation.number_of_days,
                   duration_type='hours' if allocation.type_request_unit == 'hour' else 'days',
                   person=target
                ))
            )
        return res
