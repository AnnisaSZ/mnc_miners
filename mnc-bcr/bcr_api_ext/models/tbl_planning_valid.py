from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class PlanProduksiValid(models.Model):
    _name = 'plan.production.daily.valid'
    _description = 'Sql View Table Planning Daily Valid'
    _auto = False

    plan_3mrp = fields.Date("Date")
    dates = fields.Date("Date")
    plan_3mrp2 = fields.Date("Date")
    # Planning Daily
    plan_group_id = fields.Integer("Plan Group")
    category = fields.Char("Category")
    iup = fields.Char("IUP")
    kontraktor = fields.Char("Kontraktor")
    activity = fields.Char("Activity")
    pit = fields.Char("PIT")
    source = fields.Char("Source")
    tahun_plan = fields.Char("Tahun Plan")
    bulan_period = fields.Char("Bulan Period")
    bulan_plan = fields.Char("Bulan Plan")
    date = fields.Date("Date")
    dist_cg = fields.Float("Distance CG")
    dist_ob = fields.Float("Distance OB")
    dist_ch = fields.Float("Distance CH")
    volume_cg = fields.Float("Volume CG")
    volume_ob = fields.Float("Volume OB")
    volume_ch = fields.Float("Volume CH")
    batas_plan_3mrp = fields.Date("Date")
    kon2 = fields.Char("Kontraktor2")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW plan_production_daily_valid
            AS
            (--CREATE VIEW plan_production_daily_valid AS
                SELECT dat.plan_3mrp,
                    dat.datesss,
                    dat.plan_3mrp2,
                    dat.plan_group_id,
                    dat.category,
                    dat.iup,
                    dat.kontraktor,
                    dat.activity,
                    dat.pit,
                    dat.source,
                    dat.tahun_plan,
                    dat.bulan_plan,
                    dat.date,
                    dat.volume_cg,
                    dat.volume_ob,
                    dat.volume_ch,
                    dat.dist_cg,
                    dat.dist_ob,
                    dat.dist_ch,
                    dat.batas_plan_3mrp,
                    dat.kon2
                   FROM ( SELECT to_date(((pp1.tahun_plan::text || '-'::text) || pp1.bulan_plan) || '-01'::text, 'YYYY-MM-DD'::text) AS plan_3mrp,
                            date_trunc('MONTH'::text, pp1.date::timestamp with time zone)::date AS datesss,
                            pp1.tahun_plan::text || pp1.bulan_plan AS plan_3mrp2,
                            pp1.plan_group_id,
                            pp1.category,
                            pp1.iup,
                            pp1.kontraktor,
                            pp1.activity,
                            pp1.pit,
                            pp1.source,
                            pp1.tahun_plan,
                            pp1.bulan_plan,
                            pp1.date,
                            pp1.volume_cg,
                            pp1.volume_ob,
                            pp1.volume_ch,
                            pp1.dist_cg,
                            pp1.dist_ob,
                            pp1.dist_ch,
                            pp2.batas_plan_3mrp,
                            pp2.kon2
                           FROM plan_production_daily pp1
                             LEFT JOIN ( SELECT to_char(max(to_date(((plan_production_daily.tahun_plan::text || '-'::text) || plan_production_daily.bulan_plan) || '-01'::text, 'YYYY-MM-DD'::text))::timestamp with time zone, 'YYYYMM'::text) AS batas_plan_3mrp,
                                    case when plan_production_daily.kontraktor isnull then 'x' else plan_production_daily.kontraktor end AS kon2
                                   FROM plan_production_daily
                                  GROUP BY case when plan_production_daily.kontraktor isnull then 'x' else plan_production_daily.kontraktor end) pp2 ON case when pp1.kontraktor isnull then 'x' else pp1.kontraktor end = case when pp2.kon2 isnull then 'x' else pp2.kon2 end) dat
                  WHERE dat.category::text = '3MRP'::text AND (dat.plan_3mrp2 < dat.batas_plan_3mrp AND dat.plan_3mrp = dat.datesss OR dat.plan_3mrp2 = dat.batas_plan_3mrp)
                -- and dat.activity='HAULING'

                  ORDER BY dat.date
            )
        """)
