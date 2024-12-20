from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WBSCommisioner(models.Model):
    _name = 'wbs.commisioner'
    _description = 'WBS Commisioner'
    _order = 'id desc'

    name = fields.Many2one('mncei.employee', required=True, string='Full Name', ondelete='restrict', store=True, domain="[('department.name','=','BOC')]")
    actives = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2many('res.company', string='Business Unit', store=True, required=True, copy=False)

class WBSDirector(models.Model):
    _name = 'wbs.director'
    _description = 'WBS Director'
    _order = 'id desc'

    name = fields.Many2one('mncei.employee', required=True, string='Full Name', ondelete='restrict', store=True, domain="[('department.name','=','BOD')]")
    actives = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2many('res.company', string='Business Unit', store=True, required=True, copy=False)

class WBSAuditor(models.Model):
    _name = 'wbs.auditor'
    _description = 'WBS Auditor'
    _rec_name = 'head_audit_id'
    _order = 'id desc'

    head_audit_id = fields.Many2one('mncei.employee', required=True, string='Head Audit', ondelete='restrict', store=True, domain="[('department.name','=','Internal Audit')]")
    actives = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2many('res.company', string='Business Unit', store=True, required=True, copy=False)
    
    auditor_1_ids = fields.Many2many('mncei.employee', 'auditor_1_ids', required=True, string='Auditor 1', ondelete='restrict', store=True, domain="[('department.name','=','Internal Audit')]")
    auditor_2_ids = fields.Many2many('mncei.employee', 'auditor_2_ids', required=True, string='Auditor 2', ondelete='restrict', store=True, domain="[('department.name','=','Internal Audit')]")
    auditor_3_ids = fields.Many2many('mncei.employee', 'auditor_3_ids', required=True, string='Auditor 3', ondelete='restrict', store=True, domain="[('department.name','=','Internal Audit')]")
    
class WBSTnC(models.Model):
    _name = 'wbs.tnc'
    _description = 'WBS TNC'
    _order = 'id desc'

    name = fields.Text('Terms & Conditions', store=True, required=True, copy=False)
    actives = fields.Boolean(string="Active", default=True)
