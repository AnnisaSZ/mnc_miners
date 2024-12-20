from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


# class DataInventory(models.Model):
#     _name = 'data.for.inventory'
#     _description = 'Sql View Table Data Inventory'
#     _auto = False

#     iup = fields.Char("IUP")
#     pit = fields.Char("PIT")
#     seam = fields.Char("Seam")
#     sub_activity = fields.Char("Sub Activity")
#     date = fields.Date("Date")
#     volume = fields.Float("Volume")

#     def init(self):
#         self._cr.execute("""
#             CREATE OR REPLACE VIEW data_for_inventory
#             AS
#             (
#                 -- CREATE VIEW data_for_inventory AS
#                 select
#                 bu.code iup,
#                 aa.pit,
#                 aa.seam,
#                 aa.sub_activity,
#                 aa.date,
#                 aa.volume
#                 from aktual_prod_help2 aa
#                 left join master_bisnis_unit bu on bu.name=aa.iup
#                 union all
#                 select bu.code iup,bb.pit,bb.seam,bb.activity,bb.loading_date,bb.volume_cb from aktual_barging_help3 bb
#                 left join master_bisnis_unit bu on bu.name=bb.iup
#             )
#         """)


class InventoryPIT(models.Model):
    _name = 'inventory.pit'
    _description = 'Sql View Table Inventory PIT'
    _auto = False

    sub_activity = fields.Char("Sub Activity")
    bisnis_unit = fields.Char("Busnis Unit")
    pit = fields.Char("PIT")
    seam = fields.Char("Seam")
    date = fields.Date("Date")
    volume = fields.Float("Volume")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW inventory_pit
            AS
            (
                SELECT
                sa.name AS sub_activity,
                cp.name AS bisnis_unit,
                ar.name AS pit,
                se.code AS seam,
                inv.date_act AS date,
                inv.volume
                FROM act_stockroom inv
                LEFT JOIN master_sub_activity sa ON inv.activity_id = sa.activity_id AND sa.active = true AND inv.sub_activity_id = sa.id
                LEFT JOIN res_company cp ON cp.active = true AND inv.bu_company_id = cp.id
                LEFT JOIN master_area ar ON ar.active = true AND inv.area_id = ar.id
                LEFT JOIN master_seam se ON inv.bu_company_id = se.bu_company_id AND inv.seam_id = se.id
                WHERE
                sa.name in ('MINE EXPOSES','MINEABLE') AND
                inv.active = true AND inv.state::text = 'complete'::text
            )
        """)


class InventoryBarging(models.Model):
    _name = 'for.inv.barging'
    _description = 'Sql View Table Data Inventory Barging'
    _auto = False

    iup = fields.Char("IUP")
    source = fields.Char("Source")
    source_id = fields.Integer("Source ID")
    destination = fields.Char("Destination")
    destination_id = fields.Integer("Destination ID")
    activity = fields.Char("Activity")
    volume_cb = fields.Float("Volume CB")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW for_inv_barging
            AS
            (
                SELECT
                ab.iup,
                ab.source,
                ab.source_id,
                ab.jetty destination,
                ab.jetty_id*10000 destination_id,
                'COAL BARGING' activity,
                ab.loading_date,
                CASE WHEN bd.load_cargo IS NULL OR bd.load_cargo = 0::numeric
                    THEN ab.volume_cb
                    ELSE ab.volume_cb / dat.volume_cb_tc * bd.load_cargo::double precision
                    END AS volume_cb
                FROM aktual_barging_help ab
                    LEFT JOIN
                        ( SELECT bd_1.id,
                        ar.name AS pit,
                        bdl.load_cargo
                        FROM barge_detail bd_1
                        LEFT JOIN barge_detail_line bdl ON bd_1.id = bdl.barge_id
                        LEFT JOIN master_area ar ON ar.id = bdl.pit_id) bd 
                        ON ab.barge_lot_id = bd.id AND ab.pit::text = bd.pit::text
                    LEFT JOIN 
                        ( SELECT aktual_barging_help.barge_lot_id,
                        sum(aktual_barging_help.volume_cb) AS volume_cb_tc
                        FROM aktual_barging_help
                        GROUP BY aktual_barging_help.barge_lot_id) dat
                        ON dat.barge_lot_id = ab.barge_lot_id
            )
        """)


class InventoryProduction(models.Model):
    _name = 'for.inv.production'
    _description = 'Sql View Table Data Inventory Production'
    _auto = False

    iup = fields.Char("IUP")
    source = fields.Char("Source")
    source_id = fields.Integer("Source ID")
    destination = fields.Char("Destination")
    destination_id = fields.Integer("Destination ID")
    sub_activity = fields.Char("Sub Activity")
    date = fields.Date("Date")
    volume = fields.Float("Volume")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW for_inv_production
            AS
            (
                select IUP,
                source,
                source_id,
                destination,
                destination_id,
                sub_activity,
                date,
                sum(volume) volume

                from
                (
                    select
                    cp.name IUP,
                    kont.name Kontraktor,
                    sa.name sub_activity,
                    area.name pit,
                    frso.name source,
                    act.from_source_id source_id,
                    toso.name destination,
                    act.to_source_id destination_id,
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
                    left join master_sourcegroup tosog on tosog.id=act.to_source_group_id
                    left join master_source toso on toso.id=act.to_source_id
                    left join master_shiftmode_line sh on sh.id=act.shift_line_id
                    LEFT JOIN master_seam se ON act.seam_id = se.id
                    where
                    act.state='complete'
                    and act.date_act >= '2024-03-22'
                )dat
                where sub_activity <> 'OVERBURDEN'
                group by IUP, date,
                sub_activity,source,source_id,destination,destination_id
                order by date desc
            )
        """)


class StockOpname(models.Model):
    _name = 'stock.opname'
    _description = 'Sql View Table Stock Opname'
    _auto = False

    sub_act = fields.Char("Sub Act")
    act = fields.Char("Activity")
    date = fields.Date("Date")
    iup = fields.Char("IUP")
    company_id = fields.Integer("Company ID")
    # seam = fields.Char("Seam")
    # pit = fields.Char("PIT")
    source = fields.Char("Source")
    source_id = fields.Integer("Source ID")
    end_stock = fields.Float("Volume")
    is_not_rom = fields.Boolean("Is Not Room")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW stock_opname
            AS
            (
                SELECT msa.name AS sub_act,
                ma.name AS act,
                (date_trunc('MONTH'::text, to_date((so.selected_years::text || "left"('0'::text || so.period_month::text, 2)) || '01'::text, 'YYYYMMDD'::text)::timestamp with time zone) + '1 mon -1 days'::interval)::date AS date,
                mbu.code AS iup,
                so.company_id,
                sour.name as source,
                sol.source_id,
                sum(sol.end_stock) end_stock,
                mbu.is_rom is_not_rom
               FROM act_stock_opname so
                 LEFT JOIN master_activity ma ON so.activity_id = ma.id AND ma.active = true
                 LEFT JOIN master_sub_activity msa ON so.activity_id = msa.activity_id AND msa.active = true AND so.sub_activity_id = msa.id
                 LEFT JOIN res_company cp ON cp.active = true AND so.company_id = cp.id
                 LEFT JOIN act_stock_opname_line sol ON so.id = sol.stock_opname_id
            --      LEFT JOIN master_area ar ON ar.active = true AND sol.pit_id = ar.id
            --      LEFT JOIN master_seam se ON sol.seam_id = se.id
                 LEFT JOIN master_source sour on sour.id=sol.source_id
                 LEFT JOIN master_bisnis_unit mbu ON mbu.bu_company_id = so.company_id and mbu.active=true
              WHERE so.active = true  AND sol.bedding = false
              group by msa.name,
                ma.name,
                (date_trunc('MONTH'::text, to_date((so.selected_years::text || "left"('0'::text || so.period_month::text, 2)) || '01'::text, 'YYYYMMDD'::text)::timestamp with time zone) + '1 mon -1 days'::interval)::date,
                mbu.code,
                so.company_id,
                sour.name,
                sol.source_id,mbu.is_rom
            )
        """)


class InventoryLastStock(models.Model):
    _name = 'for.inv.laststock'
    _description = 'Sql View Table Stock Opname'
    _auto = False

    sub_act = fields.Char("Sub Act")
    act = fields.Char("Activity")
    date = fields.Date("Date")
    iup = fields.Char("IUP")
    company_id = fields.Integer("Company ID")
    # seam = fields.Char("Seam")
    # pit = fields.Char("PIT")
    source = fields.Char("Source")
    source_id = fields.Integer("Source ID")
    end_stock = fields.Float("Volume")
    is_not_rom = fields.Boolean("Is Not Room")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW for_inv_laststock
            AS
            (
                SELECT so.sub_act,
                so.act,
                so.date,
                so.iup,
                so.company_id,
                so.source,
                so.source_id,
                so.end_stock,
                so.is_not_rom
                FROM ( SELECT so2.sub_act,
                    so2.act,
                    so2.date,
                    so2.iup,
                    so2.company_id,
                    so2.source,
                    so2.source_id,
                    so2.end_stock,
                    so2.is_not_rom
                   FROM ( SELECT stock_opname.source_id,
                            max(stock_opname.date) AS date
                           FROM stock_opname
                          GROUP BY stock_opname.source_id
                         HAVING stock_opname.source_id IS NOT NULL) so1
                     LEFT JOIN stock_opname so2 ON so1.source_id = so2.source_id) so
            )
        """)


# class HelpInventory(models.Model):
#     _name = 'help.inventory'
#     _description = 'Sql View Table Help Inventory'
#     _auto = False

#     inv = fields.Char("Inventory")
#     date_so = fields.Date("Date SO")
#     seam = fields.Char("Seam")
#     pit = fields.Char("PIT")
#     iup = fields.Char("IUP")
#     end_stock = fields.Float("Volume")
#     is_rom = fields.Boolean("Is Room")
#     coal_barging = fields.Float("Volume BG")
#     coal_getting = fields.Float("Volume GT")
#     coal_hauling = fields.Float("Volume HL")
#     date_barging = fields.Date("Date BG")
#     date_getting = fields.Date("Date GT")
#     date_hauling = fields.Date("Date HL")

#     def init(self):
#         self._cr.execute("""
#             CREATE OR REPLACE VIEW help_inventory
#             AS
#             (
#                 select
#                 so.sub_act inv,
#                 so.date date_so,
#                 so.iup,so.seam,
#                 so.pit,
#                 so.end_stock,
#                 so.is_rom,
#                 sum(case when sub_activity ='COAL BARGING' then volume end) coal_barging,
#                 sum(case when sub_activity ='COAL GETTING' then volume end) coal_getting,
#                 sum(case when sub_activity ='HAULING ROM TO PORT' then volume end) coal_hauling,
#                 max(case when sub_activity ='COAL BARGING' then dfi.date end) date_barging,
#                 max(case when sub_activity ='COAL GETTING' then dfi.date end) date_getting,
#                 max(case when sub_activity ='HAULING ROM TO PORT' then dfi.date end) date_hauling
#                 from stock_opname so
#                 left join data_for_inventory dfi on dfi.iup=so.iup and so.pit=dfi.pit and so.seam=dfi.seam and so.date<dfi.date
#                 group by so.sub_act, so.date, so.iup,so.seam,so.pit,so.end_stock,so.is_rom
#             )
#         """)


# class HelpInventory2(models.Model):
#     _name = 'help.inv2'
#     _description = 'Sql View Table Help Inventory'
#     _auto = False

#     date_so = fields.Date("Date SO")
#     inv = fields.Char("INV")
#     iup = fields.Char("IUP")
#     seam = fields.Char("Seam")
#     pit = fields.Char("PIT")
#     stock_update = fields.Float("Stock Update")
#     date_update = fields.Date("Date Update")

#     def init(self):
#         self._cr.execute("""
#             CREATE OR REPLACE VIEW help_inv2
#             AS
#             (
#                 select
#                 inv.date_so,
#                 inv.inv,
#                 inv.iup,
#                 inv.seam,
#                 inv.pit,
#                 case when is_rom = true then end_stock+coal_getting-coal_barging 
#                     when is_rom is null and inv='INV ROM' then end_stock+coal_hauling-coal_getting
#                     when is_rom is null and inv='INV PORT' then end_stock+coal_hauling-coal_barging
#                     end stock_update,
#                 case when is_rom = true then (case when date_getting>date_barging then date_getting else date_barging end)
#                     when is_rom is null and inv='INV ROM' then (case when date_getting>date_hauling then date_getting else date_hauling end)
#                     when is_rom is null and inv='INV PORT' then (case when date_barging>date_hauling then date_barging else date_hauling end)
#                     end date_update
#                 from help_inventory inv
#                 order by inv.date_so,inv.inv
#             )
#         """)


class InventoryResume(models.Model):
    _name = 'inventory.resume'
    _description = 'Sql View Table Inventory Resume'
    _auto = False

    date = fields.Date("Date")
    inv = fields.Char("INV")
    iup = fields.Char("IUP")
    source = fields.Char("Source")
    stock_update = fields.Float("Stock Update")
    date_update = fields.Date("Date Update")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW inventory_resume
            AS
            (
                select
                so.date,
                so.sub_act inv,
                so.iup,
                so.source,
                so.end_stock + coalesce(sum(case when so.source_id=inv.destination_id and inv.date>so.date then inv.volume end),0)
                - coalesce(sum(case when so.source_id=inv.source_id and inv.date>so.date then inv.volume end),0) stock_update,
                case when (
                case when so.date > max(inv.date) then so.date else max(inv.date) end
                    ) is null then so.date 
                    else (
                case when so.date > max(inv.date) then so.date else max(inv.date) end
                    ) end date_update

                -- so.act,so.source_id,coalesce(so.end_stock,0),
                -- coalesce(sum(case when so.source_id=inv.source_id and inv.date>so.date then inv.volume end),0) volume_out,
                -- coalesce(sum(case when so.source_id=inv.destination_id and inv.date>so.date then inv.volume end),0) volume_in,

                from for_inv_laststock so
                    left join (select bu.code iup ,aa.source_id,aa.destination_id,aa.sub_activity,aa.date,aa.volume from for_inv_production aa
                                left join master_bisnis_unit bu on bu.name=aa.iup
                                union all
                                select bu.code iup,bb.source_id,bb.destination_id,bb.activity,bb.loading_date,bb.volume_cb from for_inv_barging bb
                                left join master_bisnis_unit bu on bu.name=bb.iup
                              ) inv
                    on so.iup=inv.iup and (so.source_id=inv.source_id or so.source_id=inv.destination_id)
                group by so.sub_act,so.act,so.date,so.iup,so.source,so.source_id,so.end_stock

                union all

                select
                max(inv.date) last_update,
                inv.sub_activity inventory,bu.code iup,inv.pit || ' seam ' || inv.seam source,
                sum(volume) volume,max(inv.date) dates
                from Inventory_pit inv 
                right join (SELECT distinct bisnis_unit, sub_activity,
                max(date) tgl
                FROM Inventory_pit
                group by bisnis_unit,sub_activity) validasi on validasi.bisnis_unit=inv.bisnis_unit and validasi.tgl=inv.date
                and validasi.sub_activity=inv.sub_activity
                left join master_bisnis_unit bu on bu.active=true and inv.bisnis_unit=bu.name 
                left join res_company cp on cp.name=inv.bisnis_unit
                left join master_sub_activity msa on msa.name=inv.sub_activity
                where inv.date>'2022-12-31'

                group by bu.code,inv.sub_activity,inv.pit,inv.seam,msa.id
                having sum(volume)<>0
            )
        """)
