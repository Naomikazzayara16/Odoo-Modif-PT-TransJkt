# -*- coding: utf-8 -*-
{
    'name': 'Vendor Evaluation System',
    'version': '1.0.0',
    'category': 'Inventory',
    'summary': 'Sistem Evaluasi Vendor pada Penerimaan Barang',
    'description': """
        Modul untuk menambahkan fitur evaluasi vendor pada proses penerimaan barang.
        Fitur:
        - Input skor evaluasi vendor berdasarkan kriteria
        - Otomatis update rating vendor
        - Laporan performa vendor
    """,
    'author': 'Trans Jakarta',
    'website': 'https://www.transjakarta.co.id/',
    'depends': ['stock', 'purchase', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
        'views/res_partner_views.xml',
        'views/vendor_evaluation_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}