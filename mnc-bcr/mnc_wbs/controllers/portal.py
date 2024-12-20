from odoo import http, _
import base64
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class wbsPortal(CustomerPortal):

    @http.route(['/wbs/home'], type='http', auth='public', website=True, sitemap=False)
    def home(self, **kw):
        res = super(wbsPortal, self).home()
        return res
    
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        values['wbs_counts'] = request.env['wbs.report'].search_count([('user_name','=', request.env.user.name)])
        return values
    
    def _prepare_value_report(self,vals):
        attachment_id = False
        res = {}

        if 'report_title' in vals:
            res['title'] = vals['report_title']
        if 'company_id_report' in vals:
            res['company_id'] = vals['company_id_report']

        if 'description' in vals:
            res['description'] =vals['description']
        if 'start_date' in vals:
            res['start_date'] = vals['start_date']
        if 'end_date' in vals:
            res['end_date'] = vals['end_date']
        if 'end_date' in vals:
            res['state'] = 'Draft'
        if 'attachment' in vals:
            res['attachment'] = attachment_id
        return res
        
    @http.route(['/new/wbs_report'], type='http', auth='public', website=True, sitemap=False)
    def new_wbs_form_view(self, **kw):
        company_ids = request.env['res.company'].search([])
        wbs_obj = request.env['wbs.report']
        tnc = request.env['wbs.tnc'].search([])

        if kw:
            vals = self._prepare_value_report(kw)
            wbs_obj_id = wbs_obj.create(vals)

            attch_ids = []

            Attachment = request.env['ir.attachment']
            for file in range(15):
                files = request.httprequest.files.getlist('attachment_'+str(file))
                if files and files[0].filename != '':
                    files = files[0]
                    attachment_id = Attachment.create({
                        'name': files.filename,
                        'type': 'binary',
                        'datas': base64.b64encode(files.read()),
                        'res_model': wbs_obj_id._name,
                        'res_id': wbs_obj_id.id
                    })
                    attch_ids.append(attachment_id.id)
            wbs_obj_id.update({
                'attachment': [(6, 0, attch_ids)],
            })
            if 'submit' in kw:
                wbs_obj_id.submit()

            return request.redirect('/my/wbs_report')
        return request.render('mnc_wbs.new_portal_wbs_report_form_view', {'company_ids':company_ids,'page_name':'new_report', 'tnc':tnc})
    
    @http.route(['/my/wbs_report'], type='http', auth='public', website=True, sitemap=False)
    def wbs_list_view(self, **kw):
        wbs_obj = request.env['wbs.report']
        wbs_data = wbs_obj.search([('user_name','=', request.env.user.name)])
        vals = {'wbs':wbs_data, 'page_name':'my_report'}
        return request.render('mnc_wbs.portal_wbs_report_list_view', vals)
    
    @http.route(['/my/wbs_report_form/<model("wbs.report"):wbs_id>'], type='http', auth='public', website=True, sitemap=False)
    def wbs_form_view(self, wbs_id, **kw):
        wbs_obj = request.env['wbs.report'].search([('id','=',wbs_id.id)])
        company_id = request.env['res.company'].search([])
        file_records = request.env['ir.attachment'].search([('res_model','=','wbs.report'),('res_id','=',wbs_id.id)])
        all_file_names = file_records.mapped('name')

        if kw:
            vals = self._prepare_value_report(kw)
            wbs_obj.update(vals)
            attch_ids = file_records.ids

            Attachment = request.env['ir.attachment']
            for file in range(15):
                attachment  = kw.get('Inputattachment_'+str(file+1))
                if attachment and attachment.filename not in all_file_names:
                    attachment_data = attachment.read()
                    attachment_id = Attachment.create({
                        'name': attachment.filename,
                        'type': 'binary',
                        'datas': base64.b64encode(attachment_data),
                        'res_model': wbs_obj._name,
                        'res_id': wbs_obj.id,
                        'public': True
                    })
                    attch_ids.append(attachment_id.id)
                deleted_file  = kw.get('deleted_file_'+str(file+1))
                if deleted_file:
                    deleted_file = file_records.search([('id','=',deleted_file)])
                    deleted_file.update({
                                    'res_model': False,
                                    'res_id': False,
                                })
                    attch_ids.remove(deleted_file.id)
            wbs_obj.update({
                'attachment': [(6, 0, attch_ids)],
            })
            if 'submit' in kw:
                wbs_obj.submit()
            return request.redirect('/my/wbs_report')


        files = []     
        for file in file_records:
            download_url = '/web/content/%s' % (file.id) + '?download=true'
            files.append({
                'name': file.name,
                'download_url': download_url,
                'datas':file.datas,
                'id':file.id,
            })
        vals = {'wbs':wbs_id, 'page_name':'my_report_form','company_ids':company_id, 'files': files, 'len_files':len(wbs_id.attachment)}
        return request.render('mnc_wbs.portal_wbs_report_form_view', vals)