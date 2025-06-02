# -*- coding: utf-8 -*-
# models/res_company.py

from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    tender_threshold = fields.Float(
        string='Tender Threshold',
        default=200000000.0,  # 200 million IDR
        help='Minimum purchase order amount that requires tender process',
        company_dependent=True
    )