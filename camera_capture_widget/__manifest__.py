# -*- coding: utf-8 -*-
{
    'name': 'Web Camera Widget',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Capture images directly from your device camera in any Odoo form view',
    'description': """
Web Camera Widget for Odoo 19
=============================
Adds a camera capture button to any Binary/Image field in Odoo form views.
Click the camera icon, snap a photo, and it is saved directly to the record.

Key Features
------------
- Works on any Binary/Image field — no model restrictions
- Live camera preview with one-click capture
- Front / rear camera toggle on mobile devices
- Review and retake before confirming
- Responsive design for desktop and mobile
- No plugins or extra software required
- Compatible with Chrome, Firefox, Safari, Edge, iOS, Android
    """,
    'author': 'Flowient Technology',
    'company': 'Flowient Technology',
    'maintainer': 'Flowient Technology',
    'website': 'https://flowient.in',
    'support': 'info@flowient.in',
    'price': 5.00,
    'currency': 'USD',
    'license': 'LGPL-3',
    'depends': ['web', 'contacts'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'camera_capture_widget/static/src/scss/camera_capture_widget.scss',
            'camera_capture_widget/static/src/js/camera_capture_widget.js',
            'camera_capture_widget/static/src/xml/camera_capture_widget.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
