# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockPicking(models.Model):
    """Extend model stock.picking untuk menambahkan evaluasi vendor"""
    _inherit = 'stock.picking'

    # Relasi ke evaluasi vendor
    vendor_evaluation_id = fields.Many2one(
        'vendor.evaluation', 
        string='Evaluasi Vendor',
        help='Evaluasi vendor untuk penerimaan ini'
    )
    
    # Flag untuk menandai apakah sudah dievaluasi
    is_evaluated = fields.Boolean(
        string='Sudah Dievaluasi', 
        compute='_compute_is_evaluated',
        store=True,
        help='Menandai apakah penerimaan ini sudah dievaluasi'
    )
    
    # Skor vendor untuk penerimaan ini
    vendor_score = fields.Float(
        string='Skor Vendor',
        related='vendor_evaluation_id.total_score',
        readonly=True,
        help='Total skor evaluasi vendor'
    )

    @api.depends('vendor_evaluation_id', 'vendor_evaluation_id.evaluation_status')
    def _compute_is_evaluated(self):
        """Menentukan apakah picking sudah dievaluasi"""
        for picking in self:
            picking.is_evaluated = bool(
                picking.vendor_evaluation_id and 
                picking.vendor_evaluation_id.evaluation_status == 'done'
            )

    def action_create_vendor_evaluation(self):
        """Action untuk membuat evaluasi vendor baru"""
        # Cek apakah sudah ada evaluasi
        if self.vendor_evaluation_id:
            # Jika sudah ada, buka yang existing
            return {
                'name': 'Evaluasi Vendor',
                'type': 'ir.actions.act_window',
                'res_model': 'vendor.evaluation',
                'res_id': self.vendor_evaluation_id.id,
                'view_mode': 'form',
                'target': 'new'
            }
        
        # Jika belum ada, buat baru
        evaluation = self.env['vendor.evaluation'].create({
            'picking_id': self.id,
            'partner_id': self.partner_id.id,
        })
        
        # Link evaluasi ke picking
        self.vendor_evaluation_id = evaluation.id
        
        return {
            'name': 'Evaluasi Vendor',
            'type': 'ir.actions.act_window',
            'res_model': 'vendor.evaluation',
            'res_id': evaluation.id,
            'view_mode': 'form',
            'target': 'new'
        }

    def action_view_vendor_evaluation(self):
        """Action untuk melihat evaluasi vendor yang sudah ada"""
        if not self.vendor_evaluation_id:
            return self.action_create_vendor_evaluation()
            
        return {
            'name': 'Evaluasi Vendor',
            'type': 'ir.actions.act_window',
            'res_model': 'vendor.evaluation',
            'res_id': self.vendor_evaluation_id.id,
            'view_mode': 'form',
            'target': 'new'
        }