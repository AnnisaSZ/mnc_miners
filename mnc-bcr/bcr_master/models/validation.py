from odoo import api, fields, models, _


class ValidationType(models.Model):
    _name = 'validation.type'
    _description = 'Validation Type'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)


class Validation(models.Model):
    _name = 'validation.validation'
    _description = 'Validation'
    _rec_name = 'model_id'

    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    bisnis_unit_id = fields.Many2one('master.bisnis.unit', required=True, )
    validation_line = fields.One2many('validation.line', 'validation_id', string='Validation Line')


class ValidationLine(models.Model):
    _name = 'validation.line'
    _description = 'Validation Line'

    validation_id = fields.Many2one('validation.validation', string='Validation')
    sequence = fields.Integer(string='Sequence')
    user_id = fields.Many2one('res.users', string='User', required=True)
    validation_type_id = fields.Many2one('validation.type', string='Validation Type', required=True)


class ValidationPlan(models.Model):
    _name = 'validation.plan'
    _description = 'Validation Plan'

    sequence = fields.Integer(string='Sequence')
    user_id = fields.Many2one('res.users', string='User', required=True)
    validation_type_id = fields.Many2one('validation.type', string='Validation Type', required=True)

