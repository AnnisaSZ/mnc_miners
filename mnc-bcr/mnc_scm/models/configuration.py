from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ScmOrderType(models.Model):
    _name = 'scm.order.type'
    _description = 'Order Type SCM'
    _order = 'id desc'

    name = fields.Char('Order Type', store=True, required=True, copy=False)
    actives = fields.Boolean(string="Active")
    orf_ids = fields.One2many('order.request', 'order_type_id', store=True, string="ORF")

class ScmFOB(models.Model):
    _name = 'scm.fob'
    _description = 'FOB SCM'
    _order = 'id desc'

    name = fields.Char('FOB', store=True, required=True, copy=False)
    actives = fields.Boolean(string="Active")
    prl_ids = fields.One2many('purchase.requisition.line', 'fob_id', store=True, string="Purchase requitition")


class ScmPaymentTerm(models.Model):
    _name = 'scm.payment.term'
    _description = 'Payment Terms SCM'
    _order = 'id desc'

    name = fields.Char('Payment Terms', store=True, required=True, copy=False)
    actives = fields.Boolean(string="Active")
    prl_ids = fields.One2many('purchase.requisition.line', 'payment_terms_id', string="Purchase requitition")

    

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'id desc'

    fob = fields.Char('FOB', store=True, copy=False)
    code = fields.Char('Code', store=True, copy=False)
    shipping_from = fields.Selection([
        ('dom', 'Domestic'),
        ('import', 'Import'),
    ], default="dom", string='Shipping', store=True)

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name != "":
            domain += ['|', ('name', operator, name), ('code', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()
    
    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        context = self.env.context
        if context.get('is_scm'):
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        else:
            domain += [('name', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()
