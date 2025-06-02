# hooks.py

from odoo import SUPERUSER_ID
from odoo.api import Environment

# hooks.py

def cleanup_transjakarta_seeder(env):
    """
    Uninstall hook untuk membersihkan data yang dibuat oleh modul seeder
    """
    
    # 1) Hapus Purchase Orders terlebih dahulu
    purchase_orders = env['purchase.order'].search([
        ('partner_id.name', 'in', [
            'PT. Karoseri Nusantara',
            'PT. Ban Jakarta', 
            'PT. Oli Prima'
        ])
    ])
    if purchase_orders:
        # Cancel PO yang masih draft sebelum dihapus
        purchase_orders.filtered(lambda po: po.state == 'draft').write({'state': 'cancel'})
        purchase_orders.unlink()

    # 2) Hapus stock.quant & stock.move agar tidak ada stock move yang menghalangi perubahan UoM
    quants = env['stock.quant'].search([
        ('product_id.default_code', 'in', ['BUS-MRC', 'BAN-BUS', 'OLI-MSN'])
    ])
    if quants:
        quants.unlink()
        
    moves = env['stock.move'].search([
        ('product_id.default_code', 'in', ['BUS-MRC', 'BAN-BUS', 'OLI-MSN'])
    ])
    if moves:
        moves.unlink()

    # 3) Hapus product.supplierinfo terlebih dahulu (vendor info di produk)
    supplier_infos = env['product.supplierinfo'].search([
        ('product_tmpl_id.default_code', 'in', ['BUS-MRC', 'BAN-BUS', 'OLI-MSN'])
    ])
    if supplier_infos:
        supplier_infos.unlink()

    # 4) Hapus product.template (produk yang di-seed)
    products = env['product.template'].search([
        ('default_code', 'in', ['BUS-MRC', 'BAN-BUS', 'OLI-MSN'])
    ])
    if products:
        products.unlink()

    # 5) Hapus kategori produk yang dibuat (Bus, Suku Cadang, Bahan Habis Pakai)
    categories = env['product.category'].search([
        ('name', 'in', ['Bus', 'Suku Cadang', 'Bahan Habis Pakai'])
    ])
    if categories:
        categories.unlink()

    # 6) Hapus UoM khusus (Set, Liter) - hati-hati dengan dependency
    uoms = env['uom.uom'].search([
        ('name', 'in', ['Set', 'Liter'])
    ])
    if uoms:
        uoms.unlink()
        
    # Hapus UoM category jika kosong
    uom_categories = env['uom.category'].search([
        ('name', '=', 'Volume'),
        ('uom_ids', '=', False)  # kategori yang tidak memiliki UoM
    ])
    if uom_categories:
        uom_categories.unlink()

    # 7) Hapus warehouse & komponen terkait (comprehensive cleanup)
    warehouses = env['stock.warehouse'].search([
        ('name', 'in', ['Pool Pegangsaan', 'Pool Cijantung'])
    ])
    
    if warehouses:
        try:
            for warehouse in warehouses:
                # Hapus stock rules yang terkait
                stock_rules = env['stock.rule'].search([
                    ('warehouse_id', '=', warehouse.id)
                ])
                if stock_rules:
                    stock_rules.unlink()
                
                # Hapus procurement groups yang terkait
                proc_groups = env['procurement.group'].search([
                    ('name', 'ilike', warehouse.name)
                ])
                if proc_groups:
                    proc_groups.unlink()
                
                # Hapus picking types yang terkait
                picking_types = env['stock.picking.type'].search([
                    ('warehouse_id', '=', warehouse.id)
                ])
                if picking_types:
                    # Hapus stock rules yang referensi ke picking types ini
                    rules_with_picking = env['stock.rule'].search([
                        ('picking_type_id', 'in', picking_types.ids)
                    ])
                    if rules_with_picking:
                        rules_with_picking.unlink()
                    picking_types.unlink()
                
                # Hapus warehouse
                warehouse.unlink()
                
        except Exception as e:
            print(f"Warning: Could not delete warehouse: {e}")
            # Jika tidak bisa dihapus, coba archive saja
            warehouses.write({'active': False})
    
    # Hapus lokasi yang mungkin tersisa
    locations = env['stock.location'].search([
        ('name', 'in', ['Garasi Pegangsaan', 'Garasi Cijantung'])
    ])
    if locations:
        try:
            locations.unlink()
        except Exception as e:
            print(f"Warning: Could not delete locations: {e}")
            locations.write({'active': False})

    # 8) Hapus vendor (supplier/partner) - paling terakhir
    partners = env['res.partner'].search([
        ('name', 'in', [
            'PT. Karoseri Nusantara',
            'PT. Ban Jakarta',
            'PT. Oli Prima'
        ])
    ])
    if partners:
        partners.unlink()

    print("✅ Cleanup Transjakarta Seeder completed successfully!")
