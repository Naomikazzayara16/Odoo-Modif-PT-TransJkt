# -*- coding: utf-8 -*-
# models/res_partner.py

from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Add computed field for tender-related information
    tender_bid_count = fields.Integer(
        string='Tender Bids',
        compute='_compute_tender_stats'
    )
    
    tender_won_count = fields.Integer(
        string='Tenders Won',
        compute='_compute_tender_stats'
    )
    
    def _compute_tender_stats(self):
        for partner in self:
            if partner.is_company and partner.supplier_rank > 0:
                bids = self.env['vendor.bid'].search([('vendor_id', '=', partner.id)])
                partner.tender_bid_count = len(bids)
                partner.tender_won_count = len(bids.filtered(lambda b: b.state == 'won'))
            else:
                partner.tender_bid_count = 0
                partner.tender_won_count = 0
    
    def action_view_tender_bids(self):
        """View all tender bids for this vendor"""
        self.ensure_one()
        return {
            'name': f'Tender Bids - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'vendor.bid',
            'domain': [('vendor_id', '=', self.id)],
            'view_mode': 'tree,form',
            'context': {'default_vendor_id': self.id}
        }