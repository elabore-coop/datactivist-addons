# -*- coding: utf-8 -*-
from odoo import fields, models, api
import csv
import os
import io
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat

directory = os.path.dirname(__file__)


@api.model
def export_csv(self, export_name):       
    with open(os.path.join(directory, os.pardir, 'static','src',export_name.replace(' ','_')+'.csv'), 'w', newline='') as file:
        """
        TODO : Ajouter le titre des colonnes
        vérifier diff avec original
        """
        #find related export
        export = self.env['ir.exports'].search([('name','=',export_name)])

        #list all fields of this export
        fields = [field.name for field in export.export_fields]

        fields_description_by_name = {field.name:field.field_description for field in self.env['ir.model.fields'].search([('model','=',export.resource)])}
        
        fields_name = [fields_description_by_name[field_name.split('/')[0]] for field_name in fields]

        #list all objects in database of export resource

        objects = self.env[export.resource].search([])            

        writer = csv.writer(file, quoting=1)
        writer.writerow(fields_name)

        for object in objects:
            vals = []
            for field in fields: 
                val = safe_eval('o.'+field.replace('/','.'),{'o':object})
                if isinstance(val,models.BaseModel):
                    if val:
                        val = val.name_get()[0][1]
                    else:
                        val = ''
                if (type(val) is bool) and val == False:
                    val = ''
                vals.append(val)
            writer.writerow(vals)
            


models.Model.export_csv = export_csv