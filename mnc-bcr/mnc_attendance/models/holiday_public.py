from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from collections import defaultdict
from itertools import groupby

import logging

_logger = logging.getLogger(__name__)


class HrHolidaysPublic(models.Model):
    _inherit = "hr.holidays.public"

    date_start = fields.Date('Start Date', store=True, required=True)
    date_end = fields.Date('End Date', store=True, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verified', 'Verified'),
    ], default='draft', store=True, required=True)
    total_days = fields.Float("Total Days", store=True, compute='_calc_line')
    holiday_type = fields.Selection([
        ('public', 'Public Holiday'),
        ('mass_leave', 'Mass Leave'),
    ], default='mass_leave', store=True, required=True)

    @api.depends('line_ids')
    def _calc_line(self):
        for public in self:
            total = len(public.line_ids.ids) or 0.0
            public.total_days = total

    def action_approved(self):
        for public in self:
            public.write({
                'state': 'verified'
            })
        return

    def action_set_draft(self):
        self.ensure_one()
        self.update({
            'state': 'draft'
        })
        return

    @api.depends('holiday_type', 'date_start', 'date_end')
    def _compute_display_name(self):
        public_model = self.env['hr.holidays.public']
        for line in self:
            years = [k for k, g in groupby([line.date_start.year, line.date_end.year])]
            name = _("%s - %s") % (dict(public_model._fields['holiday_type'].selection).get(line.holiday_type), years)
            line.display_name = name

    # Override
    def _get_domain_check_date_state_one_state_ids(self):
        return [
            ("date", "=", self.date),
            ('holiday_type', '=', self.holiday_type),
            ("year_id", "=", self.year_id.id),
            ("state_ids", "!=", False),
            ("id", "!=", self.id),
        ]

    def _get_domain_check_date_state_one(self):
        return [
            ("date", "=", self.date),
            ('holiday_type', '=', self.holiday_type),
            ("year_id", "=", self.year_id.id),
            ("state_ids", "=", False),
        ]

    def _check_year_one(self):
        if self.search_count(
            [
                ("year", "=", self.year),
                ('holiday_type', '=', self.holiday_type),
                ("country_id", "=", self.country_id.id),
                ("id", "!=", self.id),
            ]
        ):
            raise ValidationError(
                _(
                    "You can't create duplicate public holiday per year and/or"
                    " country"
                )
            )
        return True
