from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


# Planning Daily
class ViewPlanningDaily(models.Model):
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
    tahun_plan = fields.Char("Tahun Plan")
    # bulan_period = fields.Char("Bulan Period")
    bulan_plan = fields.Char("Bulan Plan")
    date = fields.Date("Date")
    volume_cg = fields.Float("Volume CG")
    volume_ob = fields.Float("Volume OB")
    volume_ch = fields.Float("Volume CH")
    dist_cg = fields.Float("Distance CG")
    dist_ob = fields.Float("Distance OB")
    dist_ch = fields.Float("Distance CH")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW plan_production_daily
             AS
            (
                select
                plan.atth_monthly_id plan_group_id,
                cat.name category,
                iup.name iup,
                kont.name kontraktor,
                act.name activity,
                --subact.name Sub_Activity,
                area.name pit,
                sou.name "source",
                pl_gr.selected_years tahun_plan,
                TO_CHAR(
                    TO_DATE (pl_gr.period_month::text, 'MM'), 'MM'
                    ) bulan_plan,
                plan.date_start "date",
                --plan.id id_detail,
                sum(det_cg.volume_seam) volume_cg,
                sum(det_ob.volume_seam) volume_ob,
                sum(det_ch.volume_seam) volume_ch,
                sum(det_cg.volume_seam*plan.distance_plan)/nullif(sum(det_cg.volume_seam),0) dist_cg,
                sum(det_ob.volume_seam*plan.distance_plan)/nullif(sum(det_ob.volume_seam),0) dist_ob,
                sum(det_ch.volume_seam*plan.distance_plan)/nullif(sum(det_ch.volume_seam),0) dist_ch
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
                pl_gr.selected_years,
                TO_CHAR(
                    TO_DATE (pl_gr.period_month::text, 'MM'), 'MM'
                    )

                --order by category,iup,kontraktor,pit,plan.date_start;

                union all

                select
                plan.atth_monthly_id plan_group_id,
                cat.name category,
                iup.name iup,
                kont.name kontraktor,
                act.name activity,
                --subact.name Sub_Activity,
                area.name pit,
                sou.name "source",
                pl_gr.selected_years tahun_plan,
                TO_CHAR(
                    TO_DATE (pl_gr.period_month::text, 'MM'), 'MM'
                    ) bulan_plan,
                generate_series(
                    plan.date_start::timestamp,
                    plan.date_end::timestamp,
                    interval '1 day'
                    )::date as date,
                --(plan.date_end - plan.date_start)::integer+1 hari,
                --plan.id id_detail,
                sum(det_cg.volume_seam)/((plan.date_end - plan.date_start)::integer+1) volume_cg,
                sum(det_ob.volume_seam)/((plan.date_end - plan.date_start)::integer+1) volume_ob,
                sum(det_ch.volume_seam)/((plan.date_end - plan.date_start)::integer+1) volume_ch,
                sum(det_cg.volume_seam*plan.distance_plan)/nullif(sum(det_cg.volume_seam),0) dist_cg,
                sum(det_ob.volume_seam*plan.distance_plan)/nullif(sum(det_ob.volume_seam),0) dist_ob,
                sum(det_ch.volume_seam*plan.distance_plan)/nullif(sum(det_ch.volume_seam),0) dist_ch
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
                and is_yearly=true
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
                pl_gr.selected_years,
                TO_CHAR(
                    TO_DATE (pl_gr.period_month::text, 'MM'), 'MM'
                    )

                order by category,iup,kontraktor,pit,date
            )
        """)
