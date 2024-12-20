from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from datetime import datetime

ROMAN_NUMBER = {
    '1': 'I',
    '2': 'II',
    '3': 'III',
    '4': 'IV',
    '5': 'V',
    '6': 'VI',
    '7': 'VII',
    '8': 'VIII',
    '9': 'IX',
    '10': 'X',
    '11': 'XI',
    '12': 'XII',
}

class ShippingDetail(models.Model):
    _name = 'shipping.detail'
    _inherit = ['mail.thread', 'mail.activity.mixin'] 
    _description = 'Shipping Detail'
    _order = 'id desc'

    def _get_sequence(self):
        sequence = self.env['ir.sequence'].sudo().next_by_code('ship.deliv.sequence')
        code_month = ROMAN_NUMBER[str(datetime.now().month)]
        sequence = sequence.replace('CUSTOMCODE', code_month)
        return sequence or '/'
    
    def _get_default_company(self):
        company = self.env['res.company'].search([('name','=','Indonesia Air Transport')])
        return company if company else self.env.company

    name = fields.Char('Name', store=True, copy=False, default=_get_sequence)
    company_id = fields.Many2one(
        'res.company',
        string='Company', store=True, default=_get_default_company, required=True, copy=False
    )
    po_id = fields.Many2one('purchase.order', string='PO Number', copy=False, store=True)
    slp_id = fields.Many2one('submission.letter.payment', string='SLP Number', copy=False, store=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', copy=False, store=True)
    etd = fields.Date(string='ETD', copy=False, store=True)
    eta = fields.Date(string='ETA', copy=False, store=True)
    location = fields.Char(string="Country", copy=False, store=True, tracking=True)
    status_shipment_id = fields.Many2one('status.shipment', string='Status Shipment', store=True, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_deliv', 'To Delivery'),
        ('confirm', 'Delivery Confirm'),
        ('receive', 'Received'),
        ('checking', 'Check Part'),
        ('done', 'Distribution Part'),
        ('cancel', 'Return Part'),
        ('claim', 'Claim To Vendor'),
    ], string='State', default='draft', store=True, copy=False, track_visibility='onchange')
    notes = fields.Char(string="Notes", copy=False, store=True)
    part_dokumen = fields.Binary(
        string='Dokumen Part',
        attachment=True, store=True, copy=False
    )
    part_filename = fields.Char(
        string='Filename Part', store=True, copy=False
    )
    receive_date = fields.Date(string="Receiving Date", default=fields.Datetime.now, store=True, copy=False)
    checking_result = fields.Char(string="Checking Result", store=True, copy=False)
    order_line_ids = fields.One2many('shipping.detail.line','order_id', copy=False, store=True)
    scm_id = fields.Many2one('res.users', string='SCM', copy=False, related='orf_id.requestor_id')
    scm_manager_id = fields.Many2one('res.users', string='SCM Manager', copy=False, related='orf_id.store_id')
    store_id = fields.Many2one('res.users', string='Store', copy=False, related='orf_id.store_id')
    chief_mtc_id = fields.Many2one('res.users', string='Chief Maintenance', copy=False, related='orf_id.chief_mtc_id')

    @api.depends('scm_id')
    def _compute_is_scm(self):
        for record in self:
            if record.scm_id == self.env.user:
                record.is_scm = True
            else:
                record.is_scm = False

    is_scm = fields.Boolean(string="Is Approved", default=False, compute='_compute_is_scm', copy=False)

    @api.depends('is_qa')
    def _compute_is_qa(self):
        for record in self:
            if record.qa_id == self.env.user:
                record.is_qa = True
            else:
                record.is_qa = False

    is_qa = fields.Boolean(string="Is Approved", default=False, compute='_compute_is_qa', copy=False)
    
    def qa_domain(self):
        qa_domain = self.env.ref('mnc_scm.group_scm_qa')
        return [('id', 'in', qa_domain.users.ids)]
    
    qa_id = fields.Many2one('res.users', string='Quality Assurance', copy=False, domain=qa_domain)
    orf_id = fields.Many2one('order.request', string="ORF", store=True, copy=False)
    orf_ids = fields.Many2many('order.request', string="ORF List", compute="compute_orf_ids", store=True)

    @api.depends('order_line_ids', 'order_line_ids.orf_id')
    def compute_orf_ids(self):
        for rec in self:
            rec.orf_ids = rec.order_line_ids.mapped('orf_id')

    def to_confirm(self):
        for rec in self:
            scm_users = self.env.ref('mnc_scm.group_scm_staff')
            template_id = self.env.ref('mnc_scm.notification_shipping_mail_template')
            user_ids = [self.po_id.scm_manager_id, self.qa_id]
            # To SCM Group
            for user_id in scm_users.users:
                user_ids.append(user_id)
            # Get user in ORF
            for user_id in self.po_id.orf_ids:
                user_ids.append(user_id.store_id)
                user_ids.append(user_id.requestor_id)
            user_ids = list(set(user_ids))
            # To Send
            for user in user_ids:
                template = template_id.with_context(dbname=self._cr.dbname, invited_users=user)
                template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})
            rec.update({'state': 'confirm',})

    def to_delivery(self):
        for rec in self:
            rec.update({'state': 'to_deliv',})

    def to_receipt(self):
        for rec in self:
            rec.update({
                        'state': 'receive',
                        'receive_date': datetime.now(),
                        })

    def return_product(self):
        for rec in self:
            scm_users = self.env.ref('mnc_scm.group_scm_staff')
            template_id = self.env.ref('mnc_scm.notification_return_vendor_mail_template')
            user_ids = []
            # To SCM Group
            for user_id in scm_users.users:
                user_ids.append(user_id)
            user_ids = list(set(user_ids))
            # To Send
            for user in user_ids:
                template = template_id.with_context(dbname=self._cr.dbname, invited_users=user)
                template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})
            rec.update({'state': 'cancel',})

    def action_distribute(self):
        for rec in self:
            # mail_template = self.env.ref('mnc_scm.notification_shipping_mail_template')
            # mail_template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': next_approver.user_id.login})
            rec.update({'state': 'done',})

    def action_claim(self):
        for rec in self:
            scm_users = self.env.ref('mnc_scm.group_scm_staff')
            template_id = self.env.ref('mnc_scm.notification_warranty_claim_mail_template')
            user_ids = []
            # To SCM Group
            for user_id in scm_users.users:
                user_ids.append(user_id)
            # Get user in ORF
            for user_id in self.po_id.orf_ids:
                user_ids.append(user_id.store_id)
            user_ids = list(set(user_ids))
            # To Send
            for user in user_ids:
                template = template_id.with_context(dbname=self._cr.dbname, invited_users=user)
                template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})
            rec.update({'state': 'claim',})
    
    def reset_to_draft(self):
        for rec in self:
            rec.update({'state': 'draft',})

    @api.onchange('po_id')
    def _onchange_po_id(self):
        po_id = self.po_id
        if po_id:
            orf_id = self.env['order.request'].search([('pc_ids','in',(self.po_id.pc_id.ids))])
            partner_id = self.po_id.partner_id
            slp_id = self.po_id.slp_ids
            self.order_line_ids = False
            vals = []
            for line in po_id.order_line:
                vals.append((0, 0, {
                    'airplane_reg': line.product_id.name,
                    'ac_reg': line.order_id.airplane_reg,
                    'qty': line.product_qty,
                }))
            if vals:
                self.write({'order_line_ids': vals,
                             'po_id': po_id.id,
                             'orf_id': orf_id.id,
                             'partner_id': partner_id.id,
                             'slp_id': slp_id.id,
                             })
        else:
            self.orf_id = False
            self.partner_id = False
            self.slp_id = False
            self.order_line_ids.unlink()


class ShippingDetailLine(models.Model):
    _name = 'shipping.detail.line'
    _description = 'Shipping Detail Line'

    order_id = fields.Many2one('shipping.detail')    
    orf_id = fields.Many2one('order.request', string='No. ORF')    
    orf_line_id = fields.Many2one('order.request.line', string='No. ORF')    
    airplane_reg = fields.Char(string='No. Part', store=True, required=True)
    ac_reg = fields.Char(string='A/C Reg', related='orf_line_id.ac_reg')
    qty = fields.Float(string='Quantity', store=True, copy=False, required=True)
    qty_delivered = fields.Float(string='Quantity Delivered', default=0, store=True, copy=False, required=True)
    notes = fields.Char(string='Notes', store=True, copy= False)

class StatusShipment(models.Model):
    _name = 'status.shipment'
    _description = 'status shipment'

    name = fields.Char(string='Name', store=True, copy=False)
    active = fields.Boolean(default='True', store=True, string="Status")
    shipment_detail_ids = fields.One2many('shipping.detail', 'status_shipment_id', string='Shipment detail', copy=False)
    