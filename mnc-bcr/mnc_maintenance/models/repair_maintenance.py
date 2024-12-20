from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class RepairMaintenance(models.Model):
    _name = "repair.maintenance"
    _description = "Repair Maintenance"
    _rec_name = "no_repair"

    no_repair = fields.Char('No. Repair', store=True)
    breakdown_id = fields.Many2one('fleet.breakdown', 'Breakdown Number', store=True)
    breakdown_code = fields.Char(related='breakdown_id.code_seq', store=True)
    repair_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
    ], string='Type', store=True, tracking=True)
    is_internal = fields.Boolean('Internal', store=True)
    is_external = fields.Boolean('External', store=True)
    date = fields.Date('Date', store=True)
    unit_equip_id = fields.Many2one('fleet.equipment.unit', string='Unit Equipment', store=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', compute='get_warehouse_location', store=True)
    company_id = fields.Many2one('res.company', string="Company", related='warehouse_id.company_id', store=True)
    wh_company_id = fields.Many2one('res.company', string="Company", related='unit_equip_id.company_id', store=True)
    bisnis_unit_id = fields.Many2one('master.bisnis.unit', string="IUP", compute='get_warehouse_location', store=True)
    mncei_employee_id = fields.Many2one('mncei.employee', string="PIC", default=False, ondelete='set null', index=True, store=True)
    notes = fields.Text('Internal Notes', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('process', 'Process'),
        ('close', 'Close'),
        ('cancel', 'Cancel'),
    ], string='Type', default='draft', store=True, tracking=True)
    # Part Request
    request_ids = fields.One2many('request.part', 'repair_id', string="Part Request")
    workshop_ids = fields.One2many('workshop.station', 'repair_id', string="Workshop")
    # Moves
    picking_id = fields.Many2one('stock.picking', 'Transfer', index=True, states={'done': [('readonly', True)]}, check_company=True)
    picking_state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], related='picking_id.state')
    show_check_availability = fields.Boolean(
        related='picking_id.show_check_availability',
        help='Technical field used to compute whether the button "Check Availability" should be displayed.')
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type')
    picking_type_code = fields.Selection(
        related='picking_type_id.code',
        readonly=True)
    scheduled_date = fields.Datetime('Scheduled Date', default=fields.Datetime.now, index=True, store=True)
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,
        check_company=True, readonly=True,
        states={'request': [('readonly', False)]})
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        check_company=True, readonly=True,
        states={'request': [('readonly', False)]})
    move_ids_without_package = fields.One2many('stock.move', 'repair_id', string="Stock Moves", copy=True)

    @api.depends('wh_company_id')
    def get_warehouse_location(self):
        for repair in self:
            bisnis_unit_id = self.env['master.bisnis.unit'].search([('bu_company_id', '=', repair.wh_company_id.id)], limit=1)
            repair.bisnis_unit_id = bisnis_unit_id
            warehouse_id = self.env['stock.warehouse'].search([
                ('is_sparepart', '=', True),
                ('bisnis_unit_id', '=', bisnis_unit_id.id),
            ])
            if warehouse_id:
                repair.warehouse_id = warehouse_id
            else:
                repair.warehouse_id = False

    @api.onchange('breakdown_id')
    def _change_breakdown(self):
        if self.breakdown_id:
            self.unit_equip_id = self.breakdown_id.unit_equip_id

    def create_picking(self):
        Picking = self.env['stock.picking']
        picking_id = Picking.create({
            'picking_type_id': self.picking_type_id.id,
            'warehouse_id': self.warehouse_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'scheduled_date': self.scheduled_date,
            'origin': self.breakdown_code,
        })
        return picking_id

    def button_validate(self):
        if self.picking_id:
            self.picking_id.with_context(cancel_backorder=True)._action_done()

    def action_confirm(self):
        if not self.move_ids_without_package and self.is_internal:
            raise UserError(_("Please input your product request"))
        if not self.picking_id:
            picking_id = self.create_picking()
            self.write({
                'picking_id': picking_id.id
            })
            for move in self.move_ids_without_package:
                move.write({'picking_id': picking_id.id})
        self.mapped('move_ids_without_package')\
            .filtered(lambda move: move.state == 'draft')\
            ._action_confirm()
        return True

    def refresh_availability(self):
        # moves = self.mapped('move_ids_without_package').filtered(lambda move: move.state not in ('draft', 'cancel', 'done')).sorted(
        #     key=lambda move: (-int(move.priority), not bool(move.date_deadline), move.date_deadline, move.id)
        # )
        # if not moves:
        #     raise UserError(_('Nothing to check the availability for.'))
        # moves._action_assign()
        self.picking_id.action_assign()
        return True

    def action_cancel(self):
        self.picking_id.action_cancel()
        return True

    def create_internal(self):
        self.write({'is_internal': True})
        return

    def create_external(self):
        self.write({'is_external': True})
        return

    def do_process(self):
        if self.is_internal and self.move_ids_without_package and self.picking_id:
            self.picking_id.action_assign()
        elif not self.picking_id and self.is_internal:
            self.action_confirm()
        self.write({'state': 'process'})
        return

    def action_close(self):
        date_time = fields.Datetime.now() + timedelta(hours=7)
        # Mengambil jam dan menit
        hour = date_time.hour
        minute = date_time.minute
        # Mengubah jam dan menit ke float
        time_in_float = hour + minute / 60.0
        # Updates
        breakdown_id = self.breakdown_id
        breakdown_id.write({
            'date_rfu': date_time,
            'rfu': time_in_float,
        })
        breakdown_id.action_close()
        _logger.info("ZZZZZZZZZZZZZZZZZZZZZZ")
        print("ZZZZZZZZZZZZZZZZZZZZZZ")
        print(self.move_ids_without_package)
        if self.is_internal and self.picking_id:
            print("XXXXXXXXXXXXXXXXXXXXX")
            self.button_validate()
        self.write({'state': 'close'})
        return


class RequestPart(models.Model):
    _name = "request.part"
    _description = "Request Part Number"

    repair_id = fields.Many2one('repair.maintenance', string="Repair", store=True)
    product_tmp_id = fields.Many2one('product.template', string="Part Number", domain="[('is_sparepart', '=', True)]", store=True)
    qty_available = fields.Float('Qty Available')
    qty_request = fields.Float('Qty Request')

    @api.onchange('product_tmp_id')
    def _change_breakdown(self):
        if self.product_tmp_id:
            self.unit_equip_id = self.breakdown_id.unit_equip_id


class WorkshopStation(models.Model):
    _name = "workshop.station"
    _description = "Workshop Station"
    _rec_name = "workshop_no"

    workshop_no = fields.Char('Workshop Number', store=True)
    po_number = fields.Char('PO Number', store=True)
    date = fields.Date('Date', store=True)
    repair_id = fields.Many2one('repair.maintenance', string="Repair", store=True)
    price = fields.Float('Price', store=True)
    vendor = fields.Char('Vendor', store=True)
    description = fields.Text('Description', store=True)
    parent_state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('process', 'Process'),
        ('close', 'Close'),
        ('cancel', 'Cancel'),
    ], related='repair_id.state')
