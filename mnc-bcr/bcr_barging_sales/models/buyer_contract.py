from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, date

import logging

_logger = logging.getLogger(__name__)

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


class BuyerContract(models.Model):
    _name = "buyer.contract"
    _description = 'Buyer Contract'
    _rec_name = "no_contract"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    active = fields.Boolean('Active', store=True, default=True)
    no_contract = fields.Char('No. Contract', store=True, default="#", required=True)
    code_seq = fields.Char('Code Sequence', store=True)
    company_id = fields.Many2one('res.company', force_save='1', string='Bisnis Unit', required=True, default=lambda self: (self.env.company.id), domain=_company_ids_domain)
    buyer_id = fields.Many2one('res.partner', string="Buyer", store=True, required=True, domain="[('is_buyer', '=', True)]", tracking=True)
    contract_type = fields.Selection([
        ('Longterms', 'Longterms'),
        ('Spot', 'Spot'),
    ], default='Longterms', string='Contract Type', store=True, required=True, tracking=True)
    market_type = fields.Selection([
        ('export', 'Export'),
        ('domestic', 'Domestic'),
    ], default='export', string='Market', store=True, required=True, tracking=True)
    quantity = fields.Float('Qty Contract', store=True, required=True, tracking=True)
    percentage = fields.Integer('Qty Percentage', default=10, required=True, readonly=True, store=True)
    qty_percentage = fields.Float('Result', compute='_calc_qty_percentage')
    laycan_start = fields.Date('Laycan Start', store=True, required=True, tracking=True)
    laycan_end = fields.Date('Laycan End', store=True, required=True, tracking=True)
    product_id = fields.Many2one('product.template', string="Product", store=True, required=True, domain="[('is_marketing', '=', True)]")
    term_payment_id = fields.Many2one('buyer.term', string="Terms of Payments", store=True, required=True, domain="[('status', '=', 'active')]", tracking=True)
    details = fields.Text('Top Details', store=True, tracking=True)
    contract_start = fields.Date('Contract Start', store=True, required=True, tracking=True)
    contract_end = fields.Date('Contract End', store=True, required=True, tracking=True)
    price_type = fields.Selection([
        ('fix', 'Fix'),
        ('formula', 'Formula'),
    ], default='fix', string='Price Type', store=True, required=True, tracking=True)
    price_notes = fields.Char('Price Notes', store=True, required=True, tracking=True)
    attachment = fields.Binary('Attachments', required=True)
    filename_attachment = fields.Char('Name Attachments', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('release', 'Release'),
    ], string='Status', default='draft', store=True, required=True, copy=False, tracking=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', compute='_get_currency', store=True)
    # Rejected
    reason_reject = fields.Text("Reason Rejected", store=True)
    uid_reject = fields.Many2one('res.users', "Reason Rejected", store=True, readonly=True, tracking=True)
    contract_state = fields.Selection([
        ('open', 'Open'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], default='open', string='Status Contract', store=True, tracking=True)
    incoterms_id = fields.Many2one('master.incoterms', "Incoterms", domain="[('status', '=', 'active')]", store=True, required=True, tracking=True)
    # incoterms = fields.Selection([
    #     ('fob_barge', 'FOB Barge'),
    #     ('fob_vessel', 'FOB Vessel'),
    #     ('fas_vessel', 'FAS Vessel'),
    # ], string='Incoterms', store=True, tracking=True)

    # Approval
    spv_marketing_id = fields.Many2one('res.users', string="SPV Marketing", domain="[('company_ids', 'in', company_id)]")
    manager_marketing_id = fields.Many2one('res.users', string="Manager Marketing", domain="[('company_ids', 'in', company_id)]")
    user_approval_ids = fields.Many2many(
        'res.users', 'buyer_contract_rel', 'contract_id', 'user_id',
        string='Approvals', store=True, copy=False
    )
    approval_ids = fields.One2many('bcr.barging.approval', 'contract_id', string="Approval List", compute='add_approval', store=True)
    approve_uid = fields.Many2one('res.users', string='User Approve', store=True, readonly=True)
    approval_id = fields.Many2one(
        'bcr.barging.approval',
        string='Approval', store=True, readonly=True
    )

    # ============ Barge Data ============
    barge_detail_ids = fields.One2many('barge.detail', 'contract_id', 'Barge Details', store=True)
    total_barge = fields.Float('Total DSR', compute='_calc_total_dsr', store=True)
    total_outstanding = fields.Float('Total Outstanding', compute='_calc_total_dsr', store=True)
    is_qty_fully = fields.Boolean('Qty Fully', compute='_calc_total_dsr', store=True)
    to_be_expire = fields.Boolean('To Be Expired', store=True)

    @api.constrains('price_notes', 'price_type')
    def _check_price_notes(self):
        for buyer_contract in self:
            if buyer_contract.price_type == 'fix':
                try:
                    float(buyer_contract.price_notes)
                except ValueError:
                    raise ValidationError(_("Please Input number only in Price Notes"))

    @api.depends('barge_detail_ids', 'barge_detail_ids.dsr_volume_barge', 'barge_detail_ids.state', 'quantity', 'contract_type', 'market_type', 'state')
    def _calc_total_dsr(self):
        for buyer_contract in self:
            buyer_contract.is_qty_fully = False
            total = sum(line.dsr_volume_barge for line in buyer_contract.barge_detail_ids.filtered(lambda x: x.state == 'complete')) or 0
            qty_outstanding = buyer_contract.quantity - total
            if buyer_contract.state != 'draft':
                if buyer_contract.contract_type == 'Longterms':
                    if buyer_contract.market_type == 'export':
                        if qty_outstanding <= 50000:
                            buyer_contract.is_qty_fully = True
                    elif buyer_contract.market_type == 'domestic':
                        if qty_outstanding <= 7500:
                            buyer_contract.is_qty_fully = True
            buyer_contract.total_barge = total
            buyer_contract.total_outstanding = qty_outstanding

    @api.depends('quantity', 'percentage')
    def _calc_qty_percentage(self):
        for buyer_contract in self:
            result = 0
            if buyer_contract.quantity > 0:
                result = buyer_contract.quantity * (buyer_contract.percentage / 100)
            buyer_contract.qty_percentage = result

    @api.depends('market_type')
    def _get_currency(self):
        for buyer_contract in self:
            currency_obj = self.env['res.currency']
            if buyer_contract.market_type == 'export':
                currency_id = currency_obj.search([('name', '=', 'USD')], limit=1)
                buyer_contract.currency_id = currency_id
            else:
                currency_id = currency_obj.search([('name', '=', 'IDR')], limit=1)
                buyer_contract.currency_id = currency_id

    @api.depends('spv_marketing_id', 'manager_marketing_id')
    def add_approval(self):
        for buyer_contract in self:
            approval_obj = self.env['bcr.barging.approval']
            approval_ids = []
            if buyer_contract.spv_marketing_id and buyer_contract.manager_marketing_id:
                apps_list = [buyer_contract.spv_marketing_id.id, buyer_contract.manager_marketing_id.id]
                for approval in apps_list:
                    app_id = approval_obj.create(buyer_contract.prepare_data_approval(approval))
                    approval_ids.append(app_id.id)
            buyer_contract.approval_ids = [(6, 0, approval_ids)]

    def prepare_data_approval(self, user_id):
        data = {
            'user_id': user_id,
        }
        return data

    def action_submit(self):
        self.write({
            'state': 'release'
        })
        return

    # Update State Contract
    def action_to_done(self):
        self.write({
            'contract_state': 'done'
        })
        return

    def action_to_open(self):
        self.write({
            'contract_state': 'open'
        })
        return

    def action_to_cancel(self):
        self.write({
            'contract_state': 'cancel'
        })
        return

    def send_notif_approve(self, next_approver=False):
        mail_template = self.env.ref('bcr_barging_sales.notification_contract_approval')
        if next_approver:
            mail_template.send_mail(next_approver.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': next_approver.user_id.login})
            next_approver.update({'is_email_sent': True})
        return

    def to_approve(self):
        self.update({
            'state': 'approve',
        })
        return

    def action_revise(self):
        self.update({
            'state': 'draft',
        })
        return

    def action_reject(self):
        return {
            'name': _("Reason Rejected"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'barging.approval.wizard',
            'view_id': self.env.ref('bcr_barging_sales.barging_sales_reject_view_form').id,
        }

    # Method Combination Contract Number
    def combination_sequence_contract(self, sequence_code, company, date_contract, market_type):
        code_comp = self.env['master.bisnis.unit'].sudo().search(
            [('bu_company_id', '=', company.id)], limit=1).code
        code_month = ROMAN_NUMBER[str(date_contract.month)]
        if market_type == 'export':
            code_market = "SPA"
        elif market_type == 'domestic':
            code_market = "PJBB"
        sequence_code = sequence_code.replace('BUCODE', code_comp)
        sequence_code = sequence_code.replace('MONTH', code_month)
        sequence_code = sequence_code.replace('BUYER', self.buyer_id.kode_buyer or self.buyer_id.name)
        sequence_code = sequence_code.replace('MARKET', code_market)
        return sequence_code

    @api.model
    def create(self, vals):
        context = self.env.context
        res = super(BuyerContract, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('buyer.contract')
        res.update({"code_seq": seq})
        # Get Combination Contract Number
        # ======== Comment By Request Ahmad Daniel =====
        # ======== Mengikuti contract existing dahulu =====
        # sequence = res.combination_sequence_contract(seq, res.company_id, fields.Date.today(), res.market_type)
        # res.update({
        #     "no_contract": sequence
        # })
        # ======== ////////////////////////////////// =====
        # Create Contract from Sales Plan
        if context.get('active_model') and context.get('active_model') == 'sales.plan':
            res.update({
                "state": "release"
            })
            sales_plan_id = self.env[context.get('active_model')].browse(context.get('active_id'))
            diff_date = res.laycan_end - res.laycan_start
            if diff_date.days < 6 or diff_date.days > 2:
                sales_plan_id.update({
                    'laycan_start': res.laycan_start,
                    'laycan_end': res.laycan_end,
                })
            sales_plan_id.update({
                'contract': 'yes',
                'contract_id': res.id,
                'buyer_id': res.buyer_id.id,
                'contract_type': res.contract_type,
            })
        return res

    @api.onchange('company_id', 'market_type', 'buyer_id')
    def change_number_contract(self):
        if self.create_date:
            date_contract = self.create_date.date()
            sequence = self.combination_sequence_contract(self.code_seq, self.company_id, date_contract, self.market_type)
            self.no_contract = sequence

    @api.constrains('attachment')
    def check_attachment(self):
        for planning in self:
            if planning.attachment:
                tmp = planning.filename_attachment.split('.')
                ext = tmp[len(tmp)-1]
                if ext not in ('pdf', 'PDF'):
                    raise ValidationError(_("The file must be a PDF format file"))

    # @api.constrains('quantity', 'market_type', 'contract_type')
    # def _check_qty_contract(self):
    #     for buyer_contract in self:
    #         if buyer_contract.quantity <= 0:
    #             raise ValidationError(_("Qty Contract not <= 0"))
    #         if buyer_contract.contract_type == 'Longterms':
    #             if buyer_contract.market_type == 'export':
    #                 if buyer_contract.quantity < 50000:
    #                     raise ValidationError(_("Qty Contract musbe > 50.000"))
    #             elif buyer_contract.market_type == 'domestic':
    #                 if buyer_contract.quantity < 7500:
    #                     raise ValidationError(_("Qty Contract musbe > 7.500"))

    @api.model
    def check_exp_date(self):
        contract_ids = self.env['buyer.contract'].search([('contract_end', '>=', fields.Date.today()), ('contract_state', '=', 'open')])
        params_setting = self.env.ref('bcr_barging_sales.params_buyer_contract_1')
        if contract_ids:
            for contract_id in contract_ids:
                diff_date = contract_id.contract_end - fields.Date.today()
                if diff_date.days <= int(params_setting.value):
                    contract_id.write({'to_be_expire': True})
        return


class BuyerTerm(models.Model):
    _name = "buyer.term"
    _description = 'Buyer Terms Payments'

    active = fields.Boolean('Active', store=True, default=True)
    name = fields.Char('Terms Payment', store=True, required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], string='Status', default='active', store=True, required=True)


class MasterIncoterms(models.Model):
    _name = "master.incoterms"
    _description = 'Incoterms'

    active = fields.Boolean('Active', store=True, default=True)
    name = fields.Char('Terms Payment', store=True, required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], string='Status', default='active', store=True, required=True)
