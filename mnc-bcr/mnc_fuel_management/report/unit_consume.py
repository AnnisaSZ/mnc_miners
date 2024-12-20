# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api


class UnitConsumeReport(models.Model):
    """ Unit Consume Analysis """

    _name = "unit.consume.report"
    _auto = False
    _description = "CRM Activity Analysis"
    _rec_name = 'kode_unit'

    kode_unit = fields.Char('Kode Unit')
    fuel_consume = fields.Float('Fuel Consume')
    date = fields.Date("Date")
    standard_high = fields.Float('Standard High')
    standard_low = fields.Float('Standard Low')

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW unit_consume_report
            AS
            (SELECT
                fu.id,
                fu.kode_unit,
                coalesce(SUM(dl.total_liter)/nullif( SUM(dl.hm_finals),0),0) fuel_consume,
                fu.standard_high,
                fu.standard_low,
                dl.distribute_date date
                FROM fuel_distribution_line dl
                JOIN master_fuel_unit fu ON fu.id = dl.unit_id
                WHERE fu.standard_high <> 0
                GROUP BY fu.id, fu.kode_unit, fu.standard_high, fu.standard_low, dl.distribute_date
            )
        """)
