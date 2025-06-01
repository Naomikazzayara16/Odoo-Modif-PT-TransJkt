# custom_addons/vendor_evaluations/models/vendor_evaluation.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VendorEvaluation(models.Model):
    """Model untuk menyimpan evaluasi vendor pada setiap penerimaan barang"""
    _name = 'vendor.evaluation'
    _description = 'Vendor Evaluation'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Untuk chatter support

    # Relasi ke stock picking (penerimaan barang)
    picking_id = fields.Many2one('stock.picking', string='Receipt', required=True, ondelete='cascade')
    
    # Relasi ke vendor/partner
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    
    # Kriteria evaluasi (skala 1-100)
    contract_status_score = fields.Float(
        string='Status Kontrak Score', 
        help='Skor ketepatan waktu pengiriman (1-100)',
        default=0.0
    )
    
    unit_price_score = fields.Float(
        string='Harga Unit Score', 
        help='Skor kesesuaian harga dengan kontrak (1-100)',
        default=0.0
    )
    
    shipping_cost_score = fields.Float(
        string='Biaya Pengiriman Score', 
        help='Skor efisiensi biaya pengiriman (1-100)',
        default=0.0
    )
    
    # Skor total (otomatis dihitung berdasarkan pembobotan)
    total_score = fields.Float(
        string='Total Score', 
        compute='_compute_total_score', 
        store=True,
        help='Skor total berdasarkan pembobotan: Status Kontrak 30%, Harga Unit 40%, Biaya Pengiriman 30%'
    )
    
    # Status evaluasi
    evaluation_status = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Catatan tambahan
    notes = fields.Text(string='Catatan Evaluasi')
    
    # Tanggal evaluasi
    evaluation_date = fields.Datetime(string='Tanggal Evaluasi', default=fields.Datetime.now, tracking=True)
    
    # Evaluator
    evaluator_id = fields.Many2one('res.users', string='Evaluator', default=lambda self: self.env.user, tracking=True)

    # Nomor evaluasi (opsional, jika ingin nomor unik)
    name = fields.Char(string='Nomor Evaluasi', readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('vendor.evaluation'))

    @api.depends('contract_status_score', 'unit_price_score', 'shipping_cost_score')
    def _compute_total_score(self):
        """Menghitung total skor berdasarkan pembobotan"""
        for record in self:
            # Pembobotan: Status Kontrak 30%, Harga Unit 40%, Biaya Pengiriman 30%
            record.total_score = (
                (record.contract_status_score * 0.3) + 
                (record.unit_price_score * 0.4) + 
                (record.shipping_cost_score * 0.3)
            )

    @api.constrains('contract_status_score', 'unit_price_score', 'shipping_cost_score')
    def _check_score_range(self):
        """Validasi bahwa skor harus dalam rentang 0-100"""
        for record in self:
            scores = [
                record.contract_status_score,
                record.unit_price_score,
                record.shipping_cost_score
            ]
            for score in scores:
                if score < 0 or score > 100:
                    raise ValidationError('Skor evaluasi harus dalam rentang 0-100')

    def action_complete_evaluation(self):
        """Action untuk menyelesaikan evaluasi dan update rating vendor"""
        for record in self:
            if record.total_score < 75:
                record.message_post(body='Peringatan: Skor evaluasi (%s) di bawah ambang batas 75' % record.total_score)
            record.evaluation_status = 'done'
            # Update rating vendor
            record._update_vendor_rating()
        
    def _update_vendor_rating(self):
        """Update rating vendor berdasarkan evaluasi terbaru"""
        for record in self:
            # Cari semua evaluasi yang sudah selesai untuk vendor ini
            evaluations = self.search([
                ('partner_id', '=', record.partner_id.id),
                ('evaluation_status', '=', 'done')
            ])
            
            if evaluations:
                # Hitung rata-rata skor
                avg_score = sum(evaluations.mapped('total_score')) / len(evaluations)
                
                # Update vendor rating (konversi ke skala 1-5)
                vendor_rating = avg_score / 20  # 100 point scale to 5 point scale
                
                record.partner_id.write({
                    'vendor_rating': vendor_rating,
                    'vendor_evaluation_count': len(evaluations),
                    'last_evaluation_date': record.evaluation_date
                })

    # Modifikasi: Tambahkan validasi unik untuk memastikan satu evaluasi per picking
    @api.constrains('picking_id')
    def _check_unique_picking(self):
        for record in self:
            if self.search_count([('picking_id', '=', record.picking_id.id), ('id', '!=', record.id)]):
                raise ValidationError('Sudah ada evaluasi untuk penerimaan barang ini.')