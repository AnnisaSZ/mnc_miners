from odoo import models, fields, api, _


class ResRoster(models.Model):
    _name = 'res.roster'

    name = fields.Char('Name', compute='_compute_name', store=True)
    total_off = fields.Integer('Total Off', store=True, required=True)
    total_workdays = fields.Integer('Total Workdays', store=True, required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], default='active', store=True, required=True)

    @api.depends('total_off', 'total_workdays')
    def _compute_name(self):
        for roster in self:
            name = "%s:%s" % (roster.total_workdays, roster.total_off)
            roster.name = name


class ResDayPeriod(models.Model):
    _name = 'res.day.period'

    name = fields.Char('Name', store=True, required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], default='active', store=True, required=True)


class ResAttLocation(models.Model):
    _name = 'res.att.location'

    name = fields.Char('Name', store=True, required=True)
    loc_working_id = fields.Many2one(
        'mncei.lokasi.kerja', 'Working Location', store=True)
    location = fields.Char("Location Maps")
    longitude = fields.Char("Longitude")
    latitude = fields.Char("Latitude")
    limit_location = fields.Float("Limit Radius", default=0.0, store=True)
    allowed_location = fields.Float("Allowed Radius", default=0.0, store=True)
    is_other = fields.Boolean("Other", store=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], default='active', store=True, required=True)
