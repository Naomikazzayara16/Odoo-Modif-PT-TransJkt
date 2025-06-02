{
    "name": "Tender Automation - PT Transportasi Jakarta",
    "version": "18.0.1.0.0",
    "category": "Purchases",
    "summary": "Otomatis tender untuk pembelian di atas 200 juta",
    "description": """
        Tender Automation Module untuk PT Transportasi Jakarta
        Fitur:
        - Otomatis tender untuk pembelian di atas Rp 200.000.000
        - Manajemen proses tender multi-vendor
        - Email notification system
        - Integration dengan Purchase Order existing
        - Sesuai regulasi pengadaan PT Transportasi Jakarta
    """,
    "author": "PT Transportasi Jakarta",
    "website": "https://transjakarta.co.id",
    "license": "LGPL-3",
    "depends": ["base", "purchase", "mail", "contacts"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/email_templates.xml",
        "views/vendor_bid_views.xml",
        "views/tender_process_views.xml",
        "views/purchase_order_views.xml", 
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}