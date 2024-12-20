from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class AktualBargingHelp(models.Model):
    _name = 'aktual.barging.help'
    _description = 'Sql View Table Aktual Barging Help'
    _auto = False

    barge_lot_id = fields.Integer("Barge Lot")
    shipping_id = fields.Integer("Barge Lot")
    mv = fields.Char("MV")
    barge = fields.Char("Barge")
    tugboat = fields.Char("Tugboat")
    jetty = fields.Char("Jetty")
    jetty_id = fields.Integer("Jetty ID")
    market_type = fields.Char("Market Type")
    loading_date = fields.Date("Loading Date")
    iup = fields.Char("IUP")
    kontraktor = fields.Char("Kontraktor")
    pit = fields.Char("PIT")
    source_id = fields.Integer("Source ID")
    shift = fields.Char("Bulan Period")
    volume_cb = fields.Float("Volume CB")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW aktual_barging_help
            AS
            (
                SELECT ss.id AS shipping_id,
                bd.id AS barge_lot_id,
                mv.name AS mv,
                barg.nama_barge AS barge,
                tugb.name AS tugboat,
                tcb.jetty_id jetty_id,
                jet.name AS jetty,
                tcb.market_type,
                tcb.loading_date,
                cp.name AS iup,
                kont.name AS kontraktor,
                ar.name AS pit,
                tcb.source_id,
                sour.name AS source,
                upper(sh.ttype::text || ' SHIFT'::text) AS shift,
                sum(tcb.volume) AS volume_cb
               FROM product_detail tcb
                 LEFT JOIN barge_detail bd ON tcb.barge_detail_id = bd.id
                 LEFT JOIN sales_shipping ss ON tcb.shipping_id = ss.id
                 LEFT JOIN master_mv mv ON mv.id = tcb.mv_id
                 LEFT JOIN master_barge barg ON barg.id = tcb.barge_id
                 LEFT JOIN master_tugboat tugb ON tugb.id = bd.tugboat_id
                 LEFT JOIN master_jetty jet ON jet.id = tcb.jetty_id
                 LEFT JOIN res_company cp ON tcb.company_id = cp.id
                 LEFT JOIN res_partner kont ON kont.id = tcb.kontraktor_barging_id
                 LEFT JOIN master_shiftmode_line sh ON sh.id = tcb.shift_line_id
                 LEFT JOIN master_source sour ON sour.id = tcb.source_id
                 LEFT JOIN master_area ar ON ar.id = tcb.area_id
              WHERE tcb.active = true AND tcb.state::text = 'complete'::text
              GROUP BY ss.id, bd.id, mv.name, barg.nama_barge, tugb.name, jet.name, tcb.market_type, tcb.loading_date, cp.name, kont.name, tcb.source_id, sour.name, ar.name, (upper(sh.ttype::text || ' SHIFT'::text)),tcb.jetty_id
              ORDER BY tcb.loading_date
            )
        """)


# class AktualBargingHelp2(models.Model):
#     _name = 'aktual.barging.help2'
#     _description = 'Sql View Table Aktual Barging Help2'
#     _auto = False

#     shipping_id = fields.Integer("Shipping ID")
#     barge_lot_id = fields.Integer("Barge Lot")
#     mv = fields.Char("MV")
#     barge = fields.Char("Barge")
#     tugboat = fields.Char("Tugboat")
#     jetty = fields.Char("Jetty")
#     market_type = fields.Char("Market Type")
#     loading_date = fields.Date("Loading Date")
#     iup = fields.Char("IUP")
#     kontraktor = fields.Char("Kontraktor")
#     shift = fields.Char("Bulan Period")
#     seam = fields.Char("Seam")
#     pit_id = fields.Integer("PIT")
#     volume_cb = fields.Float("Volume CB")

#     def init(self):
#         self._cr.execute("""
#             CREATE OR REPLACE VIEW aktual_barging_help2
#             AS
#             (
#                 select
#                 ss.id shipping_id,
#                 bd.id barge_lot_id,
#                 mv.name MV,
#                 barg.nama_barge barge,
#                 tugb.name tugboat,
#                 jet.name Jetty,
#                 tcb.market_type,
#                 loading_date,
#                 cp.name iup,
#                 kont.name kontraktor,
#                 upper(sh.ttype||' SHIFT') shift,se.code seam,
#                 tcb.area_id pit_id,
#                 sum(volume) volume_cb

#                 from product_detail tcb
#                 left join barge_detail bd on tcb.barge_detail_id=bd.id
#                 left join sales_shipping ss on tcb.shipping_id=ss.id
#                 left join master_mv mv on mv.id=tcb.mv_id
#                 left join master_barge barg on barg.id=tcb.barge_id
#                 left join master_tugboat tugb on tugb.id=bd.tugboat_id
#                 left join master_jetty jet on jet.id=tcb.jetty_id
#                 left join res_company cp on tcb.company_id = cp.id
#                 left join res_partner kont on kont.id=tcb.kontraktor_barging_id
#                 left join master_shiftmode_line sh on sh.id=tcb.shift_line_id
#                 LEFT JOIN master_seam se ON tcb.seam_id = se.id
#                 LEFT JOIN master_area ar ON ar.active = true AND tcb.area_id = ar.id
#                 where tcb.active=true
#                 and tcb.state='complete'
#                 group by
#                 ss.id,
#                 bd.id,
#                 mv.name ,
#                 barg.nama_barge ,
#                 tugb.name ,
#                 jet.name ,
#                 tcb.market_type,
#                 loading_date,
#                 cp.name ,
#                 kont.name ,
#                 upper(sh.ttype||' SHIFT'),
#                 se.code,
#                 ar.name,
#                 tcb.area_id
#                 order by loading_date
#             )
#         """)


# class AktualBargingHelp3(models.Model):
#     _name = 'aktual.barging.help3'
#     _description = 'Sql View Table Aktual Barging Help3'
#     _auto = False

#     iup = fields.Char("IUP")
#     pit = fields.Char("PIT")
#     seam = fields.Char("Seam")
#     activity = fields.Char("Activity")
#     loading_date = fields.Date("PIT")
#     volume_cb = fields.Float("Volume CB")

#     def init(self):
#         self._cr.execute("""
#             CREATE OR REPLACE VIEW aktual_barging_help3
#             AS
#             (
#                 select
#                 -- ab.barge_lot_id,
#                 ab.iup
#                 ,ar.name pit,
#                 ab.seam,
#                 'COAL BARGING' activity,
#                 ab.loading_date,
#                 -- ab.volume_cb,bdl.load_cargo,dat.volume_cb_tc,
#                 ab.volume_cb/dat.volume_cb_tc*bdl.load_cargo volume_cb
#                 from aktual_barging_help2 ab
#                 left join master_area ar ON ar.active = true AND ab.pit_id = ar.id
#                 left join barge_detail_line bdl on ab.barge_lot_id=bdl.barge_id and ar.id=bdl.pit_id
#                 left join (
#                     select barge_lot_id,sum(volume_cb) volume_cb_tc
#                     from aktual_barging_help2
#                     group by barge_lot_id)dat on dat.barge_lot_id=ab.barge_lot_id
#             )
#         """)


class ActProdHelp2(models.Model):
    _name = 'aktual.prod.help2'
    _description = 'Sql View Table Actual Prod Help2'
    _auto = False

    iup = fields.Char("IUP")
    pit = fields.Char("PIT")
    seam = fields.Char("Seam")
    sub_activity = fields.Char("Sub Activity")
    date = fields.Date("Date")
    volume = fields.Float("Volume")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW aktual_prod_help2
            AS
            (
                select IUP, pit,seam,
                sub_activity,date,
                sum(volume) volume

                from
                (
                    select
                    cp.name IUP,
                    kont.name Kontraktor,
                    sa.name sub_activity,
                    area.name pit,
                    frso.name source,
                    act.date_act date,
                    se.code seam,
                    sh.ttype || ' SHIFT' shift,

                    --frsog.name source_group,tosog.name destination_group,toso.name destination,
                    act.* from act_operational act
                    left join master_sub_activity sa on sa.id = act.sub_activity_id
                    left join res_company cp on act.company_id = cp.id
                    left join res_partner kont on kont.id=act.kontraktor_id
                    left join master_area area on area.id=act.area_id
                    left join master_sourcegroup frsog on frsog.id=act.from_source_group_id
                    left join master_source frso on frso.id=act.from_source_id
                    left join master_sourcegroup tosog on tosog.id=act.from_source_group_id
                    left join master_source toso on toso.id=act.from_source_id
                    left join master_shiftmode_line sh on sh.id=act.shift_line_id
                    LEFT JOIN master_seam se ON act.seam_id = se.id
                    where
                --  act.active=true and
                    act.state='complete'
                    and act.date_act >= '2024-03-22'
                )dat
                where sub_activity <> 'OVERBURDEN'
                group by IUP, pit, date,
                sub_activity,seam
                order by date desc
            )
        """)
