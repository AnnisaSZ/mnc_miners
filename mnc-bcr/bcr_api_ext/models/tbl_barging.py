from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class AktualBarging(models.Model):
    _name = 'aktual.barging'
    _description = 'Sql View Table Aktual Barging'
    _auto = False

    shipping_id = fields.Integer("Barge Lot")
    barge_lot_id = fields.Integer("Barge Lot")
    mv = fields.Char("MV")
    barge = fields.Char("Barge")
    tugboat = fields.Char("Tugboat")
    jetty = fields.Char("Jetty")
    market_type = fields.Char("Market Type")
    loading_date = fields.Date("Loading Date")
    iup = fields.Char("IUP")
    kontraktor = fields.Char("Kontraktor")
    shift = fields.Char("Bulan Period")
    volume_cb = fields.Float("Volume CB")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW aktual_barging
            AS
            (
                SELECT ab.shipping_id,
                ab.barge_lot_id,
                ab.mv,
                ab.barge,
                ab.tugboat,
                ab.jetty,
                ab.market_type,
                ab.loading_date,
                ab.iup,
                ab.kontraktor,
                ab.shift,
                    CASE
                        WHEN bd.load_cargo IS NULL OR bd.load_cargo = 0::numeric THEN ab.volume_cb
                        ELSE ab.volume_cb / dat.volume_cb_tc * bd.load_cargo::double precision
                    END AS volume_cb
               FROM aktual_barging_help ab
                 LEFT JOIN ( SELECT bd_1.id,
                        ar.name AS pit,
                        bdl.load_cargo
                       FROM barge_detail bd_1
                         LEFT JOIN barge_detail_line bdl ON bd_1.id = bdl.barge_id
                         LEFT JOIN master_area ar ON ar.id = bdl.pit_id) bd ON ab.barge_lot_id = bd.id AND ab.pit::text = bd.pit::text
                 LEFT JOIN ( SELECT aktual_barging_help.barge_lot_id,
                        sum(aktual_barging_help.volume_cb) AS volume_cb_tc
                       FROM aktual_barging_help
                      GROUP BY aktual_barging_help.barge_lot_id) dat ON dat.barge_lot_id = ab.barge_lot_id
            )
        """)


class PlanBargingDaily(models.Model):
    _name = 'plan.barging.daily'
    _description = 'Sql View Table Planning Barging Daily'
    _auto = False

    iup = fields.Char("IUP")
    date = fields.Date("Date")
    volume_cb = fields.Float("Volume CB")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW plan_barging_daily
            AS
            (
                select
                case when contract='yes' then iup2.name else iup.name end iup,

                generate_series(
                    sp.laycan_start::timestamp,
                    sp.laycan_end::timestamp,
                    interval '1 day'
                    )::date as date,
                (sp.qty_sales_plan)/((sp.laycan_end - sp.laycan_start)::integer+1) volume_cb

                from sales_plan sp
                left join buyer_contract bc on sp.contract_id=bc.id
                left join res_company iup on iup.id=sp.company_id
                left join res_company iup2 on iup2.id=bc.company_id

                where sp.active=true
                and sp.state='approve'

                order by date desc
                )
        """)
