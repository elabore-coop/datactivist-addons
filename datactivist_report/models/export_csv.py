# -*- coding: utf-8 -*-
from odoo import fields, models, api

import os
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat
from odoo.addons.web.controllers.main import CSVExport
from odoo.http import request

directory = os.path.dirname(__file__)


@api.model
def export_csv(self, export_name):       
    
    with open(os.path.join(directory, os.pardir, 'static','src',export_name.replace(' ','_')+'.csv'), 'wb') as file:      

        #find related export
        export = self.env['ir.exports'].search([('name','=',export_name)])

        #list all fields of this export
        fields = [field.name for field in export.export_fields]
                
        #list all objects in database of export resource
        records = self.env[export.resource].search([])            

        #get data from record
        export_data = records.export_data(fields).get('datas',[])

        #execute function from CSV Export odoo core
        csv = CSVExport()
        response_data = csv.from_data(fields, export_data)
        
        #write response
        file.write(response_data)

        


models.Model.export_csv = export_csv