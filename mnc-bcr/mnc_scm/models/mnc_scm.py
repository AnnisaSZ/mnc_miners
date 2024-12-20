from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PartRequest(models.Model):
    _name = 'part.request'
    _description = 'Part Request Form'
    _order = 'id desc'

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    def _staff_store_domain(self):
        staff_store_groups = self.env.ref('mnc_scm.group_staff_store')
        return [('id', 'in', staff_store_groups.users.ids)]

    def _mtc_planner_domain(self):
        mtc_planner_groups = self.env.ref('mnc_scm.group_mtc_planner')
        return [('id', 'in', mtc_planner_groups.users.ids)]
    
    def _chief_mtc_domain(self):
        mtc_planner_groups = self.env.ref('mnc_scm.group_mtc_chief')
        return [('id', 'in', mtc_planner_groups.users.ids)]

    @api.depends('orf_ids')
    def _compute_orf(self):
        for prf in self:
            prf.orf_count = len(prf.orf_ids)

    def _get_sequence(self):
        sequence = self.env['ir.sequence'].next_by_code('prf.request')
        return sequence or '/'
    
    def _get_default_company(self):
        company = self.env['res.company'].search([('name','=','Indonesia Air Transport')])
        return company if company else self.env.company
    
    active = fields.Boolean('Active', store=True, default=True)
    name = fields.Text(string='PRF Number', size=75, store=True, copy=False, default=_get_sequence, readonly=False)
    company_id = fields.Many2one(
        'res.company',
        string='Company', store=True, default=_get_default_company, domain=_company_ids_domain, required=True, copy=False
    )
    # Created => chiefmaintenance
    chiefmaintenance = fields.Many2one('res.users', string='Chief Maintenance', store=True, required=True, domain=_chief_mtc_domain, copy=False)
    # Requestor => maintenanceplanner
    maintenanceplanner = fields.Many2one('res.users', string='Material Planner', store=True, domain=_mtc_planner_domain, default=lambda self: self.env.user, required=True, copy=False)
    staffstore = fields.Many2one('res.users', string='Staff Store', store=True, domain=_staff_store_domain, required=True, copy=False)
    request_date = fields.Date(string='Request Date', store=True, required=True, copy=False, default=fields.Date.today())
    required_before_date = fields.Selection([
        ('is_asap', 'ASAP'),
        ('non_asap', 'Non ASAP'),
     ], string='Required Before Date', default='is_asap', store=True, copy=False)
    required_before_date_string = fields.Char(string='Required Before Date', store=True, required=True, copy=False)

    priority = fields.Selection([
        ('aog', 'AOG'),
        ('urgent', 'Urgent'),
        ('normal', 'Normal'),
    ], string='Priority', default='aog', store=True, required=True, copy=False)
    part_request_ids = fields.One2many('part.request.line', 'prf_id', string='Part Number', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('store', 'Check in Store'),
        ('orf', 'ORF'),
        ('reject', 'Reject'),
    ], string='Status', default='draft', store=True, required=True, copy=False, tracking=True)
    approval_ids = fields.One2many(
        'prf.approval',
        'prf_id',
        string='Approval List', compute='add_approval', store=True, ondelete='cascade', copy=False
    )
    orf_ids = fields.One2many(
        'order.request',
        'prf_id',
        string='Orf Listed', store=True, ondelete='cascade', copy=False
    )
    orf_count = fields.Integer(compute="_compute_orf", string='ORF Count', copy=False, default=0, store=True)
    approval_id = fields.Many2one(
        'prf.approval',
        string='Approval', store=True, copy=False
    )
    next_approver_id = fields.Many2one('res.users', 'Next Approver', store=True, copy=False)

    @api.depends('maintenanceplanner', 'staffstore', 'chiefmaintenance')
    def add_approval(self):
        for prf in self:
            approval_obj = self.env['prf.approval']
            if prf.maintenanceplanner and prf.staffstore and prf.chiefmaintenance:
                user_appr_list = [prf.staffstore.id]
                approval_list = []
                for user_appr in user_appr_list:
                    approval_id = approval_obj.create(self.prepare_data_approval(user_appr))
                    approval_list.append(approval_id.id)
                prf.approval_ids = [(6, 0, approval_list)]
            else:
                prf.approval_ids = False

    def prepare_data_approval(self, user_id):
        return {
            'name': self.name,
            'user_id': user_id,
        }

    def action_sign_approve(self):
        self.ensure_one()
        if self.state == 'draft' and len(self.part_request_ids) <= 0:
            raise ValidationError(_("Please Input Part Request"))
        self.send_notif_approve(self.approval_ids[0])
        self.write({
            'state': 'store'
        })

    def action_to_orf(self):
        self.write({
            'state': 'orf'
        })

    def send_notif_approve(self, next_approver=False):
        template_id = self.env.ref('mnc_scm.notification_prf_mail_template')
        user_ids = [self.maintenanceplanner, self.chiefmaintenance, self.staffstore]
        user_ids = list(set(user_ids))
        # To Send
        for user in user_ids:
            template = template_id.with_context(dbname=self._cr.dbname, invited_users=user)
            template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})

        return True

    @api.depends('staffstore')
    def _compute_is_staffstore(self):
        for record in self:
            if record.staffstore == self.env.user:
                record.is_staffstore = True
            else:
                record.is_staffstore = False
    
    @api.depends('maintenanceplanner')
    def _compute_requestor_id(self):
        for record in self:
            if record.maintenanceplanner == self.env.user:
                record.is_create_orf = True
            else:
                record.is_create_orf = False

    is_staffstore = fields.Boolean(string="Is Approved", default=False, compute='_compute_is_staffstore', copy=False)
    is_create_orf = fields.Boolean(string="Is Approved", default=False, compute='_compute_requestor_id', copy=False)

    def action_create_orf(self):
        return {
            'name': _("ORF"),
            'type': 'ir.actions.act_window',
            'target': 'current',
            'view_mode': 'form',
            'res_model': 'order.request',
            'view_id': self.env.ref('mnc_scm.order_request_view_form').id,
            'context': self.data_orf_line()
        }

    def data_orf_line(self):
        orf_lines = self.prepare_data_orf_line()
        return {
            'default_prf_id': self.id,
            'default_requestor_id': self.maintenanceplanner,
            'default_request_date': self.request_date,
            'default_priority': self.priority,
            'default_required_before_date_string': self.required_before_date_string,
            'default_store_id': self.staffstore,
            'default_chief_mtc_id': self.chiefmaintenance,
            'default_order_request_ids': orf_lines
        }

    def prepare_data_orf_line(self):
        orf_lines = []
        for line in self.part_request_ids.filtered(lambda x: x.check_by_store and x.qty_to_order > 0):
            product = line.get_product(line.part_number)
            orf_lines.append((0, 0, {
                'prf_line_id': line.id,
                'product_tmpl_id': product.id,
                'part_number': line.part_number,
                'decription': line.decription,
                'qty_request': line.request_quantity,
                'qty_to_order': line.qty_to_order,
                'ac_reg': line.ac_reg,
                'reference': line.ipc_reference,
                'reason_for_request': line.reason_for_request,
            }))
        # if not self.part_request_ids.filtered(lambda x: not x.orf_id and x.check_by_store and x.qty_to_order > 0):
        #     raise ValidationError(_("Part Request already exist or check in your request line"))
        return orf_lines

    def action_view_orf(self, orf_ids=False):
        if not orf_ids:
            self.sudo()._read(['orf_ids'])
            orf_ids = self.orf_ids

        result = self.env['ir.actions.act_window']._for_xml_id('mnc_scm.order_request_view')
        # choose the view_mode accordingly
        if len(orf_ids) > 1:
            result['domain'] = [('id', 'in', orf_ids.ids)]
            result['context'] = {'create': 0, 'delete': 0}
        elif len(orf_ids) == 1:
            res = self.env.ref('mnc_scm.order_request_view_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = orf_ids.id
            result['context'] = {'create': 0, 'delete': 0}
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    def button_cancel(self):
        self.write({
            'state': 'reject'
        })


class PartRequestLine(models.Model):
    _name = 'part.request.line'
    _description = 'Part Request'

    orf_id = fields.Many2one('order.request', store=True, copy=False)
    part_number = fields.Char(string='Part Number', store=True, size=75, required=True, copy=False)
    decription = fields.Char(string='Description', store=True, size=75, required=True, copy=False)
    request_quantity = fields.Float(string='Qty Request', store=True, size=5, required=True, copy=False)
    qty_stock = fields.Float(string="Qty Stock", store=True, copy=False)
    qty_to_order = fields.Float('Qty Order', store=True, compute='calculate_qty', copy=False)
    ac_reg = fields.Char(string='a/c reg', store=True, size=75, required=True, copy=False)
    ipc_reference = fields.Char(string='ipc reference', store=True, size=75, copy=False)
    reason_for_request = fields.Char(string='Reason for Request', store=True, size=125, copy=False)
    part_dokumen = fields.Binary(
        string='Dokumen Part',
        attachment=True, store=True, copy=False
    )
    part_filename = fields.Char(
        string='Filename Part', store=True, copy=False
    )
    prf_id = fields.Many2one('part.request', string='prf', store=True, copy=False)
    check_by_store = fields.Boolean('Check', copy=False)

    @api.depends('qty_stock', 'request_quantity')
    def calculate_qty(self):
        for line in self:
            res_qty = line.request_quantity - line.qty_stock
            if res_qty < 0:
                res_qty = 0
            line.qty_to_order = res_qty

    def get_product(self, name):
        product_tmpl_obj = self.env['product.template']
        product_tmpl_id = self.env['product.template'].search([('name', 'ilike', name), ('is_product_scm', '=', True)], limit=1)
        if not product_tmpl_id:
            product_tmpl_id = product_tmpl_obj.create({
                'name': name,
                'is_product_scm': True,
                'taxes_id': [(6, 0, [])],
                'purchase_method': 'purchase',
                'supplier_taxes_id': [(6, 0, [])],
            })
        return product_tmpl_id
