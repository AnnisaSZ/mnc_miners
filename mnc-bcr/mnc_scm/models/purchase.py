from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'
    _order = 'id desc'

    pc_id = fields.Many2one('price.comparation', string="Price Comparison", store=True, required=True)
    scm_id = fields.Many2one('res.users', string='SCM', store=True, copy=False, related="pc_id.scm_id", required=True)

    part_dokumen = fields.Binary(
        string='Dokumen Part',
        attachment=True, store=True, copy=False
    )
    part_filename = fields.Char(
        string='Filename Part', store=True, copy=False
    )
    
    def action_in_progress(self): 
        if self.line_ids.filtered(lambda x: x.is_buy == True):
            res = super(PurchaseRequisition, self).action_in_progress()
            if self.pc_id:
                self.write({'state': 'ongoing'})
                self.name = 'Ref: ' + self.pc_id.name
            self.create_purchase_order()
            self.action_done()
            return res
        else:
            raise ValidationError(_("Please select at least one product to buy!"))

    #replace base odoo
    def action_done(self):
        """
        Generate all purchase order based on selected lines, should only be called on one agreement at a time
        """
        for requisition in self:
            for requisition_line in requisition.line_ids:
                requisition_line.supplier_info_ids.unlink()
        self.write({'state': 'done'})

    def create_purchase_order(self):
        po_obj = self.env['purchase.order']
        vals = []
        for requisition in self:
            if not requisition.vendor_id:
                raise ValidationError(_("Please Input Vendor to create Comparison"))
            currency_id = False
            for line in requisition.line_ids:
                if line.is_buy and line.product_id.uom_id:
                    vals.append(requisition.prepare_data_purchase_order_line(line))
                currency_id = line.currency_id.id
            if requisition.line_ids.filtered(lambda x: x.is_buy == True):
                po_obj.create({
                    'partner_id':requisition.vendor_id.id,
                    'requisition_id':requisition.id,
                    'pc_id':requisition.pc_id.id,
                    'company_id':requisition.pc_id.company_id.id,
                    'origin':requisition.name,
                    'currency_id':currency_id,
                    'order_line':vals
                })
        return

    def prepare_data_purchase_order_line(self,line):
        return (0, 0, {
            'orf_line_id': line.orf_line_id.id,
            'product_qty': line.product_qty,
            'product_description_variants': line.product_description_variants,
            'name': line.product_description_variants,
            'price_unit': line.price_unit,
            'currency_id':line.currency_id.id,
            'product_uom': line.product_uom_id.id,
            'ac_reg':line.ac_reg,
            'payment_terms_id':line.payment_terms_id.id,
        })


class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    def _company_ids_domain(self):
        return [('type_tax_use','=','purchase'), ('id', '=', self.requisition_id.company_id.id)]

    currency_id = fields.Many2one('res.currency', 'Currency', store=True)
    tax_id = fields.Many2one('account.tax', 'Currency', store=True, copy=False, domain=_company_ids_domain)
    condition_product = fields.Selection([
        ('new', 'New'),
        ('repair', 'Repair')
    ], default='new', required=True, copy=False, store=True)
    note = fields.Text('Notes', store=True, copy=False, required=True)
    is_buy = fields.Boolean('Buy', store=True, copy=False)
    # fob_id = fields.Char(string="FOB")
    fob_id = fields.Char(string="FOB", related="requisition_id.vendor_id.fob")
    description = fields.Char(string="Description")
    ac_reg = fields.Char(string='A/C Reg.', store=True, size=75)
    cd_part = fields.Char(string='CD.', store=True, size=75)
    del_part = fields.Char(string='Del.', store=True, size=75)
    payment_terms_id = fields.Many2one('scm.payment.term', string="Payment Terms", domain="[('actives', '=', 'True')]", required=True)
    pc_id = fields.Many2one('price.comparation', string="Price Comparison", related="requisition_id.pc_id")
    orf_line_id = fields.Many2one('order.request.line', string="ORF Line", store=True, ondelete='cascade')

    
    partner_id = fields.Many2one(related='requisition_id.vendor_id', store=True)
    qty_ordered = fields.Float(string='Ordered Quantities')
    additional_price = fields.Float(string="Handling/Charge")

    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        for rec in self:
            rec.requisition_id.currency_id = rec.currency_id

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    name = fields.Char('Name', store=True)
    

    
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _order = 'id desc'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    
    @api.depends('scm_id')
    def _compute_is_scm(self):
        for record in self:
            if record.scm_id == self.env.user:
                record.is_scm = True
            else:
                record.is_scm = False

    is_scm = fields.Boolean(string="Is Approved", default=False, compute='_compute_is_scm', copy=False)

    active = fields.Boolean('Active', store=True, default=True)
    account_payment_ids = fields.One2many('submission.letter.payment', 'po_ids')
    pc_id = fields.Many2one('price.comparation', string="No. Price Comparison", store=True, required=True, copy=False)
    scm_id = fields.Many2one('res.users', string='SCM', store=True, copy=False, related="pc_id.scm_id")
    priority = fields.Selection([
        ('aog', 'AOG'),
        ('urgent', 'Urgent'),
        ('normal', 'Normal'),
    ], string='Priority', default='aog', related='requisition_id.pc_id.priority')
    order_date = fields.Datetime('Order Date', store=True, required=True, copy=False)
    date_order = fields.Datetime('Order Date', required=True, index=True, copy=False, default=fields.Datetime.now,
        help="Depicts the date within which the Quotation should be confirmed and converted into a purchase order.")
    fao = fields.Char('FAO', related="partner_id.fao", required=True)
    name = fields.Char('Name', required=True)
    phone_no = fields.Char('Phone No.', related='partner_id.phone')
    email = fields.Char('Email', related='partner_id.email')
    airplane_reg = fields.Char('Remarks', store=True)
    ship_to = fields.Char('Ship To', store=True, copy=False)
    orf_ids = fields.Many2many('order.request', string='No. ORF', related="pc_id.orf_ids")

    def _scm_manager_domain(self):
        res_id = self.env.ref('mnc_scm.group_scm_manager')
        return [('id', 'in', res_id.users.ids)]
    
    def cfo_domain(self):
        res_id = self.env.ref('mnc_scm.group_scm_cfo')
        return [('id', 'in', res_id.users.ids)]
    
    def vpdirect_domain(self):
        res_id = self.env.ref('mnc_scm.group_scm_vp_director')
        return [('id', 'in', res_id.users.ids)]
    
    def spv_finance_domain(self):
        res_id = self.env.ref('mnc_scm.group_scm_manager_finance')
        return [('id', 'in', res_id.users.ids)]

    scm_manager_id = fields.Many2one('res.users', string='SCM Manager', store=True, copy=False, domain = _scm_manager_domain, required=True)
    cfo_id = fields.Many2one('res.users', string='C.F.O', store=True, copy=False, domain=cfo_domain, required=True)
    vp_director_id = fields.Many2one('res.users', string='V.P Director', store=True, copy=False, domain = vpdirect_domain, required=True)
    is_approved = fields.Boolean(string="Is Approved", default=True, compute='_compute_is_approved', copy=False)
    spv_finance_id = fields.Many2one('res.users', string='SPV Finance', store=True, copy=False, domain = spv_finance_domain, required=True)
    # state = fields.Selection(selection_add=[('unpaid', 'Unpaid'), ('done', 'Shipping'), ('draft', 'Draft')])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('unpaid', 'Unpaid'),
        ('done', 'Shipping'),
        ('cancel', 'Cancelled'),

    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    # state = fields.Selection(selection_add=[('unpaid', 'Unpaid'), ('done', 'Shipping'), ('draft', 'Draft')])
    # state = fields.Selection(selection_add=[('done', 'Closed'), ('second_approval', 'To Approve SLP')])
    has_slp = fields.Boolean()
    manager_approve = fields.Boolean()
    payment_terms_id = fields.Many2one('scm.payment.term', string="Payment Terms", compute="compute_tnc", store=True)


    approval_ids = fields.One2many(
        'prf.approval',
        'po_id',
        string='Approval List', compute='add_approval', store=True, ondelete='cascade', copy=False
    )
    
    user_approval_ids = fields.Many2many(
        'res.users', 'approval_user_rel_po', 'approval_id', 'user_id',
        string='Approvals', store=True, copy=False
    )

    approve_uid = fields.Many2one(
        'res.users',
        string='User Approve', store=True, readonly=True, copy=False
    )
    approval_id = fields.Many2one(
        'prf.approval',
        string='Approval', store=True, readonly=True, copy=False
    )

    is_approve_uid = fields.Boolean(compute='_check_users', store=False)

    reason_reject = fields.Text("Reason Rejected", store=True, copy=False)
    uid_reject = fields.Many2one('res.users', "Reason Rejected", store=True, readonly=True, copy=False)

    slp_count = fields.Integer(compute='_compute_slp', string='SLP count', default=0, store=True)
    slp_ids = fields.Many2many('submission.letter.payment', compute='_compute_slp', string='SLP', copy=False, store=True)

    #Take Out SLP
    delivery_ids = fields.One2many('shipping.detail', 'po_id', string='Delivery Number', copy=False, store=True)
    delivery_count = fields.Integer(compute='_compute_delivery', string='Delivery count', default=0, store=True)

    @api.depends('account_payment_ids')
    def _compute_slp(self):
        for order in self:
            slps = order.account_payment_ids
            order.slp_ids = slps
            order.slp_count = len(slps)

    @api.depends('delivery_ids')
    def _compute_delivery(self):
        for order in self:
            count = order.delivery_ids
            order.delivery_count = len(count)

    @api.depends('approve_uid')
    def _check_users(self):
        for rec in self:
            if rec.approve_uid == rec.env.user:
                rec.is_approve_uid = True
            else:
                rec.is_approve_uid = False
            

    def action_view_slp(self):
        result = self.env["ir.actions.actions"]._for_xml_id('mnc_scm.submission_letter_view')
        # result['context'] = {'default_partner_id': self.partner_id.id, 'default_origin': self.name, 'default_picking_type_id': self.picking_type_id.id}
        payment_ids = self.mapped('slp_ids')
        if not payment_ids or len(payment_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (payment_ids.ids)
        elif len(payment_ids) == 1:
            res = self.env.ref('mnc_scm.submission_letter_view_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
        result['res_id'] = payment_ids.id
        return result

    @api.depends('scm_manager_id', 'cfo_id', 'vp_director_id')
    def add_approval(self):
        for orf in self:
            approval_obj = self.env['prf.approval']
            if orf.scm_manager_id and orf.cfo_id and orf.vp_director_id:
                user_appr_list = [orf.scm_manager_id.id, orf.cfo_id.id, orf.vp_director_id.id]
                approval_list = []
                for user_appr in user_appr_list:
                    approval_id = approval_obj.create(self.prepare_data_approval(user_appr))
                    approval_list.append(approval_id.id)
                orf.approval_ids = [(6, 0, approval_list)]
                orf.approve_uid = orf.scm_manager_id
                orf.approval_id = approval_list[0]
            else:
                orf.approval_ids = False

    def prepare_data_approval(self, user_id):
        return {
            'name': self.name,
            'user_id': user_id,
            'po_id': self.id,
        }

    def action_approval(self):
        if len(self.line_ids) == 0:
            raise ValidationError(_("Please add your item request"))
        approval_uid = self.approval_ids.sorted(lambda x: x.id)[0]
        mail_template = self.env.ref('mnc_purchase_request.notification_purchase_request_mail_template_approved')
        if approval_uid:
            mail_template.send_mail(approval_uid.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': approval_uid.user_id.login})
            approval_uid.update({'is_email_sent': True})
            self.update({'state': 'waiting', 'approve_uid': approval_uid.user_id.id, 'approval_id': approval_uid.id})
        if len(self.approval_ids) == 4:
            self.update({'approve_uid': self.spv_finance_id.id, 'approval_id': approval_uid.id})
        return True
    
    @api.onchange('spv_finance_id')
    def _onchange_spv_finance_id(self):
        if len(self.approval_ids) == 4:
            self.update({'approve_uid': self.spv_finance_id.id})
    
    def _compute_is_approved(self):
        for record in self:
            if record.approve_uid == self.env.user:
                record.is_approved = True
            else:
                record.is_approved = False
    
    def action_to_approve(self):
        if not self.approval_ids:
            self.add_approval()
        self.send_notif_approve(self.approval_id)

        self.update({'state': 'to approve',
                    })
        return
    
    def action_reset_to_draft(self):
        self.update({'state': 'draft'})
        self.approval_ids.unlink()
        self.account_payment_ids.unlink()
        return
    
    def action_sign_approve(self):
        self.ensure_one()
        # Signature Check
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
                'default_po_id': self.id,
                'default_company_id': self.company_id.id,
                'default_choice_signature': signature_type,
                'default_digital_signature': digital_signature,
                'default_upload_signature': upload_signature,
                'default_upload_signature_fname': upload_signature_fname,
                'default_user_approval_ids': [(6, 0, self.user_approval_ids.ids)]
            },
        }
    
    def send_notif_done(self):
        for orf in self:
            # scm_users = self.env.ref('mnc_scm.group_scm')
            template_id = self.env.ref('mnc_scm.notification_po_mail_template')
            user_ids = [orf.scm_manager_id, orf.user_id, orf.cfo_id]
            # To SCM Group
            # for user_id in scm_users.users:
            #     user_ids.append(user_id)
            # To Send

            # Take Out SLP
            # if len(orf.approval_ids)>3:
            #     template = template_id.with_context(dbname=self._cr.dbname, invited_users=orf.scm_manager_id)
            #     template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': orf.scm_manager_id.login})
            # else:
            for user in user_ids:
                template = template_id.with_context(dbname=self._cr.dbname, invited_users=user)
                template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})

    def send_notif_approve(self, next_approver=False):
        mail_template = self.env.ref('mnc_scm.notification_po_mail_template')
        if next_approver:
            mail_template.send_mail(next_approver.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': next_approver.user_id.login})
            next_approver.update({'is_email_sent': True})
        return True
    
    def send_notif_payment(self, approver=False):
        mail_template = self.env.ref('mnc_scm.notification_po_mail_template')
        if approver:
            mail_template.send_mail(approver.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': approver.user_id.login})
            approver.update({'is_email_sent': True})
        return True
    
    def action_reject(self):
        return {
            'name': _("Reason Rejected"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'prf.approval.wizard',
            'view_id': self.env.ref('mnc_scm.prf_reject_view_form').id,
            'context': {
                'default_user_approval_ids': [(6, 0, self.user_approval_ids.ids)]
            },
        }
    
    @api.onchange('pc_id')
    def _onchange_pc_id(self):
        requisition_id =  self.pc_id
        if requisition_id:
            requisition = requisition_id
            vals = []
            currency_id = False
            for line in requisition.pr_line_ids:
                if line.is_buy:
                    currency_id = line.currency_id.id
                    add_price = 0
                    if line.additional_price:
                        add_price = line.additional_price/line.qty_ordered
                    vals.append((0, 0, {
                        'orf_line_id': line.orf_line_id.id,
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom_id.id,
                        'product_qty': line.product_qty,
                        'product_description_variants': line.product_description_variants,
                        'price_unit': (line.price_unit+add_price),
                        'currency_id':line.currency_id.id,
                    }))
            if vals:
                self.order_line = False
                self.requisition_id = False
                self.write({'order_line': vals,
                             'partner_id': self.requisition_id.vendor_id.id,
                             'currency_id': currency_id,
                             'requisition_id': requisition_id.id,
                             'orf_ids': requisition_id.orf_ids,
                            })
        
    #hide create vendor bills and send reminder
    def fields_view_get(self, view_id=None, view_type='tree', toolbar=False, submenu=False):
        res = super(PurchaseOrder, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if not self._context.get('validate', False):
            create_bills_po = self.env.ref('purchase.action_purchase_batch_bills').id or False
            reminder_act = self.env.ref('purchase.action_purchase_send_reminder').id or False
            for button in res.get('toolbar', {}).get('action', []):
                if create_bills_po and button['id'] == create_bills_po:
                    res['toolbar']['action'].remove(button)
                if  reminder_act and button['id'] == reminder_act:
                    res['toolbar']['action'].remove(button)
            return res
        
    def approve_scm_manager(self):
        for orf in self:
            self.state='second_approval'
            approval_obj = self.env['prf.approval']
            if orf.scm_manager_id:
                user_appr_list = [orf.scm_manager_id.id]
                approval_list = []
                for user_appr in user_appr_list:
                    approval_id = approval_obj.create(self.prepare_data_approval(user_appr))
                    approval_list.append(approval_id.id)
                # orf.approval_ids = (4, approval_list[0])
                orf.approve_uid = orf.spv_finance_id
                orf.approval_id = approval_list[0]
            orf.send_notif_payment(orf.approval_id)
            orf.manager_approve = True
            # orf.generate_payment()
        
    def generate_payment(self):
        # self.approve_spv_finance()
        slp_obj = self.env['submission.letter.payment']
        vals = []
        for rec in self:
            slp_ids = slp_obj.search([('po_ids', 'in', (rec.id)), ('state', '!=', 'cancel')])
            if not slp_ids:
                for line in rec.order_line:
                    vals.append(rec.prepare_data_slp_order_line(line))
                slp_id = slp_obj.create({
                        'po_ids': [(6, 0, [rec.id])],
                        'vendor_ids':[(6, 0, [rec.partner_id.id])],
                        'company_id':rec.company_id.id,
                        'state':'draft',
                        'order_line_ids':vals,
                })

    def prepare_data_slp_order_line(self,line):
        return (0, 0, {
            'po_id': line.order_id.id,
            'vendor_id': line.order_id.partner_id.id,
            'amount': line.price_unit,
            'airplane_reg': line.product_description_variants,
            'qty':line.product_qty,
            'payment_terms_id':line.payment_terms_id.id,
            
        })
    
    def send_notif_reject(self):
        for purchase in self:
            scm_users = self.env.ref('mnc_scm.group_scm_staff')
            template_id = self.env.ref('mnc_scm.notification_po_mail_template_rejected')
            user_ids = [ self.vp_director_id, self.cfo_id, self.scm_manager_id]
            user_ids = list(set(user_ids))
            # To Send
            for user in user_ids:
                template = template_id.with_context(dbname=self._cr.dbname, invited_users=user)
                template.send_mail(self.approval_id.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})
    
    #Take Out SLP
    def generate_shipping(self):
        ship_obj = self.env['shipping.detail']
        for rec in self:
            vals = []
            orf = self.env['order.request'].search([('pc_ids','in',[rec.id])])

            for line in rec.order_line:
                vals.append(rec.prepare_data_shipping_detail(line))

            ship_id = ship_obj.create({
                'partner_id':rec.partner_id.id,
                # 'slp_id':rec.id,
                'po_id':rec.id,
                # 'orf_id':orf.id,
                'order_line_ids':vals
            })
        self._compute_delivery()
        self.write({'state':'done'})
        return

    def prepare_data_shipping_detail(self,line):
        return (0, 0, {
            'orf_line_id': line.orf_line_id.id,
            'orf_id': line.orf_line_id.orf_id.id,
            'airplane_reg': line.product_description_variants,
            'qty': line.product_qty,
            'qty_delivered': line.product_qty,
        })
    
    @api.depends('order_line','order_line.payment_terms_id')
    def compute_tnc(self):
        for rec in self:
            for line in rec.order_line:
                rec.payment_terms_id = line.payment_terms_id

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        # Ensures default picking type and currency are taken from the right company.
        self_comp = self.with_company(company_id)
        vals['name']=" "
        res = super(PurchaseOrder, self_comp).create(vals)
        return res

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    # Please Delete Constraint in SQL Database
    # "ALTER TABLE purchase_order_line DROP CONSTRAINT purchase_order_line_accountable_required_fields;"

    part_dokumen = fields.Binary(
        string='Dokumen Part',
        attachment=True, store=True
    )
    part_filename = fields.Char(
        string='Filename Part', store=True
    )
    notes = fields.Char('Notes', store=True)
    ac_reg = fields.Char(string='A/C Reg.', store=True, size=75)
    date_order = fields.Datetime(related='order_id.date_order', string='Order Date', readonly=True)
    payment_terms_id = fields.Many2one('scm.payment.term', string="Payment Terms")
    orf_line_id = fields.Many2one('order.request.line', string="ORF Line", store=True, ondelete='cascade')


    
