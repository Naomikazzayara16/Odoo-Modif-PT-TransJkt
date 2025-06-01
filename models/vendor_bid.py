# -*- coding: utf-8 -*-

from odoo import models, fields, api

class VendorBid(models.Model):
    _name = 'vendor.bid'
    _description = 'Vendor Bid'
    _order = 'bid_amount asc'
    
    tender_id = fields.Many2one('tender.process', string='Tender', required=True, ondelete='cascade')
    
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True)
    
    state = fields.Selection([
        ('invited', 'Invited'),
        ('submitted', 'Submitted'),
        ('evaluated', 'Evaluated'),
        ('won', 'Won'),
        ('lost', 'Lost')
    ], default='invited')
    
    bid_amount = fields.Float(string='Bid Amount')
    
    submission_date = fields.Datetime(string='Submission Date')
    
    technical_score = fields.Float(string='Technical Score (0-100)')
    
    price_score = fields.Float(string='Price Score (0-100)')
    
    total_score = fields.Float(string='Total Score', compute='_compute_total_score', store=True)
    
    notes = fields.Text(string='Notes')
    
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    
    @api.depends('technical_score', 'price_score')
    def _compute_total_score(self):
        for bid in self:
            # Bobot: 70% teknis, 30% harga
            bid.total_score = (bid.technical_score * 0.7) + (bid.price_score * 0.3)
    
    def action_submit_bid(self):
        """Submit penawaran"""
        self.state = 'submitted'
        self.submission_date = fields.Datetime.now()
    
    def action_evaluate(self):
        """Evaluasi penawaran"""
        self.state = 'evaluated'