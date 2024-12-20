from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class PlanningHauling(models.Model):
    _name = 'planning.hauling'
    _description = 'Planning Hauling'
    _rec_name = "kode_planning"

    # Master
    kode_planning = fields.Char(string='Kode Planning', readonly=True, default="#")
    activity_id = fields.Many2one('master.activity', string='Activity', required=True,
                                  default=lambda self: (self.env["master.activity"].get_activity_by_code('01-HL')))
    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', required=True)
    bisnis_unit_id = fields.Many2one('master.bisnis.unit',
                                     default=lambda self: (self.env["res.users"].get_default_bisnis_unit_id()))

    product = fields.Many2one('product.product', string='Product', required=True, default=False)
    volume_plan = fields.Float('Volume Plan', required=True, default=0)
    kontraktor_id = fields.Many2one('res.partner', string='Kontraktor', required=True)

    date_start = fields.Date(string='Date Start')
    date_end = fields.Date(string='Date End')
    workdays = fields.Float('Workdays', compute='_compute_workdays', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Review'),
        ('approve', 'Approve'),
        ('complete', 'Complete'),
        ('reject', 'Reject'),
    ], string='State', default='draft', readonly=True)

    # Review
    total_review = fields.Integer(string='Total Review')
    total_reviewed = fields.Integer(string='Total Reviewed')
    progress_review = fields.Char(string='Review')
    review_complete = fields.Boolean(string='Review Complete')

    # Approve
    total_approve = fields.Integer(string='Total Approve')
    total_approved = fields.Integer(string='Total Approved')
    progress_approve = fields.Char(string='Approve')
    approve_complete = fields.Boolean(string='Approve Complete')

    validation_plan = fields.One2many('validation.plan', 'validation_planning_hauling_id', string='Validation',
                                      default=lambda self: (self.set_validation()))
    revise_note = fields.Char(string='Revise Note')

    is_reviewer = fields.Boolean(string='is reviewer', compute='_set_reviewer')
    is_approver = fields.Boolean(string='is approve', compute='_set_approver')

    def _set_approver(self):
        for rec in self:
            approver = rec.validation_plan.filtered(
                lambda x: x.user_id.id == self.env.user.id and x.validation_type_id.code == 'approve')
            if approver:
                rec.is_approver = True
            else:
                rec.is_approver = False

    def _set_reviewer(self):
        for rec in self:
            reviewer = rec.validation_plan.filtered(
                lambda x: x.user_id.id == self.env.user.id and x.validation_type_id.code == 'review')
            if reviewer:
                rec.is_reviewer = True
            else:
                rec.is_reviewer = False

    # BUTTON start, review, approve, revise, reject
    def action_start(self):
        if not self.validation_plan:
            raise UserError('User validation belum diinput !')
        self.write({'state': 'review'})

    def action_review(self):
        for rec in self:
            rec.state = 'approve'

    def action_approve(self):
        for rec in self:
            rec.state = 'complete'

    def action_revise(self):
        for rec in self:
            if rec.revise_note:
                rec.state = 'review'
            elif rec.revise_note == False:
                raise UserError('Fill Revise Note before click Revise ')

    def action_reject(self):
        for rec in self:
            rec.state = 'reject'

    # create, sequence
    @api.model
    def create(self, vals):
        res = super(PlanningHauling, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('planning.hauling')
        seq_code = self.env["res.users"].get_default_bisnis_unit_seq_code()
        seq = seq.replace('BUCODE', seq_code)
        res.update({"kode_planning": seq})
        return res

    def set_validation(self):
        result = False
        bu_id = self.env["res.users"].get_default_bisnis_unit_id()
        if bu_id:
            ####
            validation = self.env['validation.validation'].search([('model_id.model', '=', self._name),
                                                                   ('bisnis_unit_id', '=', bu_id)],
                                                                  limit=1)
            vals = []

            if validation:
                for rec in validation.validation_line:
                    vals.append((0, 0, {
                        'user_id': rec.user_id.id,
                        'validation_type_id': rec.validation_type_id.id,
                    }))
            else:
                raise UserError('Validation untuk Form Planning Hauling belum disetting')

            ####
            result = vals
        return result

    @api.onchange('bisnis_unit_id')
    def _onchange_bisnis_unit_id(self):
        if self.bisnis_unit_id:
            self.set_validation()

    @api.onchange('sub_activity_id')
    def _onchange_sub_activity_id(self):
        if self.sub_activity_id:
            self.product = False

    @api.depends('date_start', 'date_end')
    def _compute_workdays(self):
        if self.date_start and self.date_end:
            d1 = datetime.strptime(str(self.date_start), '%Y-%m-%d')
            d2 = datetime.strptime(str(self.date_end), '%Y-%m-%d')
            d3 = d2 - d1
            self.workdays = str(d3.days + 1)

    @api.constrains('date_start')
    def _check_date_backdate(self):
        for record in self:
            d1 = datetime.strptime(str(record.date_start), '%Y-%m-%d')
            d2 = datetime.strptime(str(record.date_end), '%Y-%m-%d')
            d3 = d2 - d1
            if d3.days + 1 <= 0:
                raise ValidationError(
                    'Check Again ! Start date must be earlier than End Date\nRevise your input')

            d4 = datetime.strptime(str(fields.Date.today()), '%Y-%m-%d')
            d5 = d1 - d4
            d5 = str(d5.days + 1)
            # if int(d5) <= -1:
            #     raise ValidationError('Check Again ! Start date cannot be less than today\nYou may input backdate transaction 1 day before today')
