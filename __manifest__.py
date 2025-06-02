{
    'name': 'Warehouse Transfer Custom',
    'version': '1.0',
    'depends': ['stock'],
    'author': 'Nama Kamu',
    'category': 'Inventory',
    'description': 'Menandai pengiriman antar gudang',
    'data': [
        'security/ir.model.access.csv',
        'views/warehouse_transfer_views.xml',
    ],
    'installable': True,
    'application': True,
}
