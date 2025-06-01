# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    tender_required = fields.Boolean(
        string='Tender Required',
        compute='_compute_tender_required',
        store=True
    )
    
    tender_process_id = fields.Many2one(
        'tender.process',
        string='Tender Process',
        readonly=True
    )
    
    tender_threshold = fields.Float(
        string='Tender Threshold',
        default=200000000.0,  # 200 juta
        company_dependent=True
    )
    
    @api.depends('amount_total')
    def _compute_tender_required(self):
        for order in self:
            order.tender_required = order.amount_total >= order.tender_threshold
    
    def button_confirm(self):
        """Override confirm - hanya bisa confirm jika tender sudah selesai atau tidak perlu tender"""
        for order in self:
            if order.tender_required and not order.tender_process_id:
                raise UserError(
                    'Purchase Order ini memerlukan proses tender karena nilainya melebihi Rp 200,000,000. '
                    'Silakan buat tender terlebih dahulu sebelum confirm.'
                )
            elif order.tender_required and order.tender_process_id and order.tender_process_id.state != 'awarded':
                raise UserError(
                    'Purchase Order ini tidak dapat dikonfirmasi karena proses tender belum selesai. '
                    f'Status tender saat ini: {dict(order.tender_process_id._fields["state"].selection)[order.tender_process_id.state]}'
                )
        return super().button_confirm()
    
    @api.onchange('order_line')
    def _onchange_order_line_tender_check(self):
        """Check tender requirement saat order line berubah"""
        if self.tender_required and not self.tender_process_id:
            return {
                'warning': {
                    'title': 'Tender Diperlukan!',
                    'message': f'Nilai total PO (Rp {self.amount_total:,.0f}) melebihi batas tender (Rp {self.tender_threshold:,.0f}). '
                              'Anda perlu membuat proses tender sebelum bisa konfirmasi PO ini.'
                }
            }
    
    def action_create_tender(self):
        """Action untuk membuat tender process"""
        self.ensure_one()
        tender = self.env['tender.process'].create({
            'name': f'Tender - {self.name}',
            'purchase_order_id': self.id,
            'estimated_amount': self.amount_total,
            'description': f'Tender untuk PO {self.name}',
            'company_id': self.company_id.id,
        })
        self.tender_process_id = tender.id
        
        return {
            'name': 'Tender Process',
            'type': 'ir.actions.act_window',
            'res_model': 'tender.process',
            'res_id': tender.id,
            'view_mode': 'form',
            'target': 'current',
        }