from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, date

import calendar
import logging

_logger = logging.getLogger(__name__)

MONTH_SELECTION = [
    ('1', 'January'),
    ('2', 'February'),
    ('3', 'March'),
    ('4', 'April'),
    ('5', 'May'),
    ('6', 'June'),
    ('7', 'July'),
    ('8', 'August'),
    ('9', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December')
]


class SalesPlan(models.Model):
    _name = "sales.plan"
    _description = 'Sales Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    def set_validation(self):
        result = False
        bu_id = self.env.company.id
        if bu_id:
            ####
            validation = self.env['validation.validation'].search([
                ('model_id.model', '=', self._name),
                ('bu_company_id', '=', bu_id)], limit=1)
            vals = []

            if validation:
                for rec in validation.validation_line:
                    vals.append((0, 0, {
                        'user_id': rec.user_id.id,
                        'validation_type_id': rec.validation_type_id.id,
                    }))
            else:
                raise UserError('Validation untuk Form Sales Plan belum disetting')
            result = vals
        return result

    def _contract_domain(self):
        return [('state', '=', 'release'), ('contract_state', '=', 'open'), ('company_id', '=', )]

    def _category_domain(self):
        return [('period_id.name', 'ilike', 'yearly'), ('status', '=', 'active')]

    # Filter Data
    planning_type = fields.Selection([
        ('Yearly', 'Yearly'),
        ('Monthly', 'Monthly'),
    ], string='Type Period', default='Yearly', store=True)
    date_start = fields.Date(string='Date Start')
    date_end = fields.Date(string='Date End')
    period_month = fields.Selection(
        selection=MONTH_SELECTION,
        string='Month',
        help='Select the desired month',
        store=True
    )
    selected_years = fields.Selection(selection='_get_year_selection', string='Years', store=True)
    category_id = fields.Many2one('planning.type.option', string='Type', domain=_category_domain, store=True)
    plan_company_ids = fields.Many2many('res.company', string='Bisnis Unit')
    plan_attach_ids = fields.One2many('sales.plan.attachment', 'sales_plan_id', string='Attachment')

    @api.onchange('planning_type')
    def onchange_type_planning(self):
        if self.planning_type == 'Yearly':
            return {'domain': {'category_id': [('period_id.name', 'ilike', 'yearly'), ('status', '=', 'active')]}}
        if self.planning_type == 'Monthly':
            return {'domain': {'category_id': [('period_id.name', 'ilike', 'monthly'), ('status', '=', 'active')]}}

    # To Get Value Year
    def _get_year_selection(self):
        current_year = date.today().year
        year_range = [(str(year), str(year)) for year in range(current_year, current_year + 5)]
        return year_range

    # Result
    result = fields.Float('Result', store=True)
    result_plan_ids = fields.One2many('result.plan.production', 'plan_id', string='Result')

    def categroy_product(self):
        categ_ids = self.env['category.type.coal'].search([('state', '=', 'active')])
        return categ_ids

    @api.onchange('planning_type', 'date_start', 'date_end', 'period_month', 'selected_years', 'plan_company_ids', 'category_id')
    def calculate_result_plan(self):
        for sales_plan in self:
            self.result_plan_ids = False
            # total_days = 0
            values = []
            # Search Category
            categ_ids = sales_plan.categroy_product()
            if sales_plan.selected_years:
                # Deleted if value
                if self.planning_type == 'Yearly':
                    self.period_month = False
                    if self.category_id:
                        if self.category_id.period_id.name != 'Yearly':
                            self.category_id = False
                elif self.planning_type == 'Monthly':
                    if self.category_id:
                        if self.category_id.period_id.name != 'Monthly':
                            self.category_id = False
                # ================ Search and Calculate ==========
                if sales_plan.plan_company_ids:
                    domain = [('company_id', 'in', sales_plan.plan_company_ids.ids), ('selected_years', '=', sales_plan.selected_years)]
                    period_month = False
                    # Jika Dipilih bulan
                    if sales_plan.period_month:
                        period_month = sales_plan.period_month
                        start_date_plan, end_date_plan = sales_plan._get_total_days_in_month(sales_plan.period_month, sales_plan.selected_years)
                        workdays_in_month = (end_date_plan - start_date_plan).days + 1
                        plan_list = sales_plan._get_planning_production(sales_plan.planning_type, domain, start_date_plan, end_date_plan)
                    # Jika setting bulan kerja berdasarkan date period
                    elif sales_plan.date_start or sales_plan.date_end and not sales_plan.period_month:
                        period_month = False
                        if sales_plan.date_start.month == sales_plan.date_end.month:
                            if sales_plan.date_start:
                                period_month = str(sales_plan.date_start.month)
                            elif sales_plan.date_end:
                                period_month = str(sales_plan.date_end.month)
                            start_date_plan, end_date_plan = sales_plan._get_total_days_in_month(period_month, sales_plan.selected_years)
                            workdays_in_month = (end_date_plan - start_date_plan).days + 1
                            plan_list = sales_plan._get_planning_production(sales_plan.planning_type, domain, start_date_plan, end_date_plan)
                        else:
                            # Loop while
                            plan_list = []
                            if sales_plan.date_start and sales_plan.date_end:
                                i = sales_plan.date_start.month
                                end = (sales_plan.date_end.month + 1)
                                workdays_in_month = 0
                                while i < end:
                                    workdays_in_month += (sales_plan.check_days(int(sales_plan.selected_years), i)[1])
                                    start_date, end_date = sales_plan._get_total_days_in_month(i, sales_plan.selected_years)
                                    if plan_list:
                                        plan_list += sales_plan._get_planning_production(sales_plan.planning_type, domain, start_date, end_date)
                                    else:
                                        plan_list = sales_plan._get_planning_production(sales_plan.planning_type, domain, start_date, end_date)
                                    i += 1
                            # else:
                            #     if sales_plan.date_start:
                            #         start_date_plan = sales_plan.date_start
                            #         total_days_date_start = (sales_plan.check_days(int(sales_plan.selected_years), int(sales_plan.date_start.month))[1])
                            #         # Search Planning in Period Month Start Date
                            #         start_date, end_date = sales_plan._get_total_days_in_month(start_date_plan.month, sales_plan.selected_years)
                            #         plan_list = sales_plan._get_planning_production(sales_plan.planning_type, domain, start_date, end_date)
                            #     if sales_plan.date_end:
                            #         end_date_plan = sales_plan.date_end
                            #         total_days_date_end = (sales_plan.check_days(int(sales_plan.selected_years), int(end_date_plan.month))[1])
                            #         # Search Planning in Period Month End Date
                            #         start_date, end_date = sales_plan._get_total_days_in_month(end_date_plan.month, sales_plan.selected_years)
                            #         plan_list += sales_plan._get_planning_production(sales_plan.planning_type, domain, start_date, end_date)
                            #     workdays_in_month = total_days_date_start + total_days_date_end

                    if sales_plan.planning_type == 'Yearly':
                        # Split data by Category Coal
                        total_volume_gar = sales_plan._get_split_data_volume(categ_ids, plan_list, workdays_in_month)
                        # To Prepare Data result split by category
                        for total_vol in total_volume_gar:
                            data = sales_plan._prepare_data_result(total_volume_gar, total_vol)
                            values.append(data)
                    else:
                        total_volume_gar = sales_plan._get_split_data_volume(categ_ids, plan_list, 1)
                        # To Prepare Data result split by category
                        for total_vol in total_volume_gar:
                            data = sales_plan._prepare_data_result(total_volume_gar, total_vol)
                            values.append(data)

            sales_plan.result_plan_ids = values

    # Search Record Planning
    def _get_planning_production(self, type_plan, domain, start_date_in_month=False, end_date_in_month=False):
        attach_plan_obj = self.env['planning.month.attachment']
        plan_list = []
        # Search Based on Attachment
        # Search in Yearly
        if type_plan == 'Yearly':
            domain += [('attachment_type', '=', 'Yearly'), ('option_id', '=', self.category_id.id)]
            plan_yearly_ids = attach_plan_obj.search(domain)
            if plan_yearly_ids:
                for plan_yearly_id in plan_yearly_ids:
                    if start_date_in_month and end_date_in_month:
                        for plan_id in plan_yearly_id.planning_monthly_ids.filtered(lambda p: p.date_start >= start_date_in_month and p.date_start <= end_date_in_month and p.option_id == self.category_id and p.sub_activity_id.name == "COAL GETTING"):
                            plan_list.append(plan_id)
                    else:
                        for plan_id in plan_yearly_id.planning_monthly_ids.filtered(lambda p: p.sub_activity_id.name == "COAL GETTING"):
                            plan_list.append(plan_id)
        # Search in Monthly
        else:
            domain += [('attachment_type', '=', 'Monthly'), ('period_month', '=', self.period_month), ('option_id', '=', self.category_id.id)]
            plan_month_ids = attach_plan_obj.search(domain)
            if plan_month_ids:
                for plan_month_id in plan_month_ids:
                    for plan_id in plan_month_id.planning_monthly_ids.filtered(lambda p: p.date_start >= self.date_start and p.date_start <= self.date_end and p.option_id == self.category_id and p.sub_activity_id.name == "COAL GETTING"):
                        plan_list.append(plan_id)
        return plan_list

    def _prepare_data_result(self, total_volume_gar, total_volume):
        return (0, 0, {
            'category_id': total_volume.id,
            'volume': total_volume_gar[total_volume]
        })

    def _get_total_days_in_month(self, selec_month, select_years):
        start_date = (datetime(int(select_years), int(selec_month), 1)).date()
        last_date = (calendar.monthrange(int(select_years), int(selec_month)))[1]
        end_date_plan = _("%s-%s-%s 00:00:00") % (select_years, selec_month, last_date)
        end_date = (datetime.strptime(end_date_plan, "%Y-%m-%d %H:%M:%S")).date()
        return start_date, end_date

    # Filering Data Planning with Category
    def _get_split_data_volume(self, categ_ids, plan_list, workdays_in_month):
        total_volume_gar = {}
        for categ_id in categ_ids:
            total_volume = 0
            for plan_id in plan_list:
                for seam_plan in plan_id.seam_plan_ids.filtered(lambda x: x.cv_ar >= categ_id.start_gar and x.cv_ar <= categ_id.end_gar and x.ts_id == categ_id.ts_id):
                    total_volume += seam_plan.volume_seam
            # Check if duration date
            workdays = 0
            if self.date_start or self.date_end:
                if self.date_start and self.date_end:
                    workdays = (self.date_end - self.date_start).days + 1
                else:
                    workdays = 1
            if workdays > 0:
                if workdays_in_month > 1:
                    total_volume = (workdays / workdays_in_month) * total_volume
                else:
                    total_volume = total_volume
            total_volume_gar[categ_id] = total_volume
        return total_volume_gar

    # Plan
    active = fields.Boolean('Active', store=True, default=True)
    contract = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], default='yes', copy=False, required=True)
    company_id = fields.Many2one('res.company', force_save='1', string='Bisnis Unit', default=lambda self: (self.env.company.id), domain=_company_ids_domain)
    contract_id = fields.Many2one('buyer.contract', 'No. Contract', store=True, domain="[('state', '=', 'release'), ('contract_state', '=', 'open'), ('company_id', '=', company_id)]", copy=False)
    contract_type = fields.Selection([
        ('Longterms', 'Longterms'),
        ('Spot', 'Spot'),
    ], default='Longterms', string='Contract Type', store=True, required=True, tracking=True)
    buyer_id = fields.Many2one('res.partner', string="Buyer", store=True, domain="[('is_buyer', '=', True)]", tracking=True)
    bl_month = fields.Selection(
        selection=MONTH_SELECTION,
        string='BL Month',
        help='Select the desired month',
        store=True
    )
    bl_years = fields.Selection(selection='_get_year_selection', string='BL Years', store=True)
    laycan_start = fields.Date('Laycan Start', store=True, tracking=True)
    laycan_end = fields.Date('Laycan End', store=True, tracking=True)
    qty_sales_plan = fields.Float('Qty Sales Plan', store=True, required=True, tracking=True)
    product_id = fields.Many2one('product.template', string="Product", store=True, required=True, domain="[('is_marketing', '=', True)]")
    sizing = fields.Selection([
        ('sizing', 'Sizing'),
        ('no_sizing', 'No Sizing'),
    ], default='sizing', string='Sizing', store=True, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approval'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], string='Status', default='draft', store=True, required=True, copy=False, tracking=True)
    market_type = fields.Selection([
        ('Export', 'Export'),
        ('Domestic', 'Domestic'),
    ], string='Market', related='contract_id.market_type')
    # Approval
    spv_marketing_id = fields.Many2one('res.users', string="SPV Marketing", domain="[('company_ids', 'in', company_id)]")
    manager_marketing_id = fields.Many2one('res.users', string="Manager Marketing", domain="[('company_ids', 'in', company_id)]")
    user_approval_ids = fields.Many2many(
        'res.users', 'sales_plan_user_rel', 'sales_plan_id', 'user_id',
        string='Approvals', store=True, copy=False
    )
    reason_reject = fields.Text("Reason Rejected", store=True)
    uid_reject = fields.Many2one('res.users', "Reason Rejected", store=True, readonly=True, tracking=True)
    # VALIDATION
    validation_plan = fields.One2many('validation.plan', 'validation_sales_plan_id', string='Validation',
        default=lambda self: (self.set_validation()))
    is_approver = fields.Boolean(string='is approve', compute='_set_approver')
    is_creator = fields.Boolean(string='is creator', compute='_is_creator')

    @api.constrains('laycan_start', 'laycan_end')
    def _check_duration_laycan(self):
        for sales_plan in self:
            if sales_plan.laycan_start and sales_plan.laycan_end:
                diff_date = sales_plan.laycan_end - sales_plan.laycan_start
                if diff_date.days > 6 or diff_date.days < 2:
                    raise ValidationError(_("Laycan Date Max 7 Days or Min 3 Days Duration"))

    def _set_approver(self):
        for sales_plan in self:
            approver = sales_plan.validation_plan.filtered(lambda x: x.user_id.id == self.env.user.id)
            if approver:
                sales_plan.is_approver = True
            else:
                sales_plan.is_approver = False

    def _is_creator(self):
        for sales_plan in self:
            if self.env.user.id == sales_plan.create_uid.id:
                sales_plan.is_creator = True
            else:
                sales_plan.is_creator = False

    def check_days(self, years, month):
        return calendar.monthrange(years, month) or False

    def action_submit(self):
        for sales_plan in self:
            if self.env.uid != sales_plan.create_uid.id:
                raise ValidationError(_("You cann't creator this record"))
            for user_validation in sales_plan.validation_plan:
                bl_month = dict(self._fields['bl_month'].selection).get(sales_plan.bl_month) or "-"
                no_contract = '-'
                if sales_plan.contract_id:
                    no_contract = sales_plan.contract_id.no_contract
                template = self.env.ref('bcr_barging_sales.notification_sales_plan_approval').with_context(
                    bl_month=bl_month,
                    invited_users=user_validation.user_id.name,
                    no_contract=no_contract
                )
                template.send_mail(sales_plan.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user_validation.user_id.login})
            self.write({
                'state': 'waiting'
            })
        return

    def action_revise(self):
        self.update({
            'state': 'draft',
        })
        return

    def action_reject(self):
        self.update({
            'state': 'reject',
        })
        return

    def action_approve(self):
        for sales_plan in self:
            users = []
            for user_validation in sales_plan.validation_plan:
                users.append(user_validation.user_id.id)

            if self.env.uid in users:
                sales_plan.write({
                    'state': 'approve'
                })
            else:
                raise ValidationError(_("You cann't approver"))
            return

    def name_get(self):
        result = []
        for sales_plan in self:
            if sales_plan.contract == 'yes':
                contract = sales_plan.contract_id.no_contract
                name = _("(%s) %s") % (str(sales_plan.id), contract)
            else:
                name = sales_plan.id
            result.append((sales_plan.id, name))
        return result

    @api.onchange('contract')
    def change_contract_type(self):
        if self.contract == 'no':
            self.contract_id = False
            self.buyer_id = False
            self.bl_month = False
            self.bl_years = False
            self.laycan_start = False
            self.laycan_end = False
            self.product_id = False
            self.qty_sales_plan = False
        if self.contract == 'yes' and not self.contract_id:
            self.contract_id = False
            self.buyer_id = False
            self.bl_month = False
            self.bl_years = False
            self.laycan_start = False
            self.laycan_end = False
            self.product_id = False
            self.qty_sales_plan = False

    @api.onchange('contract_id')
    def change_contract_value(self):
        if self.contract_id and self.contract == 'yes':
            contract = self.contract_id
            # Set Value
            self.buyer_id = contract.buyer_id
            self.company_id = contract.company_id
            self.buyer_id = contract.buyer_id
            self.laycan_start = contract.laycan_start
            self.laycan_end = contract.laycan_end
            self.product_id = contract.product_id
            self.contract_type = contract.contract_type

    # Create Contract
    def prepare_context_contract(self):
        return {
            'create': 0,
            'default_quantity': self.qty_sales_plan,
            'default_company_id': self.company_id.id,
            'default_buyer_id': self.buyer_id.id or False,
            'default_product_id': self.product_id.id,
            'default_contract_type': self.contract_type,
            'default_laycan_start': self.laycan_start,
            'default_laycan_end': self.laycan_end,
        }

    def action_create_contract(self):
        self.ensure_one()
        context = self.prepare_context_contract()
        return {
            'name': _("Create Contract"),
            'type': 'ir.actions.act_window',
            'target': 'current',
            'view_mode': 'form',
            'res_model': 'buyer.contract',
            'view_id': self.env.ref('bcr_barging_sales.buyer_contract_view_form').id,
            'context': context
        }


class CategoryTypeCoal(models.Model):
    _name = "category.type.coal"
    _description = 'Category Type Coal'

    active = fields.Boolean('Active', store=True, default=True)
    name = fields.Char('Name', store=True, required=True)
    start_gar = fields.Integer('Start GAR', store=True, required=True)
    end_gar = fields.Integer('End GAR', store=True, required=True)
    ts_id = fields.Many2one('ts.adb', string='TS', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class ResultPlanProduction(models.Model):
    _name = "result.plan.production"
    _description = 'Result Plan Production'

    active = fields.Boolean('Active', store=True, default=True)
    category_id = fields.Many2one('category.type.coal', string='Category', store=True)
    ts_id = fields.Many2one('ts.adb', related='category_id.ts_id', string='TS', store=True)
    plan_id = fields.Many2one('sales.plan', string='Plan', store=True)
    volume = fields.Float('Volume')


class PlanningOperationalAttach(models.Model):
    _name = 'sales.plan.attachment'
    _description = 'Sales Plan Attachment'
    _order = 'id asc'
    _rec_name = 'sales_plan_id'

    sales_plan_id = fields.Many2one('sales.plan', string='Sales Plan', ondelete='cascade')
    name = fields.Char("Name")
    attach_file = fields.Binary(string="Attachment")
    attach_name = fields.Char(string="Filename")
