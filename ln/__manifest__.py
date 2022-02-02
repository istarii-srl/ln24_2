# -*- coding: utf-8 -*-
{
    'name': "ln",

    'summary': """
        LN24""",

    'description': """
        LN 24 Helper module
    """,

    'author': "istarii",
    'website': "https://istarii.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'ERP',
    'license': 'OPL-1',
    'version': '15.0.0.204',

    # any module necessary for this one to work correctly
    'depends': ['base', 'planning', 'contacts', 'hr_attendance', 'hr', 'hr_holidays'],

    # always loaded
    'data': [
        'data/ln_settings.xml',
        'data/cron_jobs.xml',
        'data/mail_templates.xml',
        'views/planning_slot.xml',
        'views/hr_employee.xml',
        'views/attendance_rule.xml',
        'views/day.xml',
        'views/frame.xml',
        'views/planning_views.xml',
        'views/planning_templates.xml',
        'views/planning_template.xml',
        'views/hr_attendance.xml',
        'wizards/confirm_slot_wizard.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_frontend': [
            'ln/static/src/js/planning_calendar_front.js',
        ],
        'web.assets_backend': [
            'ln/static/src/js/planning_buttons.js',
            'ln/static/src/scss/ln.scss',
        ],
        'web.assets_qweb': [
            'ln/static/src/xml/planning_buttons.xml',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
