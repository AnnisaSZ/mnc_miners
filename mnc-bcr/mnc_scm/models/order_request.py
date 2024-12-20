from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class OrderRequest(models.Model):
    _name = 'order.request'
    _description = 'Order Request Form'
    _order = 'id desc'

    _sql_constraints = [
        ('orf_name_uniq', 'unique(name)', "The number you entered already exists. Please enter a different number."),]

    def _mtc_director_domain(self):
        mtc_groups = self.env.ref('mnc_scm.group_scm')
        return [('id', 'in', mtc_groups.users.ids)]
    
    def _chief_director_domain(self):
        mtc_groups = self.env.ref('mnc_scm.group_mtc_chief')
        return [('id', 'in', mtc_groups.users.ids)]
    
    def _mtc_planner_domain(self):
        users_search = self.env['res.users'].search([])
        users = []
        for user in users_search:
            if user.has_group('mnc_scm.group_mtc_planner') or user.has_group('mnc_scm.group_staff_store'):
                users.append(user.id)
        return [('id', 'in', users)]
        # mtc_planner_groups = self.env.ref('mnc_scm.group_mtc_planner','mnc_scm.group_staff_store')
        # return [('id', 'in', mtc_planner_groups.users.ids)]
    
    def _staff_store_domain(self):
        staff_store_groups = self.env.ref('mnc_scm.group_staff_store')
        return [('id', 'in', staff_store_groups.users.ids)]
    
    def _get_sequence(self):
        sequence = self.env['ir.sequence'].next_by_code('orf.request')
        return sequence or '/'

    @api.depends('pc_ids')
    def _compute_pc(self):
        for orf in self:
            orf.pc_count = len(orf.pc_ids)

    def _get_default_company(self):
        company = self.env['res.company'].search([('name','=','Indonesia Air Transport')])
        return company if company else self.env.company

    prf_id = fields.Many2one('part.request', string="Part Request", store=True, tracking=True, domain="[('state', '=', 'orf')]")
    name = fields.Char('ORF No.', store=True, required=True, readonly=False)
    no_repair_card = fields.Char('No. Repair Card', store=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company', store=True, default=_get_default_company)
    requestor_id = fields.Many2one('res.users', string='Request By', store=True, domain=_mtc_planner_domain)
    chief_mtc_id = fields.Many2one('res.users', string='Chief Maintenance', domain=_chief_director_domain, store=True)
    director_mtc_id = fields.Many2one('res.users', string='Maintenance Director', domain=_mtc_director_domain, store=True, required=True)
    store_id = fields.Many2one('res.users', domain=_staff_store_domain, string='Staff Store', store=True)
    order_type_id = fields.Many2one('scm.order.type', string="To Be Filled For Order Type", store=True, domain="[('actives', '=', 'True')]", required=True)
    component_serial_number = fields.Char('Us Component Serial Number', store=True)
    progress_orf = fields.Char('Status Progress', compute='_compute_progress_status', store=False)
    required_before_date = fields.Selection([
        ('is_asap', 'ASAP'),
        ('non_asap', 'Non ASAP'),
     ], string='Required Before Date', store=True)
    required_before_date_string = fields.Char(string='Required Before Date', store=True, required=True, copy=False)
    
    planning = fields.Text('Planning For', store=True)
    priority = fields.Selection([
        ('aog', 'AOG'),
        ('urgent', 'Urgent'),
        ('normal', 'Normal'),
    ], string='Priority', store=True)
    location = fields.Selection([
        ('jakarta', 'Jakarta'),
        ('banyuwangi', 'Banyuwangi'),
    ], default="jakarta", string='Location', store=True)
    request_date = fields.Date(string='Request Date', store=True, default=fields.Date.today())
    order_request_ids = fields.One2many('order.request.line', 'orf_id', string='Part Number')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approve'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ], string='Status', default='draft', store=True, required=True, copy=False, tracking=True)

    # ============================= Approval =============================
    user_approval_ids = fields.Many2many(
        'res.users', 'approval_user_scm_rel', 'approval_scm_id', 'user_id',
        string='Approvals', store=True, copy=False
    )
    approval_ids = fields.One2many(
        'prf.approval',
        'orf_id',
        string='Approval List', compute='add_approval', store=True, ondelete='cascade', copy=False
    )
    approve_uid = fields.Many2one(
        'res.users',
        string='User Approve', store=True, readonly=True, copy=False
    )
    approval_id = fields.Many2one(
        'prf.approval',
        string='Approval', store=True, readonly=True, copy=False
    )
    reason_reject = fields.Text("Reason Rejected", store=True, copy=False)
    uid_reject = fields.Many2one('res.users', "User Reject", store=True, readonly=True, copy=False)
    pc_ids = fields.Many2many(
        'price.comparation',
        string='Price Comparison', store=True, ondelete='cascade', copy=False
    )
    pc_count = fields.Integer(compute="_compute_pc", string='PC Count', copy=False, default=0, store=True)
    delivery_ids = fields.One2many(
        'shipping.detail.line',
        'orf_id',
        string='Delivery Detail', store=True, ondelete='cascade', copy=False
    )
    po_ids = fields.Many2many('purchase.order', string='No. PO', copy=False)

    revision = fields.Integer('Revision', default='1')
    original_name = fields.Char('Name')

    # Check User Approval
    is_approver = fields.Boolean(string='is approve', compute='_set_approver')

    @api.depends('po_ids', 'pc_ids', 'delivery_ids')
    def _compute_progress_status(self):
        for orf in self:
            state = 'ORF'
            if orf.delivery_ids:
                state = 'Delivery' 
            elif orf.po_ids.account_payment_ids:
                state = 'Submission Letter Payment' 
            elif orf.po_ids:
                state = 'Purchase Order' 
            elif orf.pc_ids:
                state = 'Price Comparison'
            orf.progress_orf = state

    @api.depends('requestor_id')
    def _compute_is_scm(self):
        for record in self:
            if record.requestor_id == self.env.user:
                record.is_scm = True
            else:
                record.is_scm = False

    is_scm = fields.Boolean(string="Is Approved", default=False, compute='_compute_is_scm', copy=False)


    # ========================================================================
    def _set_approver(self):
        for sales_plan in self:
            if self.env.uid == self.approve_uid.id:
                sales_plan.is_approver = True
            else:
                sales_plan.is_approver = False
    # ========================================================================

    @api.depends('chief_mtc_id', 'store_id', 'director_mtc_id', 'requestor_id')
    def add_approval(self):
        for orf in self:
            orf.approval_ids = False
            approval_obj = self.env['prf.approval']
            if orf.chief_mtc_id and orf.director_mtc_id and orf.store_id:
                user_appr_list = [orf.store_id.id, orf.chief_mtc_id.id, orf.director_mtc_id.id]
                approval_list = []
                for user_appr in user_appr_list:
                    approval_id = approval_obj.create(self.prepare_data_approval(user_appr))
                    approval_list.append(approval_id.id)
                orf.approval_ids = [(6, 0, approval_list)]
            else:
                orf.approval_ids = False

    def prepare_data_approval(self, user_id):
        return {
            'name': self.name,
            'user_id': user_id,
        }

    def action_submit(self):
        if not self.order_request_ids:
                raise ValidationError(_("Part Request cannot be blank."))
        if not self.required_before_date_string:
                raise ValidationError(_("Required Before Date cannot be blank."))
        self.send_notif_approve()
        self.update({'state': 'waiting', 'approve_uid': self.approval_ids[0].user_id.id, 'approval_id': self.approval_ids[0].id})
        return

    def send_notif_approve(self, next_approver=False):
        mail_template = self.env.ref('mnc_scm.notification_orf_mail_template')
        if next_approver:
            mail_template.send_mail(next_approver.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': next_approver.user_id.login})
            next_approver.update({'is_email_sent': True})
        else:
            if self.approval_ids:
                next_approver = self.approval_ids[0]
                mail_template.send_mail(next_approver.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': next_approver.user_id.login})
                next_approver.update({'is_email_sent': True})
        return
    
    def send_notif_reject(self, next_approver=False):
        for orf in self:
            scm_users = self.env.ref('mnc_scm.group_scm_staff')
            template_id = self.env.ref('mnc_scm.notification_orf_mail_template_rejected')
            user_ids = [self.chief_mtc_id, self.store_id, self.create_uid, self.requestor_id]
            user_ids = list(set(user_ids))
            # To Send
            for user in user_ids:
                template = template_id.with_context(dbname=self._cr.dbname, invited_users=user)
                template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})

    def send_notif_done(self):
        for orf in self:
            scm_users = self.env.ref('mnc_scm.group_scm_staff') + self.env.ref('mnc_scm.group_scm_manager')
            template_id = self.env.ref('mnc_scm.approved_orf_mail_template')
            user_ids = [self.chief_mtc_id, self.store_id, self.requestor_id]
            # To SCM Group
            for user_id in scm_users.users:
                user_ids.append(user_id)
            user_ids = list(set(user_ids))
            # To Send
            for user in user_ids:
                template = template_id.with_context(dbname=self._cr.dbname, invited_users=user)
                template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})

    def action_sign_approve(self):
        self.ensure_one()
        signature_type = self.env.user.choice_signature
        upload_signature = False
        digital_signature = False
        upload_signature_fname = ''
        if signature_type == 'upload':
            upload_signature = self.env.user.upload_signature
            upload_signature_fname = self.env.user.upload_signature_fname
            if not upload_signature:
                raise ValidationError(_("Please add your signature in Click Your name in Top Right > Preference > Signature"))
        elif signature_type == 'draw':
            digital_signature = self.env.user.digital_signature
            if not digital_signature:
                raise ValidationError(_("Please add your signature in Click Your name in Top Right > Preference > Signature"))
        else:
            raise ValidationError(_("Please add your signature in Click Your name in Top Right > Preference > Signature"))
        return {
            'name': _("Sign & Approve"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'prf.approval.wizard',
            'view_id': self.env.ref('mnc_scm.prf_approval_wizard_form').id,
            'context': {
                'default_choice_signature': signature_type,
                'default_digital_signature': digital_signature,
                'default_upload_signature': upload_signature,
                'default_upload_signature_fname': upload_signature_fname,
                'default_user_approval_ids': [(6, 0, self.user_approval_ids.ids)]
            },
        }

    def action_reject(self):
        self.ensure_one()
        return {
            'name': _("Reject Reason"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'prf.approval.wizard',
            'view_id': self.env.ref('mnc_scm.prf_reject_view_form').id,
            'context': {
                'default_user_approval_ids': [(6, 0, self.user_approval_ids.ids)]
            },
        }

    def action_create_pc(self):
        self.ensure_one()
        return {
            'name': _("Price Comparison"),
            'type': 'ir.actions.act_window',
            'target': 'current',
            'view_mode': 'form',
            'res_model': 'price.comparation',
            'view_id': self.env.ref('mnc_scm.price_comp_view_form').id,
            
            # 'context': {'default_orf_id': self.id,}
            'context': self.prepare_data_pc()
        }

    def button_cancel(self):
        return {
            'name': _("Cancel Reason"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'prf.approval.wizard',
            'view_id': self.env.ref('mnc_scm.orf_cancel_view_form').id,
            'context': {
                'default_user_approval_ids': [(6, 0, self.user_approval_ids.ids)]
            },
        }


    def action_cancel(self):
        if self.prf_id:
            self.prf_id.button_cancel()    
        self.update({'state': 'reject'})
        if not self.original_name:
            self.original_name = self.name
        name = self.original_name + ' REV0' + str(self.revision)
        prf = False
        if self.prf_id:
            prf = self.prf_id.id
        self.env['order.request'].create({
            'name': name,
            'prf_id': prf,
            'requestor_id': self.requestor_id.id,
            'request_date': self.request_date,
            'location': self.location,
            'no_repair_card': self.no_repair_card,
            'required_before_date_string': self.required_before_date_string,
            'priority': self.priority,
            'order_type_id': self.order_type_id.id,
            'component_serial_number': self.component_serial_number,
            'store_id': self.store_id.id,
            'director_mtc_id': self.director_mtc_id.id,
            'chief_mtc_id': self.chief_mtc_id.id,
            'revision': self.revision + 1,
            'original_name': self.original_name,
            'order_request_ids': self.prepare_data_orf_line(),
        })        
    
    def prepare_data_orf_line(self):
        orf_lines = []
        for line in self.order_request_ids:
            product = line.get_product(line.part_number)
            prf_id = False
            if line.prf_line_id:
                prf_id = line.prf_line_id.id
            orf_lines.append((0, 0, {
                'product_tmpl_id': product.id,
                'prf_line_id': prf_id,
                'part_number': line.part_number,
                'decription': line.decription,
                'qty_request': line.qty_request,
                'ac_reg': line.ac_reg,
                'reference': line.reference,
                'reason_for_request': line.reason_for_request,
                'remarks': line.remarks,
                'order_type_id': line.order_type_id.id,
                'qty_to_order': line.qty_to_order,
            }))
        # if not self.part_request_ids.filtered(lambda x: not x.orf_id and x.check_by_store and x.qty_to_order > 0):
        #     raise ValidationError(_("Part Request already exist or check in your request line"))
        return orf_lines
    
    def set_draft(self):
        for line in self.approval_ids:
            line.update({
                'is_email_sent': False,
                'is_current_user': False,
                'approve_date': False,
                'notes': "",
            })
        self.update({'state': 'draft'})
        return

    def prepare_data_pc(self):
        pc_lines = []
        # for line in self.order_request_ids.filtered(lambda x: x.order_type == 'buy' and x.qty_to_order > 0):
        for line in self.order_request_ids.filtered(lambda x: x.qty_to_order > 0):
            pc_lines.append((0, 0, {
                'part_number': line.part_number,
                'description': line.decription,
                'name': line.decription,
                'orf_line_id': line.id,
                'product_tmpl_id': line.product_tmpl_id.id,
                'qty': line.qty_to_order,
                'ac_reg': line.ac_reg,
            }))
        if not self.order_request_ids.filtered(lambda x: x.qty_to_order > 0):
        # if not self.order_request_ids.filtered(lambda x: x.order_type == 'buy' and x.qty_to_order > 0):
            raise ValidationError(_("All Part Request already have ORF"))
        return {'default_orf_ids': [self.id],
                'default_company_id': self.company_id.id,
                'pc_line_ids': pc_lines,
            }

    def action_view_pc(self, pc_ids=False):
        if not pc_ids:
            self.sudo()._read(['pc_ids'])
            pc_ids = self.pc_ids

        result = self.env['ir.actions.act_window']._for_xml_id('mnc_scm.price_comp_view')
        # choose the view_mode accordingly
        if len(pc_ids) > 1:
            result['domain'] = [('id', 'in', pc_ids.ids)]
            result['context'] = {'create': 1, 'delete': 0}
        elif len(pc_ids) == 1:
            res = self.env.ref('mnc_scm.price_comp_view_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = pc_ids.id
            result['context'] = {'create': 1, 'delete': 0}
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.onchange('prf_id')
    def _change_request_line(self):
        self.order_request_ids = False
        if self.prf_id:
            orf_line = self.prf_id.prepare_data_orf_line()
            self.requestor_id = self.prf_id.maintenanceplanner
            self.request_date = self.prf_id.request_date
            self.priority = self.prf_id.priority
            self.required_before_date_string = self.prf_id.required_before_date_string
            self.store_id = self.prf_id.staffstore
            self.chief_mtc_id = self.prf_id.chiefmaintenance

            self.order_request_ids = orf_line

    # @api.model
    # def create(self, vals):
    #     res = super(OrderRequest, self).create(vals)
    #     seq = res._get_sequence()
    #     res.update({"name": seq})
    #     return res


class OrderRequestLine(models.Model):
    _name = 'order.request.line'
    _description = 'Order Request Line'

    prf_line_id = fields.Many2one('part.request.line', store=True, required=False)
    orf_id = fields.Many2one('order.request', store=True)
    pc_id = fields.Many2one('price.comparation', store=True)
    product_tmpl_id = fields.Many2one('product.template', store=True, ondelete='cascade', domain="[('is_product_scm', '=', True)]")
    product_id = fields.Many2one('product.product', related="product_tmpl_id.product_variant_id")
    part_number = fields.Char(string='Part Number', store=True, size=75)
    decription = fields.Char(string='Description', store=True, size=75)
    remarks = fields.Char(string='Remarks', store=True, size=75)
    qty_request = fields.Float(string="Qty Request", store=True, readonly=False, required=True)
    reference = fields.Char(string="IPC Reference", store=True, readonly=False, required=True)
    ac_reg = fields.Char(string='A/C Reg.', store=True, size=75, required=True,readonly=False)
    reason_for_request = fields.Char(string='Reason for Request', required=True, store=True, size=125)
    order_type_id = fields.Many2one('scm.order.type', string="Order Type", store=True, domain="[('actives', '=', 'True')]", required=True)
    qty_to_order = fields.Float('Qty Order', store=True, required=True)
    part_dokumen = fields.Binary(
        string='Dokumen Part',
        attachment=True, store=True
    )
    part_filename = fields.Char(
        string='Filename Part', store=True
    )

    @api.model
    def create(self, vals):
        res = super(OrderRequestLine, self).create(vals)
        if res.prf_line_id:
            res.prf_line_id.update({'orf_id': res.orf_id.id})
        return res
    
    @api.depends('part_number')
    def change_part_number(self):
        product = self.get_product(self.part_number)
        self.product_tmpl_id = product

    def get_product(self, name):
        product_tmpl_obj = self.env['product.template']
        product_tmpl_id = self.env['product.template'].search([('name', '=', name), ('is_product_scm', '=', True)], limit=1)
        if not product_tmpl_id:
            product_tmpl_id = product_tmpl_obj.create({
                'name': name,
                'is_product_scm': True,
                'taxes_id': [(6, 0, [])],
                'purchase_method': 'purchase',
                'supplier_taxes_id': [(6, 0, [])],
            })
        product_tmpl_id.uom_id = 1
        return product_tmpl_id
