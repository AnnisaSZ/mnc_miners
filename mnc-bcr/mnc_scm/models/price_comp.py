from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, date



class PriceComparation(models.Model):
    _name = 'price.comparation'
    _description = 'Price Comparison Form'
    _order = 'id desc'

    @api.depends('po_ids')
    def _compute_po(self):
        for pc in self:
            pc.po_count = len(pc.po_ids)

    def _get_default_company(self):
        company = self.env['res.company'].search([('name','=','Indonesia Air Transport')])
        return company if company else self.env.company
    
    company_id = fields.Many2one(
        'res.company',
        string='Company', store=True, default=_get_default_company, required=True, copy=False
    )

    def _get_sequence(self):
        sequence = self.env['ir.sequence'].next_by_code('price.comparation')
        return sequence or '/'

    name = fields.Char('Name', store=True, copy=False, default=_get_sequence)
    orf_ids = fields.Many2many('order.request', string="ORF", required=True)
    priority = fields.Selection([
        ('aog', 'AOG'),
        ('urgent', 'Urgent'),
        ('normal', 'Normal'),
    ], string='Priority', store=True)
    internal_memo = fields.Text('Internal Memo', store=True)
    summary = fields.Text('Summary', store=True)
    issued = fields.Date('Date', store=True, required=True, default=fields.Date.today())
    pc_line_ids = fields.One2many('price.comparation.line', 'pc_id', string='Order Line', store=True)
    requisition_ids = fields.One2many('purchase.requisition', 'pc_id', string='Agreement', store=True)
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('comparation', 'Comparison'),
        ('to approve', 'To Approve'),
        ('approved', 'All Approve'),
        ('purchase', 'Purchase'),
        ('cancel', 'Cancel'),
    ], default='draft', store=True)
    po_count = fields.Integer(compute="_compute_po", string='Comparison Count', copy=False, default=0, store=True)
    po_ids = fields.One2many('purchase.order', 'pc_id', string='PO', store=True)
    pr_line_ids = fields.One2many('purchase.requisition.line', 'pc_id', string='PC id', copy=False)
    ac_type = fields.Selection([
        ('legacy_600', 'LEGACY-600'),
        ('ec155b1', 'EC155B1'),
        ('atr42_500', 'ATR42-500'),
        ('general', 'GENERAL'),
        ('consumable', 'CONSUMABLE'),
        ('tools', 'TOOLS'),
    ], string='A/C Type', store=True, required=True)


    # ======================================= scm, scm manager, c.f.o, vp
    def _scm_manager_domain(self):
        res_id = self.env.ref('mnc_scm.group_scm_manager')
        return [('id', 'in', res_id.users.ids)]
    
    def cfo_domain(self):
        res_id = self.env.ref('mnc_scm.group_scm_cfo')
        return [('id', 'in', res_id.users.ids)]
    
    def vpdirect_domain(self):
        res_id = self.env.ref('mnc_scm.group_scm_vp_director')
        return [('id', 'in', res_id.users.ids)]
    
    def scmstaff_domain(self):
        res_id = self.env.ref('mnc_scm.group_scm_staff')
        return [('id', 'in', res_id.users.ids)]
    
    scm_id = fields.Many2one('res.users', string='SCM', store=True, copy=False, domain= _scm_manager_domain, required=True, default=lambda self: self.env.user)
    scm_manager_id = fields.Many2one('res.users', string='SCM Manager', store=True, copy=False, domain = _scm_manager_domain, required=True)
    cfo_id = fields.Many2one('res.users', string='C.F.O', store=True, copy=False, domain=cfo_domain, required=True)
    vp_director_id = fields.Many2one('res.users', string='V.P Director', store=True, copy=False, domain = vpdirect_domain, required=True)
    is_approved = fields.Boolean(string="Is Approved", default=True, compute='_compute_is_approved', copy=False)

    @api.depends('scm_id')
    def _compute_is_scm(self):
        for record in self:
            if record.scm_id == self.env.user:
                record.is_scm = True
            else:
                record.is_scm = False

    is_scm = fields.Boolean(string="Is Approved", default=False, compute='_compute_is_scm', copy=False)
    # =======================================
    approval_ids = fields.One2many(
        'price.approval',
        'pc_id',
        string='Approval List', compute='add_approval', store=True, ondelete='cascade', copy=False
    )
    
    user_approval_ids = fields.Many2many(
        'res.users', 'approval_user_rel_pc', 'approval_id', 'user_id',
        string='Approvals', store=True, copy=False
    )

    approve_uid = fields.Many2one(
        'res.users',
        string='User Approve', store=True, readonly=True, copy=False
    )
    approval_id = fields.Many2one(
        'price.approval',
        string='Approval', store=True, readonly=True, copy=False
    )

    is_approve_uid = fields.Boolean(compute='_check_users', store=False)

    reason_reject = fields.Text("Reason Rejected", store=True, copy=False)
    uid_reject = fields.Many2one('res.users', "Reason Rejected", store=True, readonly=True, copy=False)

    @api.depends('approve_uid')
    def _check_users(self):
        for rec in self:
            if rec.approve_uid == rec.env.user: 
                rec.is_approve_uid = True
            else:
                rec.is_approve_uid = False

    @api.depends('scm_manager_id', 'cfo_id', 'vp_director_id')
    def add_approval(self):
        for rec in self:
            approval_obj = self.env['price.approval']
            if rec.scm_manager_id and rec.cfo_id and rec.vp_director_id:
                user_appr_list = [rec.scm_manager_id.id, rec.cfo_id.id, rec.vp_director_id.id]
                approval_list = []
                for user_appr in user_appr_list:
                    approval_id = approval_obj.create(self.prepare_data_approval(user_appr))
                    approval_list.append(approval_id.id)
                rec.approval_ids = [(6, 0, approval_list)]
                rec.approve_uid = rec.scm_manager_id
                rec.approval_id = approval_list[0]
            else:
                rec.approval_ids = False

    def prepare_data_approval(self, user_id):
        return {
            'name': self.name,
            'user_id': user_id,
            'pc_id': self.id,
        }
    
    def action_to_approve(self):
        checked = self.pr_line_ids.filtered(lambda x: x.is_buy)
        if checked:
            self.approval_ids.unlink()
            self.add_approval()
            self.send_notif_approve(self.approval_id)
            self.update({'state': 'to approve',
                        })
        else:
            raise ValidationError(_("You must choose at least one part number to buy."))
        return
    
    def send_notif_approve(self, next_approver=False):
        mail_template = self.env.ref('mnc_scm.notification_pc_mail_template')
        if next_approver:
            mail_template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': next_approver.user_id.login})
            next_approver.update({'is_email_sent': True})
        else:
            if self.approval_ids:
                next_approver = self.approval_ids[0]
                mail_template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': next_approver.user_id.login})
                next_approver.update({'is_email_sent': True})
        return
    
        # for pc_id in self:
        #     scm_users = pc_id.env.ref('mnc_scm.group_scm_staff')
        #     template_id = pc_id.env.ref('mnc_scm.notification_pc_mail_template_rejected')
        #     user_ids = [pc_id.chief_mtc_id, pc_id.store_id, pc_id.create_uid, pc_id.requestor_id]
        #     user_ids = list(set(user_ids))
        #     # To Send
        #     for user in user_ids:
        #         template = template_id.with_context(dbname=self._cr.dbname, invited_users=user)
        #         template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})
    
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
            'res_model': 'pc.approval.wizard',
            'view_id': self.env.ref('mnc_scm.pc_approval_wizard_form').id,
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
            scm_users = self.env.ref('mnc_scm.group_scm_staff')
            template_id = self.env.ref('mnc_scm.approved_pc_mail_template')
            user_ids = [self.scm_manager_id, self.cfo_id, self.vp_director_id]
            # To SCM Group
            for user_id in scm_users.users:
                user_ids.append(user_id)
            user_ids = list(set(user_ids))
            # To Send
            for user in user_ids:
                template = template_id.with_context(dbname=self._cr.dbname, invited_users=user)
                template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})
    
    def action_reject(self):
        return {
            'name': _("Reason Rejected"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'pc.approval.wizard',
            'view_id': self.env.ref('mnc_scm.pc_reject_view_form').id,
            'context': {
                'default_user_approval_ids': [(6, 0, self.user_approval_ids.ids)]
            },
        }

    # =======================================

    def submit_po(self):
        for requsition in self.requisition_ids:
            requsition.create_purchase_order()
        self.update({"state": 'purchase'})
        return

    @api.onchange('orf_ids')
    def _onchange_orf_ids(self):
        self.pc_line_ids = False
        if self.orf_ids:
            for orf_id in self.orf_ids:
                self.priority = orf_id.priority
                pc_line_prep = orf_id.prepare_data_pc()
                self.update({"pc_line_ids": pc_line_prep['pc_line_ids']})
        else:
            self.pc_line_ids = False

    def create_agreement(self):
        no_vendor = self.pc_line_ids.filtered(lambda x: not x.vendor_ids)
        if no_vendor:
            raise ValidationError(_("You Must Input Vendor Name."))
        else:
            self.requisition_ids = False
            agreement_obj = self.env['purchase.requisition']
            requisition_ids = []
            for price_comp in self:
                for vendor in self.pc_line_ids.mapped('vendor_ids'):
                    vals_vendor = []
                    vals = []
                    agreement_id = agreement_obj.create({
                        'user_id': self.env.uid,
                        'pc_id': price_comp.id,
                        'type_id': self.env.ref('purchase_requisition.type_multi').id,
                        'origin': price_comp.name,
                        'vendor_id': vendor.id,
                    })

                    for item in self.pc_line_ids.filtered(lambda x: vendor in (x.vendor_ids)):
                        vals.append((0, 0, price_comp._prepare_purchase_agreement_line(item)))
                        product_id = item.product_tmpl_id.product_variant_id.id
                    vals_vendor = price_comp._prepare_section_line(vendor, product_id)

                    agreement_id.write({'line_ids': [(0, 0, vals_vendor)]})
                    agreement_id.write({'line_ids': vals})
                    requisition_ids.append(agreement_id.id)

                price_comp.write({'state': 'comparation'})
        return
       
    def _prepare_section_line(self, vendor, line):
        return {
            'display_type': 'line_section',
            'name': vendor.name,
            'product_id': line
        }

    def _prepare_purchase_agreement_line(self, line):
        product = line.get_product(line.part_number)
        line.product_tmpl_id = product
        return {
            'orf_line_id': line.orf_line_id.id,
            'product_id': product.product_variant_id.id,
            'name':line.description,
            'description':product.description,
            'product_uom_id': product.uom_id.id,
            'product_qty': line.qty,
            'qty_ordered': line.qty,
            'ac_reg': line.ac_reg,
            'product_description_variants': line.part_number,
        }

    def action_view_po(self, po_ids=False):
        if not po_ids:
            self.sudo()._read(['po_ids'])
            po_ids = self.po_ids

        result = self.env['ir.actions.act_window']._for_xml_id('mnc_scm.scm_po_views_action')
        # choose the view_mode accordingly
        if len(po_ids) > 1:
            result['domain'] = [('id', 'in', po_ids.ids)]
            result['context'] = {'create': 1, 'delete': 1}
        elif len(po_ids) == 1:
            res = self.env.ref('mnc_scm.scm_po_views_action', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = po_ids.ids
            result['context'] = {'create': 1, 'delete': 1}
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


class PriceComparationLine(models.Model):
    _name = 'price.comparation.line'
    _description = 'Price Comparation Line'

    product_tmpl_id = fields.Many2one('product.template', string="Part Number", store=True, ondelete='cascade', domain="[('is_product_scm', '=', True)]")
    orf_line_id = fields.Many2one('order.request.line', string="ORF Line", store=True, ondelete='cascade')
    vendor_ids = fields.Many2many('res.partner', 'pc_partner_rel', 'partner_id', 'pc_line_id', domain="[('is_company', '=', True),('supplier_rank', '>', 0)]", store=True)
    pc_id = fields.Many2one('price.comparation', store=True)
    part_number = fields.Char('Part Number', store=True)
    description = fields.Char('Description', store=True)
    qty = fields.Float('Qty', store=True, required=True)
    part_dokumen = fields.Binary(
        string='Dokumen Part',
        attachment=True, store=True
    )
    part_filename = fields.Char(
        string='Filename Part', store=True
    )
    ac_reg = fields.Char(string='A/C Reg.', store=True, size=75)

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    name = fields.Char(required=False)

    @api.depends('part_number')
    def change_part_number(self):
        product = self.get_product(self.part_number)
        self.product_tmpl_id = product

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
                'uom_id': 1,
            })
        product_tmpl_id.uom_id=1
        return product_tmpl_id
    
# class ProductPriceLine(models.Model):

