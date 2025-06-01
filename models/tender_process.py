# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

class TenderProcess(models.Model):
    _name = 'tender.process'
    _description = 'Tender Process'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char(string='Tender Number', required=True, copy=False, 
                       default=lambda self: self.env['ir.sequence'].next_by_code('tender.process'))
    
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('invitation_sent', 'Invitation Sent'),
        ('bid_collection', 'Collecting Bids'),
        ('evaluation', 'Evaluation'),
        ('awarded', 'Awarded'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)
    
    estimated_amount = fields.Float(string='Estimated Amount', required=True)
    
    description = fields.Text(string='Description')
    
    bid_submission_deadline = fields.Datetime(
        string='Bid Submission Deadline',
        default=lambda self: datetime.now() + timedelta(days=7)
    )
    
    vendor_ids = fields.Many2many(
        'res.partner',
        'tender_vendor_rel',
        'tender_id',
        'vendor_id',
        string='Invited Vendors',
        domain=[('is_company', '=', True), ('supplier_rank', '>', 0)]
    )
    
    bid_ids = fields.One2many('vendor.bid', 'tender_id', string='Vendor Bids')
    
    winning_bid_id = fields.Many2one('vendor.bid', string='Winning Bid')
    
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company)
    
    def action_send_invitations(self):
        """Kirim undangan tender ke vendor"""
        self.ensure_one()
        if not self.vendor_ids:
            raise UserError('Pilih minimal satu vendor untuk diundang.')
        
        template = self.env.ref('tender_automation.email_template_tender_invitation')
        
        for vendor in self.vendor_ids:
            # Buat bid record untuk setiap vendor
            bid = self.env['vendor.bid'].create({
                'tender_id': self.id,
                'vendor_id': vendor.id,
                'state': 'invited'
            })
            
            # Kirim email
            template.send_mail(
                self.id,
                force_send=True,
                email_values={'recipient_ids': [(4, vendor.id)]}
            )
        
        self.state = 'invitation_sent'
        self.message_post(body=f'Undangan tender telah dikirim ke {len(self.vendor_ids)} vendor.')
    
    def action_start_bid_collection(self):
        """Mulai periode pengumpulan penawaran"""
        self.state = 'bid_collection'
    
    def action_evaluate_bids(self):
        """Evaluasi penawaran"""
        self.state = 'evaluation'
    
    def action_award_tender(self):
        """Berikan tender ke pemenang"""
        if not self.winning_bid_id:
            raise UserError('Pilih pemenang tender terlebih dahulu.')
        
        # Update purchase order dengan vendor pemenang
        self.purchase_order_id.write({
            'partner_id': self.winning_bid_id.vendor_id.id,
            'amount_total': self.winning_bid_id.bid_amount,
        })
        
        self.state = 'awarded'
        self.message_post(body=f'Tender dimenangkan oleh {self.winning_bid_id.vendor_id.name}')
    
    def action_cancel_tender(self):
        """Batalkan tender"""
        self.state = 'cancelled'