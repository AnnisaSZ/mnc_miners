from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging


_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_sparepart = fields.Boolean('Sparepart', store=True)
    part_numbers = fields.Char('Part Number', store=True)
    purchase_price = fields.Float('Purchase Price', store=True)

    # Out/In Products
    product_in = fields.Integer('Product In', compute='_calc_product_moves')
    product_out = fields.Integer('Product Out', compute='_calc_product_moves')

    # @api.depends('')
    def _calc_product_moves(self):
        for product_tmpl in self:
            move_line_ids = self.env['stock.move.line'].search([('product_id', '=', product_tmpl.product_variant_id.id)])
            product_in = 0
            product_out = 0
            if move_line_ids:
                for move_line in move_line_ids:
                    picking_id = self.env['stock.picking'].search([('name', '=', move_line.reference)])
                    if picking_id:
                        qty = 0
                        for picking_move in picking_id.move_ids_without_package.filtered(lambda x: x.product_id == product_tmpl.product_variant_id):
                            qty += picking_move.quantity_done
                        if picking_id.picking_type_id.sequence_code == 'IN':
                                product_in += qty
                        if picking_id.picking_type_id.sequence_code == 'OUT':
                            product_out += qty
            product_tmpl.product_in = product_in
            product_tmpl.product_out = product_out
