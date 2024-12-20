from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime


class MnceiTicket(models.Model):
    _name = 'mncei.ticket'
    _description = 'MNCEI Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def get_sequence_number(self):
        sequence = self.env['ir.sequence'].next_by_code('ticket.helpdesk')
        return sequence

    no_ticket = fields.Char(
        string='No.', store=True, required=True, copy=False, default=get_sequence_number
    )
    name = fields.Char(
        string='Title', store=True, required=True, copy=False, default='/'
    )
    company_id = fields.Many2one('res.company', string="Company", store=True, required=True)
    request_id = fields.Many2one(
        'res.users',
        string='Requestor', default=lambda self: self.env.user, store=True, required=True
    )
    requestor_announce_ids = fields.Many2many(
        'res.users', 'requestor_annouce_rel', 'announce_id', 'requestor_id',
        string='CC User', store=True, required=True
    )
    email_request = fields.Char(
        string='Email', related='request_id.login', store=True
    )
    request_type = fields.Many2one(
        'mncei.ticket.type',
        string='Type', store=True, required=True, domain="[('status', '=', 'aktif')]"
    )
    categ_id = fields.Many2one(
        'mncei.ticket.category',
        string='Category', store=True, required=True, domain="[('status', '=', 'aktif')]"
    )
    dept_id = fields.Many2one(
        'mncei.department',
        string='To Department', store=True, tracking=True, required=True, domain="[('state', '=', 'active')]"
    )
    it_dept_id = fields.Many2one(
        'mncei.department',
        string='Department IT', store=True, tracking=True, domain="[('state', '=', 'active')]"
    )
    # person = fields.Boolean('Person Task', store=True)
    responsible_ids = fields.Many2many(
        'res.users',
        string='Responsible', store=True, required=True, tracking=True, domain="[('mncei_employee_id', '!=', False), ('mncei_dept_id', '=', dept_id)]"
    )
    # responsible_ids = fields.Many2one(
    #     'res.users', 'responsible_users_rel', 'responsible_id', 'requestor_id',
    #     string='Responsible', store=True, tracking=True, domain="[('mncei_employee_id', '!=', False), ('mncei_dept_id', '=', dept_id)]"
    # )
    urgency = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High')
        ], default='low', store=True, string='Priority', required=True, copy=False)
    expected_date = fields.Date('Expected Date', store=True)
    is_followup = fields.Boolean('Follow Up', store=True)
    description = fields.Text('Description', store=True, required=True)
    atth_file = fields.Binary(
        string='Attachment',
        attachment=True, store=True, copy=False
    )
    name_file = fields.Char(
        string='File Name', copy=False, store=True
    )
    state_id = fields.Many2one(
        'mncei.ticket.state', string='Status', index=True, tracking=True,
        compute='_compute_stage_id', readonly=False, store=True,
        copy=False, ondelete='restrict', group_expand='_read_group_stage_ids', domain="[('status', '=', 'aktif')]"
    )
    is_request = fields.Boolean('Is Request', store=True, default=True, copy=False)
    is_process = fields.Boolean('Is Process', store=True, copy=False)
    is_finish = fields.Boolean('Is Finish', store=True, copy=False)
    is_revice = fields.Boolean('Is Revice', store=True, copy=False)
    update_stage = fields.Datetime(string='Update Stage', store=True, copy=False, default=fields.Datetime.now())
    last_stage = fields.Datetime(string='Last Stage', store=True, copy=False)

    def _compute_is_responsible(self):
        for record in self:
            if self.env.user.id in record.responsible_ids.ids:
                record.is_responsible = True
            else:
                record.is_responsible = False

    def _compute_is_user_cc(self):
        for record in self:
            if self.env.user.id in record.requestor_announce_ids.ids:
                record.is_cc_user = True
            else:
                record.is_cc_user = False

    is_responsible = fields.Boolean(string="Is Responsible", compute='_compute_is_responsible')
    is_cc_user = fields.Boolean(string="Is CC User", compute='_compute_is_user_cc')

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = ['|', ('id', 'in', stages.ids), ('status', '=', 'aktif')]
        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.depends('responsible_ids')
    def _compute_stage_id(self):
        for ticket in self:
            if not ticket.state_id:
                ticket.state_id = ticket._stage_find(domain=[('status', '=', 'aktif')]).id

    def _stage_find(self, domain=None, order='sequence'):
        search_domain = list(domain)
        return self.env['mncei.ticket.state'].search(search_domain, order=order, limit=1)

    def action_to_process(self):
        process_id = self.env.ref('mnc_ticket_request.status_process')
        for ticket in self:
            ticket.update({
                'state_id': process_id.id,
                'is_process': True,
                'is_request': False,
                'is_finish': False,
                'is_revice': False,
            })

    def action_to_finish(self):
        finish_id = self.env.ref('mnc_ticket_request.status_finish')
        for ticket in self:
            ticket.update({
                'state_id': finish_id.id,
                'is_process': False,
                'is_request': False,
                'is_finish': True,
                'is_revice': False,
            })

    def action_to_revice(self):
        revice_id = self.env.ref('mnc_ticket_request.status_revice')
        for ticket in self:
            ticket.update({
                'state_id': revice_id.id,
                'is_process': False,
                'is_request': False,
                'is_finish': False,
                'is_revice': True,
            })

    @api.onchange('request_type')
    def onchange_category(self):
        self.categ_id = False

    @api.onchange('dept_id')
    def onchange_department(self):
        self.responsible_ids = False

    @api.model
    def create(self, vals):
        res = super(MnceiTicket, self).create(vals)
        res.notify_email(is_create=True)
        return res

    def write(self, values):
        if values.get('is_followup'):
            self.notify_email(is_followup=True)
        if values.get('state_id'):
            values.update({
                'update_stage': fields.Datetime.now(),
                'last_stage': self.update_stage or False})
            self.notify_email()
        if values.get('responsible_ids'):
            for res_respon in values.get('responsible_ids'):
                for responsible_id in res_respon[2]:
                    self.notify_email(is_create=True, responsible_id=responsible_id)
        res = super(MnceiTicket, self).write(values)
        return res

    def notify_email(self, is_create=False, is_followup=False, responsible_id=False):
        template_followup = self.env.ref('mnc_ticket_request.notification_followup')
        template_progress = self.env.ref('mnc_ticket_request.notification_progress')
        email_to = self.request_id
        if is_create:
            # To Responsible
            if responsible_id:
                email_to = self.env['res.users'].browse(responsible_id)
                template_create = self.env.ref('mnc_ticket_request.notification_request_ticket').with_context(dbname=self._cr.dbname, invited_users=email_to)
                template_create.send_mail(self.id, force_send=True, email_values={'email_to': email_to.login})
            else:
                for responsible_id in self.responsible_ids:
                    template_create = self.env.ref('mnc_ticket_request.notification_request_ticket').with_context(dbname=self._cr.dbname, invited_users=responsible_id)
                    template_create.send_mail(self.id, force_send=True, email_values={'email_to': email_to.login})

        #############################################
        elif is_followup:
            template_followup.send_mail(self.id, force_send=True, email_values={'email_to': email_to.login})
            for cc_user in self.requestor_announce_ids:
                template_followup.send_mail(self.id, force_send=True, email_values={'email_to': cc_user.login})
        else:
            template_progress.send_mail(self.id, force_send=True, email_values={'email_to': email_to.login})
            for cc_user in self.requestor_announce_ids:
                template_progress.send_mail(self.id, force_send=True, email_values={'email_to': cc_user.login})

    def check_auto_solved(self):
        stage_finish_id = self.env['mncei.ticket.state'].search([('is_finish', '=', True)], limit=1)
        stage_solved_id = self.env['mncei.ticket.state'].search([('is_solved', '=', True)], limit=1)
        ticket_ids = self.env['mncei.ticket'].search([('state_id', '=', stage_finish_id.id)])
        if ticket_ids:
            for ticket_id in ticket_ids:
                duration = ticket_id.categ_id.duration_auto_solve
                calc_duration = fields.Datetime.now().hour - ticket_id.update_stage.hour
                if calc_duration >= duration and stage_solved_id:
                    ticket_id.write({'state_id': stage_solved_id.id})
        return

    def check_auto_reminder(self):
        # Template Email
        template_reminder = self.env.ref('mnc_ticket_request.email_reminder_ticket').with_context(dbname=self._cr.dbname, invited_users=user_id)
        # Parameter
        stage_draft_id = self.env['mncei.ticket.state'].search([('is_draft', '=', True)], limit=1)
        ticket_ids = self.env['mncei.ticket'].search([('state_id', '=', stage_draft_id.id)])
        if ticket_ids:
            for ticket_id in ticket_ids:
                duration = int(self.env['ir.config_parameter'].sudo().get_param('duration_remainder'))
                calc_duration_days = fields.Date.today() - ticket_id.update_stage.date()
                if calc_duration_days.days >= 1:
                    for responsible_id in ticket_id.responsible_ids:
                        template_reminder = self.env.ref('mnc_ticket_request.email_reminder_ticket').with_context(dbname=self._cr.dbname, invited_users=responsible_id)
                        template_reminder.send_mail(ticket_id.id, force_send=True, email_values={'email_to': ticket_id.responsible_id.login})
                else:
                    calc_duration = fields.Datetime.now().hour - ticket_id.update_stage.hour
                    if calc_duration >= duration:
                        for responsible_id in ticket_id.responsible_ids:
                            template_reminder = self.env.ref('mnc_ticket_request.email_reminder_ticket').with_context(dbname=self._cr.dbname, invited_users=responsible_id)
                            template_reminder.send_mail(ticket_id.id, force_send=True, email_values={'email_to': ticket_id.responsible_id.login})
        return
