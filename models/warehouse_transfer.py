from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_inter_warehouse = fields.Boolean(
        string="Inter-Warehouse Transfer",
        compute="_compute_inter_warehouse",
        store=True
    )

    @api.depends('location_id', 'location_dest_id')
    def _compute_inter_warehouse(self):
        for record in self:
            record.is_inter_warehouse = (
                record.location_id.usage == 'internal' and
                record.location_dest_id.usage == 'internal'
            )
