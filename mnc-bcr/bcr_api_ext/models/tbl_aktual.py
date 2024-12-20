from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


# Actual Production
class ViewActProduction(models.Model):
    _name = 'aktual.production.daily'
    _description = 'Sql View Table Actual'
    _auto = False

    iup = fields.Char("IUP")
    kontraktor = fields.Char("Kontraktor")
    activity = fields.Char("Activity")
    pit = fields.Char("PIT")
    source = fields.Char("Source")
    date = fields.Date("Date")
    shift = fields.Char("Shift")
    volume_ob = fields.Float("Volume OB")
    volume_cg = fields.Float("Volume CG")
    volume_ch = fields.Float("Volume CH")
    dist_ob = fields.Float("Dist OB")
    dist_cg = fields.Float("Dist CG")
    dist_ch = fields.Float("Dist CH")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW aktual_production_daily
            AS
            (select
                iup,kontraktor,--activity,
                pit,source,date,shift,
                sum(case when sub_act='OVERBURDEN' then vol end) volume_ob,
                sum(case when sub_act='COAL GETTING' then vol end) volume_cg,
                sum(case when sub_act='HAULING ROM TO PORT' then vol end) volume_ch,
                sum(case when sub_act='OVERBURDEN' then vol*dist end)/nullif(sum(case when sub_act='OVERBURDEN' then vol end),0) dist_ob,
                sum(case when sub_act='COAL GETTING' then vol*dist end)/nullif(sum(case when sub_act='COAL GETTING' then vol end),0) dist_cg,
                sum(case when sub_act='HAULING ROM TO PORT' then vol*dist end)/nullif(sum(case when sub_act='HAULING ROM TO PORT' then vol end),0) dist_ch

                from
                        (
                        select
                        cp.name iup,
                        kont.name kontraktor,
                        act.name activity,
                        area.name pit,
                        sou.name "source",
                        ap.date_act "date",
                        s.name shift,
                        ap.distance dist,
                        sa.name sub_act,
                        ap.volume vol
                        from act_production ap
                        left join master_activity act on act.id=ap.activity_id
                        left join master_sub_activity sa on sa.id = ap.sub_activity_id
                        left join res_company cp on ap.bu_company_id = cp.id
                        left join res_partner kont on kont.id=ap.kontraktor_id
                        left join master_area area on area.id=ap.area_id
                        left join master_source sou on sou.id=ap.source_id
                        left join master_shift s on ap.shift_id=s.id
                        where ap.active=TRUE
                        and state='complete'
                        and ap.date_act <= '2024-03-21'

                        union all

                        select
                        cp.name iup,
                        kont.name kontraktor,
                        act.name activity,
                        area.name pit,
                        '-' source,
                        ah.date_act "date",
                        s.name shift,
                        0 dist,
                        sa.name sub_act,
                        ah.volume vol
                        from act_hauling ah
                        left join master_activity act on act.id=ah.activity_id
                        left join master_sub_activity sa on sa.id = ah.sub_activity_id
                        left join res_company cp on ah.bu_company_id = cp.id
                        left join res_partner kont on kont.id=ah.kontraktor_id
                        left join master_area area on area.id=ah.area_id
                        left join master_shift s on ah.shift_id=s.id
                        where ah.active=TRUE
                        and state='complete'
                        and ah.date_act <= '2024-03-21'
                        )d
                group by iup,kontraktor,activity,pit,source,date,shift
                --order by iup,kontraktor,pit,date

                union all


                select IUP, kontraktor, pit,source, date,shift,
                sum(case when sub_activity = 'OVERBURDEN' then volume end) volume_ob,
                sum(case when sub_activity = 'COAL GETTING' then volume end) volume_cg,
                sum(case when sub_activity = 'HAULING ROM TO PORT' then volume end) volume_ch,
                sum(case when sub_activity='OVERBURDEN' then volume*distance end)/nullif(sum(case when sub_activity='OVERBURDEN' then volume end),0) dist_ob,
                sum(case when sub_activity='COAL GETTING' then volume*distance end)/nullif(sum(case when sub_activity='COAL GETTING' then volume end),0) dist_cg,
                sum(case when sub_activity='HAULING ROM TO PORT' then volume*distance end)/nullif(sum(case when sub_activity='HAULING ROM TO PORT' then volume end),0) dist_ch

                from
                (
                    select
                    cp.name IUP,
                    kont.name Kontraktor,
                    sa.name sub_activity,
                    area.name pit,
                    frso.name source,
                    act.date_act date,
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
                    where act.active=true
                    and act.state='complete'
                    and act.date_act >= '2024-03-22'
                )dat
            group by IUP, kontraktor, pit,source, date,shift
            order by date desc
            )
        """)


# Actual Rain
class ActRainSlippery(models.Model):
    _name = 'aktual.rainslip.daily'
    _description = 'Sql View Table Actual Rain'
    _auto = False

    iup = fields.Char("IUP")
    kontraktor = fields.Char("Kontraktor")
    pit = fields.Char("PIT")
    date = fields.Date("Date")
    shift = fields.Char("Shift")
    vol_rain = fields.Float("Volume Rain")
    vol_slip = fields.Float("Volume SLIPPERY")
    vol_rf = fields.Float("Volume RAIN FALL")
    vol_rainslip = fields.Float("Volume RAIN SLIP")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW aktual_rainslip_daily
            AS
            (select
                cp.name iup,
                kont.name kontraktor,
                area.name Pit,
                d.date_act date,
                s.name Shift,
                sum(case when pt.name='RAIN' then d.volume end) vol_rain,
                sum(case when pt.name='SLIPPERY' then d.volume end) vol_slip,
                sum(case when pt.name='RAIN FALL' then d.volume end) vol_rf,
                coalesce(sum(case when pt.name='RAIN' then d.volume end),0)+coalesce(sum(case when pt.name='SLIPPERY' then d.volume end),0) vol_rainslip
                from act_delay d
                left join res_company cp on d.bu_company_id=cp.id
                left join product_product pp on pp.id=d.product
                left join product_template pt on pt.id=pp.product_tmpl_id
                left join master_shift s on d.shift_id=s.id
                left join res_partner kont on kont.id=d.kontraktor_id
                left join master_area area on area.id=d.area_id
                where 
                --d.date_act <= '2023-07-11'and 
                pt.name in ('RAIN','SLIPPERY','RAIN FALL')
                and cp.id = any(array[1,2,4])
                and d.state='complete'
                and d.active=TRUE
                group by 
                cp.name,
                kont.name,
                area.name,
                d.date_act,
                s.name

                --order by date_act desc,shift

                union all

                select 
                cp.name iup,
                kont.name kontraktor,
                area.name pit,
                d.date_act date,
                sh.ttype||' SHIFT' shift,
                SUM(dl.rain) vol_rain,
                sum(dl.slippery) vol_slip,
                sum(dl.rainfall) vol_rf,
                SUM(dl.rain)+sum(dl.slippery) vol_rainslip
                from act_delay d
                left join act_delay_line dl on d.id=dl.delay_id
                left join res_company cp on d.bu_company_id=cp.id
                left join res_partner kont on kont.id=d.kontraktor_id
                left join master_area area on area.id=d.area_id
                left join master_shiftmode_line sh on sh.id=dl.shift_line_id
                where rain is not null
                and d.state='complete'
                and d.active=TRUE
                group by 
                cp.name ,
                kont.name ,
                area.name ,
                d.date_act ,
                sh.ttype||' SHIFT'
                order by date desc
            )
        """)
