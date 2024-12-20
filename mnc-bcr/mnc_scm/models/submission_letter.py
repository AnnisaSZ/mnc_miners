from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SubmissionLetterPayment(models.Model):
    _name = 'submission.letter.payment'
    _description = 'SCM Account Payment'
    _order = 'id desc'

    def _get_sequence(self):
        sequence = self.env['ir.sequence'].next_by_code('slp.sequence')
        return sequence or '/'
    
    def _spv_finance_domain(self):
        spv_finance_domain = self.env.ref('mnc_scm.group_scm_manager_finance')
        return [('id', 'in', spv_finance_domain.users.ids)]
    
    def _manager_finance_domain(self):
        spv_finance_domain = self.env.ref('mnc_scm.group_scm_manager_finance')
        return [('id', 'in', spv_finance_domain.users.ids)]
    
    def cfo_domain(self):
        res_id = self.env.ref('mnc_scm.group_scm_cfo')
        return [('id', 'in', res_id.users.ids)]
    
    def vpdirect_domain(self):
        res_id = self.env.ref('mnc_scm.group_scm_vp_director')
        return [('id', 'in', res_id.users.ids)]
    
    def pres_direct_domain(self):
        res_id = self.env.ref('mnc_scm.group_scm_president_director')
        return [('id', 'in', res_id.users.ids)]
    
    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]
    
    name = fields.Char('No. Submission Letter', store=True, required=True, default=_get_sequence)
    po_ids = fields.Many2many('purchase.order', string='PO Number', store=True, required=True, copy=False)
    vendor_ids = fields.Many2many('res.partner', string='Vendor', store=True, copy=False, required=True)
    perihal = fields.Char('Perihal (regrading)', store=True, copy=False)
    order_line_ids = fields.One2many('submission.letter.payment.line', 'payment_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('progress', 'Payment On Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft', store=True, copy=False)

    def _get_default_company(self):
        company = self.env['res.company'].search([('name','=','Indonesia Air Transport')])
        return company if company else self.env.company

    company_id = fields.Many2one('res.company', string='Company', store=True, default=_get_default_company, domain=_company_ids_domain, required=True, copy=False)
    active = fields.Boolean('Active', store=True, default=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=lambda self: self.env.company.currency_id.id)
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')


    # Approval
    spv_finance_id = fields.Many2one('res.users', string='SPV Finance', store=True, domain=_spv_finance_domain, copy=False)
    finance_manager_id = fields.Many2one('res.users', string='Manager Finance', store=True, domain=_manager_finance_domain, copy=False)
    cfo_id = fields.Many2one('res.users', string='C.F.O', store=True, copy=False, domain=cfo_domain)
    vp_director_id = fields.Many2one('res.users', string='V.P Director', store=True, copy=False, domain = vpdirect_domain)
    president_director_id = fields.Many2one('res.users', string='President Director', store=True, copy=False, domain = pres_direct_domain)

    #approval
    approval_ids = fields.One2many(
        'slp.approval',
        'slp_id',
        string='Approval List', compute='add_approval', store=True, ondelete='cascade', copy=False
    )
    
    user_approval_ids = fields.Many2many(
        'res.users', 'approval_user_rel_slp', 'approval_id', 'user_id',
        string='Approvals', store=True, copy=False
    )

    approve_uid = fields.Many2one(
        'res.users',
        string='User Approve', store=True, readonly=True, copy=False
    )
    approval_id = fields.Many2one(
        'slp.approval',
        string='Approval', store=True, readonly=True, copy=False
    )

    is_approve_uid = fields.Boolean(compute='_check_users', store=False)
    is_spv_finance = fields.Boolean(compute='_check_users', store=False)
    reason_reject = fields.Text("Reason Rejected", store=True, copy=False)
    uid_reject = fields.Many2one('res.users', "Reason Rejected", store=True, readonly=True, copy=False)

    delivery_detail_ids = fields.One2many('shipping.detail','slp_id')
    delivery_count = fields.Integer(compute='_compute_delivery', string='Delivery count', default=0, store=True)
    delivery_ids = fields.Many2many('shipping.detail', compute='_compute_delivery', string='Delivery', copy=False, store=True)

    @api.depends('approve_uid')
    def _check_users(self):
        for rec in self:
            if rec.approve_uid == rec.env.user: 
                rec.is_approve_uid = True
            else:
                rec.is_approve_uid = False

            if rec.spv_finance_id == rec.env.user: 
                rec.is_spv_finance = True
            else:
                rec.is_spv_finance = False

    def action_done(self):
        for rec in self:
            rec.write({'state':'done'})
    
    def action_view_delivery(self):
        self.ensure_one()
        payment_ids = self.mapped('delivery_ids')
        domain = "[('id','in',%s)]" % (payment_ids.ids)

        return {
            'name': _('Shipping Detail'),
            'view_mode': 'tree,form',
            'views': [(self.env.ref('mnc_scm.delivery_detail_view_tree').id, 'tree'), (self.env.ref('mnc_scm.ship_detail_view_form').id, 'form')],
            'res_model': 'shipping.detail',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': {},
        }

    @api.depends('delivery_detail_ids')
    def _compute_delivery(self):
        for order in self:
            delivery_ids = order.delivery_detail_ids
            order.delivery_ids = delivery_ids
            order.delivery_count = len(delivery_ids)

    def action_submit_slp(self):
        for rec in self:
            if not rec.approval_ids:
                rec.add_approval()
            approval_uid = rec.approval_ids.sorted(lambda x: x.id)[0]
            mail_template = rec.env.ref('mnc_scm.notification_slp_mail_template')
            if approval_uid:
                mail_template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': approval_uid.user_id.login})
                approval_uid.update({'is_email_sent': True})
                self.update({'state': 'confirm', 'approve_uid': approval_uid.user_id.id, 'approval_id': approval_uid.id})
            rec.update({'state': 'confirm',})
            return True

    @api.depends('spv_finance_id', 'finance_manager_id', 'cfo_id', 'vp_director_id')
    def add_approval(self):
        for rec in self:
            approval_obj = self.env['slp.approval']
            if rec.spv_finance_id and rec.finance_manager_id and rec.cfo_id and rec.vp_director_id:
                user_appr_list = [rec.spv_finance_id.id, rec.finance_manager_id.id, rec.cfo_id.id, rec.vp_director_id.id]
                if rec.president_director_id:
                    user_appr_list.append(rec.president_director_id.id)
                approval_list = []
                for user_appr in user_appr_list:
                    approval_id = approval_obj.create(self.prepare_data_approval(user_appr))
                    approval_list.append(approval_id.id)
                rec.approval_ids = [(6, 0, approval_list)]
                rec.approve_uid = rec.spv_finance_id
                rec.approval_id = approval_list[0]
            else:
                rec.approval_ids = False

    def prepare_data_approval(self, user_id):
        return {
            'name': self.name,
            'user_id': user_id,
            'slp_id': self.id,
        }
    
    def send_notif_approve(self, next_approver=False):
        mail_template = self.env.ref('mnc_scm.notification_slp_mail_template')
        if next_approver:
            mail_template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': next_approver.user_id.login})
            next_approver.update({'is_email_sent': True})
        return 
    
    def send_notif_done(self):
        for orf in self:
            scm_users = self.env.ref('mnc_scm.group_scm')
            template_id = self.env.ref('mnc_scm.notification_slp_mail_template')
            user_ids = [self.spv_finance_id, self.finance_manager_id, self.cfo_id]
            # To SCM Group
            for user_id in scm_users.users:
                user_ids.append(user_id)
            # To Send
            for user in user_ids:
                template = template_id.with_context(dbname=self._cr.dbname, invited_users=user)
                template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})

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
            'res_model': 'slp.approval.wizard',
            'view_id': self.env.ref('mnc_scm.slp_approval_wizard_form').id,
            'context': {
                'default_slp_id': self.id,
                'default_company_id': self.company_id.id,
                'default_choice_signature': signature_type,
                'default_digital_signature': digital_signature,
                'default_upload_signature': upload_signature,
                'default_upload_signature_fname': upload_signature_fname,
                'default_user_approval_ids': [(6, 0, self.user_approval_ids.ids)]
            },
        }
    
    def action_sign_reject(self):
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
            'name': _("Sign & Reject"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'slp.approval.wizard',
            'view_id': self.env.ref('mnc_scm.slp_reject_view_form').id,
            'context': {
                'default_slp_id': self.id,
                'default_company_id': self.company_id.id,
                'default_choice_signature': signature_type,
                'default_digital_signature': digital_signature,
                'default_upload_signature': upload_signature,
                'default_upload_signature_fname': upload_signature_fname,
                'default_user_approval_ids': [(6, 0, self.user_approval_ids.ids)]
            },
        }
    
    def reset_to_draft(self):
        for rec in self:
            rec.write({'state':'draft'})
            rec.approval_ids.unlink()

    def generate_shipping(self):
        ship_obj = self.env['shipping.detail']
        for rec in self:
            for po in rec.po_ids:
                vals = []
                if not rec.vendor_ids:
                    raise ValidationError(_("Please Input Vendor to create comparison"))
                ship_id = ship_obj.search([('slp_id', '=', rec.id), ('po_id', '=', po.id)])
                for line in rec.order_line_ids:
                    if line.po_id == po:
                        vals.append(rec.prepare_data_shipping_detail(line))
                if ship_id:
                    ship_id.order_line_ids.unlink()
                    ship_id.write({
                            'state':'draft',
                            'order_line_ids':vals,
                        })
                else:
                    orf = self.env['order.request'].search([('pc_ids','in',(po.pc_id.ids))])
                    ship_id = ship_obj.create({
                        'partner_id':po.partner_id.id,
                        'slp_id':rec.id,
                        'po_id':po.id,
                        'orf_id':orf.id,
                        'order_line_ids':vals
                    })
        self._compute_delivery()
        return

    def prepare_data_shipping_detail(self,line):
        return (0, 0, {
            'airplane_reg': line.airplane_reg,
            'qty': line.qty,
        })
    

    @api.depends('order_line_ids.amount_total')
    def _amount_all(self):
        for order in self:
            amount = 0.0
            for line in order.order_line_ids:
               amount += line.amount_total
            order.update({
                'amount_total': amount,
            })

    @api.onchange('po_ids')
    def _onchange_po_ids(self):
        self.order_line_ids = False
        self.vendor_ids = False
        self.cfo_id = False
        self.vp_director_id = False

        po_ids = self.po_ids
        vendor = []
        vals = []
        if po_ids:
            for po_id in po_ids:
                vendor.append((4, po_id.partner_id.id))
                self.vp_director_id = po_id.vp_director_id
                for line in po_id.order_line:
                    vals.append((0, 0, {
                        'airplane_reg': line.product_description_variants,
                        'qty': line.product_qty,
                        'amount': line.price_unit,
                        'vendor_id': po_id.partner_id.id,
                        'po_id': po_id.id,
                        'po_line_id': line.id,
                    }))
            
            if vals:
                self.write({'order_line_ids': vals,
                            'vendor_ids': vendor,
                            })
                
    def action_reject(self):
        asdadlk
        for purchase in self:
            scm_users = self.env.ref('mnc_scm.group_scm_staff')
            template_id = self.env.ref('mnc_scm.notification_slp_mail_template_rejected')
            user_ids = [ self.vp_director_id, self.cfo_id, self.scm_manager_id]
            user_ids = list(set(user_ids))
            # To Send
            for user in user_ids:
                template = template_id.with_context(dbname=self._cr.dbname, invited_users=user)
                template.send_mail(self.approval_id.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})

class SubmissionLetterPaymentLine(models.Model):
    _name = 'submission.letter.payment.line'

    payment_id = fields.Many2one('submission.letter.payment', store=True)
    airplane_reg = fields.Char(string='No. Part', store=True)
    giro_cek = fields.Char(string='Metode Pembayaran', store=True)
    amount = fields.Float(string='Biaya', store=True)
    qty = fields.Float(string='Qty', store=True)
    notes = fields.Char(string='Notes', store=True)
    no_invoice = fields.Char(string='No. Invoice', store=True)
    part_dokumen = fields.Binary(
        string='Dokumen Part',
        attachment=True, store=True, copy=False
    )
    part_filename = fields.Char(
        string='Filename Part', store=True, copy=False
    )

    currency_id = fields.Many2one(related='payment_id.currency_id', store=True, string='Currency', readonly=True)
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')
    vendor_id = fields.Many2one('res.partner', string='Vendor', store=True, copy=False, required=True)
    po_id = fields.Many2one('purchase.order', string='PO Number', store=True, required=True, copy=False, force_save=True)
    po_line_id = fields.Many2one('purchase.order.line', string='PO Number', store=True, required=True, copy=False, force_save=True)
    payment_terms_id = fields.Many2one('scm.payment.term', string="Payment Terms", related="po_line_id.payment_terms_id")


    @api.constrains('part_dokumen')
    def check_attachment(self):
        for rec in self:
            if rec.part_dokumen:
                tmp = rec.part_filename.split('.')
                ext = tmp[len(tmp)-1]
                if ext not in ('pdf', 'PDF', 'png', 'PNG'):
                    raise ValidationError(_("The file must be a PDF/PNG format file"))

    @api.depends('qty', 'amount')
    def _amount_all(self):
        for rec in self:
            rec.amount_total = rec.qty*rec.amount