# -*- coding: utf-8 -*-
# models/tender_process.py

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class TenderProcess(models.Model):
    _name = 'tender.process'
    _description = 'Tender Process'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'display_name'
    
    name = fields.Char(
        string='Tender Reference',
        required=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('tender.process') or 'New'
    )
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    city = fields.Char(string='City')
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order',
        required=True,
        ondelete='cascade'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('invitation_sent', 'Invitation Sent'),
        ('bid_collection', 'Collecting Bids'),
        ('evaluation', 'Under Evaluation'),
        ('awarded', 'Awarded'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True, required=True)
    
    state_display = fields.Char(
        string='Status',
        compute='_compute_state_display'
    )
    
    estimated_amount = fields.Float(
        string='Estimated Amount',
        required=True,
        tracking=True
    )
    
    description = fields.Text(string='Description')
    
    bid_submission_deadline = fields.Datetime(
        string='Bid Submission Deadline',
        default=lambda self: fields.Datetime.now() + timedelta(days=7),
        required=True,
        tracking=True
    )

    supplier_rank = fields.Integer(string="Supplier Rank")

    vendor_ids = fields.Many2many(
        'res.partner',
        'tender_vendor_rel',
        'tender_id',
        'vendor_id',
        string='Invited Vendors',
        domain=[('is_company', '=', True), ('supplier_rank', '>', 0)]
    )
    
    bid_ids = fields.One2many(
        'vendor.bid',
        'tender_id',
        string='Vendor Bids'
    )
    
    
    winning_bid_id = fields.Many2one(
        'vendor.bid',
        string='Winning Bid',
        domain="[('tender_id', '=', id), ('state', '=', 'submitted')]"
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    
    # Computed fields
    bid_count = fields.Integer(
        string='Bid Count',
        compute='_compute_bid_count'
    )
    
    submitted_bid_count = fields.Integer(
        string='Submitted Bids',
        compute='_compute_bid_count'
    )
    
    @api.depends('name', 'purchase_order_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.purchase_order_id:
                record.display_name = f"{record.name} - {record.purchase_order_id.name}"
            else:
                record.display_name = record.name or 'New'
    
    @api.depends('state')
    def _compute_state_display(self):
        state_dict = dict(self._fields['state'].selection)
        for record in self:
            record.state_display = state_dict.get(record.state, record.state)
    
    @api.depends('bid_ids', 'bid_ids.state')
    def _compute_bid_count(self):
        for record in self:
            record.bid_count = len(record.bid_ids)
            record.submitted_bid_count = len(record.bid_ids.filtered(lambda b: b.state == 'submitted'))
    
    @api.constrains('bid_submission_deadline')
    def _check_deadline(self):
        for record in self:
            if record.bid_submission_deadline <= fields.Datetime.now():
                raise ValidationError('Bid submission deadline must be in the future.')
    
    @api.constrains('winning_bid_id', 'state')
    def _check_winning_bid(self):
        for record in self:
            if record.state == 'awarded' and not record.winning_bid_id:
                raise ValidationError('Winning bid must be selected when tender is awarded.')
    
    def action_send_invitations(self):
        """Send tender invitations to vendors"""
        self.ensure_one()
        if not self.vendor_ids:
            raise UserError('Please select at least one vendor to invite.')
        
        if self.state != 'draft':
            raise UserError('Invitations can only be sent from draft state.')
        
        # Create bid records for each vendor
        for vendor in self.vendor_ids:
            existing_bid = self.bid_ids.filtered(lambda b: b.vendor_id == vendor)
            if not existing_bid:
                self.env['vendor.bid'].create({
                    'tender_id': self.id,
                    'vendor_id': vendor.id,
                    'state': 'invited'
                })
        
        # Send email invitations
        template = self.env.ref('tender_automation.email_template_tender_invitation', False)
        if template:
            for vendor in self.vendor_ids:
                template.send_mail(
                    self.id,
                    force_send=True,
                    email_values={'recipient_ids': [(4, vendor.id)]}
                )
        
        self.state = 'invitation_sent'
        self.message_post(
            body=f'Tender invitations sent to {len(self.vendor_ids)} vendors.',
            subject='Tender Invitations Sent'
        )
    
    def action_start_bid_collection(self):
        """Start bid collection period"""
        self.ensure_one()
        if self.state != 'invitation_sent':
            raise UserError('Can only start bid collection after sending invitations.')
        
        self.state = 'bid_collection'
        self.message_post(body='Bid collection period started.')
    
    def action_evaluate_bids(self):
        """Start bid evaluation"""
        self.ensure_one()
        if self.state != 'bid_collection':
            raise UserError('Can only evaluate bids during collection period.')
        
        if not self.bid_ids.filtered(lambda b: b.state == 'submitted'):
            raise UserError('No submitted bids to evaluate.')
        
        self.state = 'evaluation'
        self.message_post(body='Bid evaluation started.')
    
    def action_award_tender(self):
        """Award tender to winning bidder"""
        self.ensure_one()
        if self.state != 'evaluation':
            raise UserError('Can only award tender during evaluation phase.')
        
        if not self.winning_bid_id:
            raise UserError('Please select winning bid first.')
        
        # Update winning bid
        self.winning_bid_id.state = 'won'
        
        # Update losing bids
        losing_bids = self.bid_ids.filtered(lambda b: b.id != self.winning_bid_id.id and b.state == 'submitted')
        losing_bids.write({'state': 'lost'})
        
        # Update purchase order
        self.purchase_order_id.write({
            'partner_id': self.winning_bid_id.vendor_id.id,
        })
        
        self.state = 'awarded'
        self.message_post(
            body=f'Tender awarded to {self.winning_bid_id.vendor_id.name} '
                 f'with bid amount: {self.winning_bid_id.bid_amount:,.0f}',
            subject='Tender Awarded'
        )
    
    def action_cancel_tender(self):
        """Cancel tender process"""
        self.ensure_one()
        if self.state == 'awarded':
            raise UserError('Cannot cancel awarded tender.')
        
        self.state = 'cancelled'
        self.message_post(body='Tender process cancelled.')
    
    def action_reset_to_draft(self):
        """Reset tender to draft (only from cancelled state)"""
        self.ensure_one()
        if self.state != 'cancelled':
            raise UserError('Can only reset cancelled tenders to draft.')
        
        self.state = 'draft'
        self.message_post(body='Tender reset to draft.')
    
    def action_view_bids(self):
        """View all bids for this tender"""
        self.ensure_one()
        return {
            'name': f'Bids for {self.display_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'vendor.bid',
            'domain': [('tender_id', '=', self.id)],
            'view_mode': 'tree,form',
            'context': {'default_tender_id': self.id}
        }