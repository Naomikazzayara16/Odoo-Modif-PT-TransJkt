{
    'name': 'Transjakarta Seeder',
    'version': '18.0.1.0',
    'category': 'Tools',
    'summary': 'Seeder data awal untuk Transjakarta (Purchase & Inventory)',
    'description': 'Seeder data vendor, produk, dan gudang untuk Transjakarta.',
    'author': 'Transjakarta IT',
    'website': 'https://www.transjakarta.co.id',
    'license': 'LGPL-3',
    'depends': ['purchase', 'stock', 'product', 'uom'],
    'data': [
        'data/seed_transjakarta.xml',
    ],
    'uninstall_hook': 'cleanup_transjakarta_seeder', 
    'installable': True,
    'application': False,
    'auto_install': False,
} 