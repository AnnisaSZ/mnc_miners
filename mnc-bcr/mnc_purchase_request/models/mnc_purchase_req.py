from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MnceiPurchaseRequest(models.Model):
    _name = 'mncei.purchase.requisition'
    _description = 'MNCEI Purchase Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    pr_no = fields.Char(
        string='PR No.', store=True, required=True, copy=False, default='/'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company', store=True, default=lambda self: self.env.company, domain=_company_ids_domain, required=True
    )
    department_id = fields.Many2one(
        'mncei.department',
        string='Department', store=True, required=True
    )
    order_by_id = fields.Many2one(
        'mncei.employee',
        string='Order By', store=True, required=True
    )
    date_request = fields.Date('Date Required', store=True, required=True)
    eta = fields.Date('Expected Date Arrival', store=True, required=True)
    budget = fields.Selection([
        ('is_budget', 'Budgeted'),
        ('not_budget', 'Non Budget'),
    ], string='Budget', default='is_budget', store=True, required=True)
    capex = fields.Selection([
        ('is_capex', 'Capex'),
        ('not_capex', 'Non Capex'),
    ], string='Capex', default='is_capex', store=True, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approval'),
        ('procurement', 'Procurement'),
        ('approve', 'Approved'),
        ('payment', 'In Payment'),
        ('cancel', 'Cancel'),
        ('reject', 'Reject'),
    ], string='Status', default='draft', store=True, required=True, copy=False, tracking=True)
    payment_state = fields.Selection([
        ('payment', 'In Payment'),
        ('cancel', 'Cancel'),
    ], string='Payment Status', tracking=True, store=True, copy=False)
    remaks = fields.Text('Remaks', store=True)
    # Reference
    ref_mol_no = fields.Char('MOL No.', store=True)
    ref_bl_no = fields.Char('BL No.', store=True)
    ref_cn_unit = fields.Char('CN Unit', store=True)
    ref_model = fields.Char('Model', store=True)
    ref_smr = fields.Char('SMR', store=True)
    ref_date = fields.Date('Ref Date', store=True)
    pr_reason = fields.Text(
        string='Purchase Reason', store=True, required=True, copy=False
    )
    supplier = fields.Char('Nominated Supplier', store=True)

    # Approval
    requestor_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user,
        string='Requestor', store=True, required=True
    )
    head_request_id = fields.Many2one(
        'res.users',
        string='Head Requestor', store=True, required=True
    )
    head_hrga_id = fields.Many2one(
        'res.users',
        string='Head HR/GA', store=True, required=True
    )
    head_finance_id = fields.Many2one(
        'res.users',
        string='Head Finance', store=True, required=True
    )
    procurement_id = fields.Many2one(
        'res.users',
        string='Procurement', store=True, required=True
    )
    it_id = fields.Many2one(
        'res.users',
        string='Head IT', store=True
    )
    head_ga_id = fields.Many2one(
        'res.users',
        string='GA', store=True, required=True
    )
    direksi1_id = fields.Many2one(
        'res.users',
        string='Direksi Operational', store=True, required=True
    )
    direksi2_id = fields.Many2one(
        'res.users',
        string='Direksi Finance', store=True, required=True
    )
    direksi3_id = fields.Many2one(
        'res.users',
        string='Direksi', store=True, copy=False
    )
    # Set Finance
    finance_uid = fields.Many2one('res.users', "Finance", store=True, copy=False)

    line_ids = fields.One2many(
        'mncei.purchase.requisition.line',
        'request_id',
        string='Item List',
    )
    url = fields.Char(
        string='Url', compute='_get_rul', store=True, copy=False
    )
    approval_ids = fields.One2many(
        'mncei.purchase.requisition.approval',
        'pr_id',
        string='Approval List', compute='add_approval', store=True, ondelete='cascade', copy=False
    )
    finance_approval_ids = fields.Many2many(
        'mncei.purchase.requisition.approval',
        'approval_finance_rel', 'approve_id', 'pr_id',
        string='Approval List', compute='add_approval', store=True, ondelete='cascade', copy=False
    )
    user_approval_ids = fields.Many2many(
        'res.users', 'approval_user_rel', 'approval_id', 'user_id',
        string='Approvals', store=True, copy=False
    )
    total_price = fields.Integer("Total Price", compute='_compute_total_price', store=True, copy=False)
    reason_reject = fields.Text("Reason Rejected", store=True, copy=False)
    uid_reject = fields.Many2one('res.users', "Reason Rejected", store=True, readonly=True, copy=False)

    attach_ids = fields.One2many(
        'mncei.purchase.requisition.attachment',
        'pr_id',
        string='Attachment List', store=True, ondelete='cascade', copy=False
    )
    approve_uid = fields.Many2one(
        'res.users',
        string='User Approve', store=True, readonly=True, copy=False
    )
    approval_id = fields.Many2one(
        'mncei.purchase.requisition.approval',
        string='Approval', store=True, readonly=True, copy=False
    )

    @api.depends('requestor_id', 'head_request_id', 'head_ga_id', 'it_id', 'head_finance_id', 'procurement_id', 'head_hrga_id', 'direksi1_id', 'direksi2_id', 'direksi3_id')
    def add_approval(self):
        for pr in self:
            approval_obj = self.env['mncei.purchase.requisition.approval']
            if pr.approval_ids:
                approval_list = []
                if any(approval.is_email_sent for approval in pr.approval_ids):
                    for approval in pr.approval_ids.filtered(lambda x: x.is_current_user or x.user_id == self.env.user):
                        approval_list.append(approval._origin.id)
                    head_dept_list = [pr.head_hrga_id.id, pr.head_finance_id.id]
                    bod_list = [pr.direksi1_id.id, pr.direksi2_id.id]
                    # Head IT
                    if pr.it_id:
                        head_dept_list.insert(1, pr.it_id.id)
                    # Optional Direksi 3
                    if pr.direksi3_id:
                        bod_list.append(pr.direksi3_id.id)
                    # Create New
                    for res_app in head_dept_list:
                        app_id = approval_obj.create(pr.prepare_data_approval(res_app, is_head_dept=True))
                        approval_list.append(app_id.id)
                    # BOD Create Approval
                    for bod_id in bod_list:
                        app_id = approval_obj.create(pr.prepare_data_approval(bod_id, is_bod=True))
                        approval_list.append(app_id.id)
                    procurement_id = approval_obj.create(pr.prepare_data_approval(pr.procurement_id.id, is_procurement=True))
                    approval_list.append(procurement_id.id)
                    pr.approval_ids = [(6, 0, approval_list)]
                else:
                    if pr.requestor_id and pr.head_request_id and pr.head_ga_id and pr.head_finance_id and pr.procurement_id and pr.head_hrga_id and pr.direksi1_id and pr.direksi2_id:
                        bod_list = [pr.direksi1_id.id, pr.direksi2_id.id]
                        # Head Dept
                        head_dept_list = [pr.head_request_id.id, pr.head_ga_id.id, pr.head_hrga_id.id, pr.head_finance_id.id]
                        # Head IT
                        if pr.it_id:
                            head_dept_list.insert(3, pr.it_id.id)
                        # Optional Direksi 3
                        if pr.direksi3_id:
                            bod_list.append(pr.direksi3_id.id)
                        # Head Dept Create Approval
                        for res_app in head_dept_list:
                            app_id = approval_obj.create(pr.prepare_data_approval(res_app, is_head_dept=True))
                            approval_list.append(app_id.id)
                        # BOD Create Approval
                        for bod_id in bod_list:
                            app_id = approval_obj.create(pr.prepare_data_approval(bod_id, is_bod=True))
                            approval_list.append(app_id.id)
                        # Procurement
                        procurement_id = approval_obj.create(pr.prepare_data_approval(pr.procurement_id.id, is_procurement=True))
                        approval_list.append(procurement_id.id)
                        pr.approval_ids = [(6, 0, approval_list)]
            # Head User > GA > HRGA > IT (Optional) > Head Finance > BOD Operational > BOD Finance
            elif not pr.approval_ids:
                if pr.requestor_id and pr.head_request_id and pr.head_ga_id and pr.head_finance_id and pr.procurement_id and pr.head_hrga_id and pr.direksi1_id and pr.direksi2_id:
                    bod_list = [pr.direksi1_id.id, pr.direksi2_id.id]
                    # Head Dept
                    head_dept_list = [pr.head_request_id.id, pr.head_ga_id.id, pr.head_hrga_id.id, pr.head_finance_id.id]
                    approval_list = []
                    # Head IT
                    if pr.it_id:
                        head_dept_list.insert(3, pr.it_id.id)
                    # Optional Direksi 3
                    if pr.direksi3_id:
                        bod_list.append(pr.direksi3_id.id)
                    # Head Dept Create Approval
                    for res_app in head_dept_list:
                        app_id = approval_obj.create(pr.prepare_data_approval(res_app, is_head_dept=True))
                        approval_list.append(app_id.id)
                    # BOD Create Approval
                    for bod_id in bod_list:
                        app_id = approval_obj.create(pr.prepare_data_approval(bod_id, is_bod=True))
                        approval_list.append(app_id.id)
                    # Procurement
                    procurement_id = approval_obj.create(pr.prepare_data_approval(pr.procurement_id.id, is_procurement=True))
                    approval_list.append(procurement_id.id)
                    pr.approval_ids = [(6, 0, approval_list)]
            else:
                pr.approval_ids = False

    def prepare_data_approval(self, user_id, is_head_dept=False, is_bod=False, is_procurement=False):
        data = {
            'user_id': user_id,
        }
        if is_head_dept:
            data.update({
                'is_head_dept': True
            })
        if is_bod:
            data.update({
                'is_bod': True
            })
        if is_procurement:
            data.update({
                'is_procurement': True
            })
        return data

    def action_sign_approve(self):
        self.ensure_one()
        is_procurement = False
        if self.state == 'procurement':
            is_procurement = True
        # Signature Check
        signature_type = self.env.user.choice_signature
        upload_signature = False
        digital_signature = False
        if signature_type == 'upload':
            upload_signature = self.env.user.upload_signature
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
            'res_model': 'purchase.requisition.approval.wizard',
            'view_id': self.env.ref('mnc_purchase_request.mncei_pr_approval_wizard_form').id,
            'context': {'default_is_procurement': is_procurement, 'default_company_id': self.company_id.id, 'default_choice_signature': signature_type, 'default_digital_signature': digital_signature, 'default_upload_signature': upload_signature},
        }

    def open_reject(self):
        return {
            'name': _("Reason Rejected"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'purchase.requisition.approval.wizard',
            'view_id': self.env.ref('mnc_purchase_request.reject_view_form').id,
        }

    def to_payment(self):
        return {
            'name': _("To Payment"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'purchase.requisition.approval.wizard',
            'view_id': self.env.ref('mnc_purchase_request.payment_view_form').id,
            'context': {'company_id': self.company_id.id}
        }

    def action_cancel(self):
        return {
            'name': _("Cancel PR"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'purchase.requisition.approval.wizard',
            'view_id': self.env.ref('mnc_purchase_request.payment_cancel_view_form').id,
        }

    def set_draft(self):
        for line in self.approval_ids:
            line.update({
                'is_email_sent': False,
                'is_current_user': False,
                'approve_date': False,
            })
        self.update({'state': 'draft'})
        return

    @api.depends('pr_no')
    def _get_rul(self):
        for pr in self:
            config = self.env['ir.config_parameter'].sudo()
            url_link = config.get_param('web.base.url', False)
            pr.url = url_link or 'http://mncminers.com'

    def name_get(self):
        result = []
        for pr in self:
            name = pr.pr_no
            result.append((pr.id, name))
        return result

    def send_notif_approve(self, next_approver=False):
        mail_template = self.env.ref('mnc_purchase_request.notification_purchase_request_mail_template_approved')
        if next_approver:
            mail_template.send_mail(next_approver.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': next_approver.user_id.login})
            next_approver.update({'is_email_sent': True})
        return True

    def action_approval(self):
        approval_uid = self.approval_ids.sorted(lambda x: x.id)[0]
        mail_template = self.env.ref('mnc_purchase_request.notification_purchase_request_mail_template_approved')
        if approval_uid:
            mail_template.send_mail(approval_uid.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': approval_uid.user_id.login})
            approval_uid.update({'is_email_sent': True})
            self.update({'state': 'waiting', 'approve_uid': approval_uid.user_id.id, 'approval_id': approval_uid.id})
        return True

    def to_procurement(self):
        self.update({
            'state': 'procurement',
        })
        return

    def to_approve(self, finance_user, next_approver=False):
        mail_template = self.env.ref('mnc_purchase_request.notification_purchase_request_mail_finance')
        self.update({
            'state': 'approve',
            'finance_uid': finance_user.id,
        })
        mail_template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to':finance_user.login})
        next_approver.update({'is_email_sent': True})
        return

    @api.onchange('date_request', 'eta')
    def onchange_check_eta(self):
        if self.date_request and self.eta:
            if self.eta < self.date_request:
                return {'warning': {'title': _('Warning'), 'message': _("Expected Date Arrival harus lebih besar dari Date Required")}}

    @api.constrains('date_request', 'eta')
    def _check_eta(self):
        for pr in self:
            if fields.Date.today() > pr.date_request:
                raise ValidationError(_("Date Required harus lebih besar dari hari ini"))
            else:
                if pr.eta < pr.date_request:
                    raise ValidationError(_("Expected Date Arrival harus lebih besar dari Date Required"))

    @api.depends('line_ids')
    def _compute_total_price(self):
        for pr in self:
            pr.total_price = 0
            if pr.line_ids:
                pr.total_price = sum(line.est_price for line in pr.line_ids)

    def _compute_is_creator(self):
        for record in self:
            if record.requestor_id == self.env.user:
                record.is_creator = True
            else:
                record.is_creator = False

    def _compute_is_approved(self):
        for record in self:
            if record.approve_uid == self.env.user:
                record.is_approved = True
            else:
                record.is_approved = False

    def _compute_is_ga_uid(self):
        for record in self:
            if record.head_ga_id == self.env.user:
                record.is_ga_uid = True
            else:
                record.is_ga_uid = False

    def _compute_is_hr_uid(self):
        for record in self:
            if record.head_hrga_id == self.env.user:
                record.is_hr_uid = True
            else:
                record.is_hr_uid = False

    is_creator = fields.Boolean(string="Is Creator", default=True, compute='_compute_is_creator', copy=False)
    is_approved = fields.Boolean(string="Is Approved", default=True, compute='_compute_is_approved', copy=False)
    is_ga_uid = fields.Boolean(string="Is GA User", default=True, compute='_compute_is_ga_uid', copy=False)
    is_hr_uid = fields.Boolean(string="Is HR User", default=True, compute='_compute_is_hr_uid', copy=False)

    def print_pr(self):
        return self.env.ref('mnc_purchase_request.action_print_pr_new').report_action(self)


class MnceiPurchaseRequestLine(models.Model):
    _name = 'mncei.purchase.requisition.line'
    _description = 'MNCEI Purchase Requisition Line'

    request_id = fields.Many2one(
        'mncei.purchase.requisition',
        string='Request',
    )
    item_part_no_id = fields.Many2one(
        'asetkategori.module',
        string='Item Part No.', store=True, required=True
    )
    sub_categ_id = fields.Many2one(
        'sub.categ.aset',
        string='Item Part No.', store=True, required=True
    )
    sub_categ_line_id = fields.Many2one(
        'sub.categ.aset.line',
        string='Item Part No.', store=True
    )
    item_name = fields.Char(
        string='Item Name', store=True, required=True
    )
    description = fields.Char(
        string='Description', store=True, required=True
    )
    qty = fields.Integer(
        string='Qty Request', store=True, required=True
    )
    price_qty = fields.Integer(
        string='Unit Price', store=True, required=True
    )
    uom = fields.Char(
        string='UoM', store=True
    )
    est_price = fields.Integer(
        string='Est. Price', store=True, required=True
    )
    other_info = fields.Char(
        string='Other Information', store=True
    )

    @api.onchange('qty', 'price_qty')
    def change_calculate_price(self):
        if self.qty > 0 and self.price_qty > 0:
            self.est_price = self.qty * self.price_qty
        else:
            self.est_price = 0
