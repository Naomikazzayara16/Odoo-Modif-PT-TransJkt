# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    """Extend model res.partner untuk menambahkan informasi rating vendor"""
    _inherit = 'res.partner'

    # Rating vendor (skala 1-5)
    vendor_rating = fields.Float(
        string='Vendor Rating', 
        readonly=True, 
        default=0.0,
        help='Rating vendor berdasarkan evaluasi (skala 1-5)'
    )
    
    # Jumlah evaluasi
    vendor_evaluation_count = fields.Integer(
        string='Jumlah Evaluasi', 
        readonly=True, 
        default=0,
        help='Total jumlah evaluasi yang telah dilakukan'
    )
    
    # Tanggal evaluasi terakhir  
    last_evaluation_date = fields.Datetime(
        string='Evaluasi Terakhir',
        readonly=True,
        help='Tanggal evaluasi vendor terakhir'
    )
    
    # Status vendor berdasarkan rating
    vendor_status = fields.Selection(
        selection=[
            ('excellent', 'Excellent (4.5-5.0)'),
            ('good', 'Good (3.5-4.4)'),
            ('average', 'Average (2.5-3.4)'),
            ('poor', 'Poor (1.5-2.4)'),
            ('very_poor', 'Very Poor (0-1.4)'),
            ('not_evaluated', 'Belum Dievaluasi')
        ],
        string='Status Vendor',
        compute='_compute_vendor_status',
        store=True,
        help='Status vendor berdasarkan rating rata-rata evaluasi'
    )
    
    # One2many relation ke evaluasi
    vendor_evaluation_ids = fields.One2many(
        'vendor.evaluation', 
        'partner_id', 
        string='Evaluasi Vendor',
        readonly=True
    )

    @api.depends('vendor_rating', 'vendor_evaluation_count')
    def _compute_vendor_status(self):
        """Menentukan status vendor berdasarkan rating"""
        for partner in self:
            if partner.vendor_evaluation_count == 0:
                partner.vendor_status = 'not_evaluated'
            elif partner.vendor_rating >= 4.5:
                partner.vendor_status = 'excellent'
            elif partner.vendor_rating >= 3.5:
                partner.vendor_status = 'good'
            elif partner.vendor_rating >= 2.5:
                partner.vendor_status = 'average'
            elif partner.vendor_rating >= 1.5:
                partner.vendor_status = 'poor'
            else:
                partner.vendor_status = 'very_poor'

    def action_view_vendor_evaluations(self):
        """Action untuk melihat semua evaluasi vendor"""
        self.ensure_one()
        return {
            'name': f'Evaluasi Vendor - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'vendor.evaluation',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }