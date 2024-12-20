from odoo import models, fields, api, _
from odoo.tools import float_compare, float_is_zero
# from odoo.exceptions import AccessError, UserError, ValidationError

import logging


_logger = logging.getLogger(__name__)


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    is_sparepart = fields.Boolean('Sparepart', store=True)
    bisnis_unit_id = fields.Many2one('master.bisnis.unit', string="IUP", store=True)


class ProductCategories(models.Model):
    _inherit = "product.category"

    is_sparepart = fields.Boolean('Sparepart', store=True)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", domain="[('is_sparepart', '=', True)]", store=True)
    is_sparepart = fields.Boolean('Sparepart', related='warehouse_id.is_sparepart', store=True)


class StockQuant(models.Model):
    _inherit = "stock.quant"

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", store=True)
    is_sparepart = fields.Boolean('Sparepart', related='warehouse_id.is_sparepart', store=True)
    lot_stock_id = fields.Many2one('stock.location', string="Location", related="warehouse_id.lot_stock_id", store=True)

    @api.onchange('location_id')
    def change_warehouse(self):
        if self.location_id:
            warehouse_id = self.env['stock.warehouse'].search([('lot_stock_id', '=', self.location_id.id)], limit=1)
            if warehouse_id:
                self.warehouse_id = warehouse_id

    @api.model
    def _get_inventory_fields_create(self):
        """ Returns a list of fields user can edit when he want to create a quant in `inventory_mode`.
        """
        basic_fields = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id', 'inventory_quantity']
        addons_fields = ['warehouse_id', 'is_sparepart', 'lot_stock_id']
        return basic_fields + addons_fields


class StockIventory(models.Model):
    _inherit = "stock.inventory"

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", domain="[('company_id', '=', company_id), ('is_sparepart', '=', True)]", store=True)
    lot_stock_id = fields.Many2one('stock.location', string="Location", related="warehouse_id.lot_stock_id", store=True)
    location_ids = fields.Many2many(
        'stock.location', string='Locations',
        readonly=True, check_company=True,
        states={'draft': [('readonly', False)]},
        domain="[('id', '=', lot_stock_id), ('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit'])]")
    is_sparepart = fields.Boolean('Sparepart', related='warehouse_id.is_sparepart', store=True)
    product_ids = fields.Many2many(
        'product.product', string='Products', check_company=True,
        domain="[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id), ('is_sparepart', '=', True)]", readonly=True,
        states={'draft': [('readonly', False)]},
        help="Specify Products to focus your inventory on particular Products.")


class StockMove(models.Model):
    _inherit = "stock.move"

    repair_id = fields.Many2one('repair.maintenance', string="Repair", index=True)

    # def _get_price_unit(self):
    #     """ Returns the unit price to value this stock move """
    #     self.ensure_one()
    #     price_unit = self.price_unit
    #     precision = self.env['decimal.precision'].precision_get('Product Price')
    #     # If the move is a return, use the original move's price unit.
    #     print(">>>>>>Price Unit<<<<<<<")
    #     print(price_unit)
    #     print(self._should_force_price_unit())
    #     print(float_is_zero(price_unit, precision))
    #     if self.origin_returned_move_id and self.origin_returned_move_id.sudo().stock_valuation_layer_ids:
    #         print("XXXXXXXXXXXXXXXXXXXX00")
    #         layers = self.origin_returned_move_id.sudo().stock_valuation_layer_ids
    #         # dropshipping create additional positive svl to make sure there is no impact on the stock valuation
    #         # We need to remove them from the computation of the price unit.
    #         if self.origin_returned_move_id._is_dropshipped():
    #             layers = layers.filtered(lambda l: float_compare(l.value, 0, precision_rounding=l.product_id.uom_id.rounding) <= 0)
    #         layers |= layers.stock_valuation_layer_ids
    #         quantity = sum(layers.mapped("quantity"))
    #         return layers.currency_id.round(sum(layers.mapped("value")) / quantity) if not float_is_zero(quantity, precision_rounding=layers.uom_id.rounding) else 0
    #     return price_unit
    #     # return price_unit if not float_is_zero(price_unit, precision) or self._should_force_price_unit() else self.product_id.standard_price

    # def _create_in_svl(self, forced_quantity=None):
    #     """Create a `stock.valuation.layer` from `self`.

    #     :param forced_quantity: under some circunstances, the quantity to value is different than
    #         the initial demand of the move (Default value = None)
    #     """
    #     svl_vals_list = []
    #     for move in self:
    #         move = move.with_company(move.company_id)
    #         valued_move_lines = move._get_in_move_lines()
    #         valued_quantity = 0
    #         for valued_move_line in valued_move_lines:
    #             valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
    #         unit_cost = abs(move._get_price_unit())  # May be negative (i.e. decrease an out move).
    #         if not move.product_id.product_tmpl_id.is_sparepart:
    #             if move.product_id.cost_method == 'standard':
    #                 unit_cost = move.product_id.standard_price
    #         svl_vals = move.product_id._prepare_in_svl_vals(forced_quantity or valued_quantity, unit_cost)
    #         svl_vals.update(move._prepare_common_svl_vals())
    #         if forced_quantity:
    #             svl_vals['description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
    #         svl_vals_list.append(svl_vals)
    #     return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)
