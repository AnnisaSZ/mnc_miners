from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class ViewPlanning(models.Model):
    _name = 'plan.production.daily'
    _description = 'Sql View Table Planning'
    _auto = False

    plan_group_id = fields.Integer("Plan Group")
    category = fields.Char("Category")
    iup = fields.Char("IUP")
    kontraktor = fields.Char("Kontraktor")
    activity = fields.Char("Activity")
    pit = fields.Char("PIT")
    source = fields.Char("Source")
    tahun = fields.Char("Tahun")
    bulan = fields.Char("Bulan")
    distance = fields.Float("Distance")
    volume_cg = fields.Float("Volume CG")
    volume_ob = fields.Float("Volume OB")
    volume_ch = fields.Float("Volume CH")
    date = fields.Date("Date")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW plan_production_daily
             AS
            (select
                plan.atth_monthly_id plan_group_id,
                cat.name category,
                iup.name iup,
                kont.name kontraktor,
                act.name Activity,
                --subact.name Sub_Activity,
                area.name pit,
                sou.name source,
                pl_gr.selected_years tahun,
                TO_CHAR(
                    TO_DATE (pl_gr.period_month::text, 'MM'), 'Month'
                    ) bulan,
                plan.date_start AS date,
                plan.distance_plan distance,
                --plan.id id_detail,
                sum(det_cg.volume_seam) volume_cg,
                sum(det_ob.volume_seam) volume_ob,
                sum(det_ch.volume_seam) volume_ch
                from planning_opr plan
                    left join planning_type_option cat on cat.id=plan.option_id
                    left join res_company iup on iup.id=plan.company_id
                    left join res_partner kont on kont.id=plan.kontraktor_id
                    left join master_activity act on act.id=plan.activity_id
                    left join master_sub_activity subact on subact.id=plan.sub_activity_id
                    left join master_area area on area.id=plan.area_id
                    left join master_source sou on sou.id=plan.source_id
                    left join seam_code_plan_line det_cg on det_cg.planning_id=plan.id and subact.name='COAL GETTING'
                    left join seam_code_plan_line det_ob on det_ob.planning_product_id=plan.id and subact.name='OVERBURDEN'
                    left join seam_code_plan_line det_ch on det_ch.planning_id=plan.id and subact.name='HAULING ROM TO PORT'
                    left join planning_month_attachment pl_gr on pl_gr.id=plan.atth_monthly_id
                where plan.active=true
                and plan.state='complete'
                and is_monthly=true
                --and subact.name='COAL GETTING'

                group by plan.atth_monthly_id,
                cat.name,
                iup.name,
                kont.name,
                act.name,
                --subact.name,
                area.name,
                sou.name,
                plan.date_start,
                plan.date_end,
                plan.distance_plan,
                pl_gr.selected_years,
                TO_CHAR(
                    TO_DATE (pl_gr.period_month::text, 'MM'), 'Month'
                    )

                order by category,iup,kontraktor,pit,plan.date_start
            )
        """)


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
    volume_ob = fields.Float("Volume OB")
    volume_cg = fields.Float("Volume CG")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW aktual_production_daily
            AS
            (select
                iup,kontraktor,activity,pit,source,date,
                sum(case when sub_act='OVERBURDEN' then vol end) volume_ob,
                sum(case when sub_act='COAL GETTING' then vol end) volume_cg
                from
                (
                    select
                    cp.name iup,
                    kont.name kontraktor,
                    act.name activity,
                    area.name pit,
                    sou.name "source",
                    ap.date_act "date",
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
                    where ap.active=TRUE
                    and state='complete'
                    --and sa.name='OVERBURDEN'
                    --and cp.id  = any(iup)
                )d
                group by iup,kontraktor,activity,pit,source,date
                order by iup,kontraktor,pit,date
            )
        """)
