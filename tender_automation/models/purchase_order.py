# -*- coding: utf-8 -*-
# models/purchase_order.py

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    tender_required = fields.Boolean(
        string='Tender Required',
        compute='_compute_tender_required',
        store=True,
        help='Automatically set to True if order amount exceeds tender threshold'
    )
    
    tender_process_id = fields.Many2one(
        'tender.process',
        string='Tender Process',
        readonly=True,
        ondelete='restrict'
    )
    
    tender_threshold = fields.Float(
        string='Tender Threshold',
        related='company_id.tender_threshold',
        readonly=True
    )
    
    @api.depends('amount_total', 'company_id.tender_threshold')
    def _compute_tender_required(self):
        for order in self:
            order.tender_required = order.amount_total >= order.company_id.tender_threshold
    
    @api.constrains('state', 'tender_required', 'tender_process_id')
    def _check_tender_completion(self):
        """Ensure tender is completed before confirming PO"""
        for order in self:
            if order.state in ['purchase', 'done'] and order.tender_required:
                if not order.tender_process_id:
                    raise ValidationError(
                        f'Purchase Order {order.name} requires tender process '
                        f'as amount ({order.amount_total:,.0f}) exceeds threshold '
                        f'({order.tender_threshold:,.0f}). Please create tender first.'
                    )
                elif order.tender_process_id.state != 'awarded':
                    raise ValidationError(
                        f'Cannot confirm PO {order.name}. '
                        f'Tender status: {order.tender_process_id.state_display}'
                    )
    
    def button_confirm(self):
        """Override confirm to check tender requirements"""
        self._check_tender_completion()
        return super().button_confirm()
    
    @api.onchange('order_line')
    def _onchange_order_line_tender_check(self):
        """Show warning when tender is required"""
        if self.tender_required and not self.tender_process_id:
            return {
                'warning': {
                    'title': 'Tender Required!',
                    'message': (
                        f'Total amount (Rp {self.amount_total:,.0f}) exceeds '
                        f'tender threshold (Rp {self.tender_threshold:,.0f}). '
                        'Please create tender process before confirming.'
                    )
                }
            }
    
    def action_create_tender(self):
        """Create tender process for this PO"""
        self.ensure_one()
        if self.tender_process_id:
            raise UserError('Tender process already exists for this PO.')
        
        tender = self.env['tender.process'].create({
            'name': f'Tender for {self.name}',
            'purchase_order_id': self.id,
            'estimated_amount': self.amount_total,
            'description': f'Tender process for Purchase Order {self.name}',
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
    
    def action_view_tender(self):
        """View related tender process"""
        self.ensure_one()
        if not self.tender_process_id:
            raise UserError('No tender process found for this PO.')
        
        return {
            'name': 'Tender Process',
            'type': 'ir.actions.act_window',
            'res_model': 'tender.process',
            'res_id': self.tender_process_id.id,
            'view_mode': 'form',
        }
