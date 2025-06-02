# -*- coding: utf-8 -*-
# models/vendor_bid.py

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class VendorBid(models.Model):
    _name = 'vendor.bid'
    _description = 'Vendor Bid'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'bid_amount asc, submission_date desc'
    _rec_name = 'display_name'
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    tender_id = fields.Many2one(
        'tender.process',
        string='Tender Process',
        required=True,
        ondelete='cascade'
    )
    
    
    vendor_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        required=True,
        domain=[('is_company', '=', True), ('supplier_rank', '>', 0)]
    )
    
    state = fields.Selection([
        ('invited', 'Invited'),
        ('submitted', 'Submitted'),
        ('won', 'Won'),
        ('lost', 'Lost')
    ], default='invited', tracking=True, required=True)
    
    bid_amount = fields.Float(
        string='Bid Amount',
        tracking=True
    )
    
    submission_date = fields.Datetime(
        string='Submission Date',
        readonly=True
    )
    
    technical_score = fields.Float(
        string='Technical Score (0-100)',
        help='Technical evaluation score out of 100'
    )
    
    price_score = fields.Float(
        string='Price Score (0-100)',
        help='Price evaluation score out of 100'
    )
    
    total_score = fields.Float(
        string='Total Score',
        compute='_compute_total_score',
        store=True,
        help='Weighted total score (70% technical + 30% price)'
    )
    
    notes = fields.Text(string='Notes')
    
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'vendor_bid_attachment_rel',
        'bid_id',
        'attachment_id',
        string='Attachments'
    )
    
    company_id = fields.Many2one(
        'res.company',
        related='tender_id.company_id',
        store=True
    )
    
    # Computed fields
    is_winning_bid = fields.Boolean(
        string='Is Winning Bid',
        compute='_compute_is_winning_bid'
    )
    
    @api.depends('tender_id.name', 'vendor_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.tender_id and record.vendor_id:
                record.display_name = f"{record.tender_id.name} - {record.vendor_id.name}"
            else:
                record.display_name = 'New Bid'
    
    @api.depends('technical_score', 'price_score')
    def _compute_total_score(self):
        for bid in self:
            # Weight: 70% technical, 30% price
            bid.total_score = (bid.technical_score * 0.7) + (bid.price_score * 0.3)
    
    @api.depends('tender_id.winning_bid_id')
    def _compute_is_winning_bid(self):
        for record in self:
            record.is_winning_bid = record.tender_id.winning_bid_id == record
    
    @api.constrains('technical_score', 'price_score')
    def _check_scores(self):
        for bid in self:
            if bid.technical_score < 0 or bid.technical_score > 100:
                raise ValidationError('Technical score must be between 0 and 100.')
            if bid.price_score < 0 or bid.price_score > 100:
                raise ValidationError('Price score must be between 0 and 100.')
    
    @api.constrains('bid_amount')
    def _check_bid_amount(self):
        for bid in self:
            if bid.state == 'submitted' and bid.bid_amount <= 0:
                raise ValidationError('Bid amount must be greater than 0 for submitted bids.')
    
    def action_submit_bid(self):
        """Submit the bid"""
        self.ensure_one()
        if self.state != 'invited':
            raise UserError('Only invited bids can be submitted.')
        
        if self.bid_amount <= 0:
            raise UserError('Bid amount must be greater than 0.')
        
        if self.tender_id.state not in ['invitation_sent', 'bid_collection']:
            raise UserError('Tender is not accepting bids at this time.')
        
        if fields.Datetime.now() > self.tender_id.bid_submission_deadline:
            raise UserError('Bid submission deadline has passed.')
        
        self.write({
            'state': 'submitted',
            'submission_date': fields.Datetime.now()
        })
        
        self.message_post(
            body=f'Bid submitted with amount: {self.bid_amount:,.0f}',
            subject='Bid Submitted'
        )
    
    def action_view_tender(self):
        """View related tender process"""
        self.ensure_one()
        return {
            'name': 'Tender Process',
            'type': 'ir.actions.act_window',
            'res_model': 'tender.process',
            'res_id': self.tender_id.id,
            'view_mode': 'form',
        }
