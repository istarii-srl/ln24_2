import logging
from urllib.parse import urlencode
from odoo.http import request
from odoo import http

_logger = logging.getLogger(__name__)

class MailHelper:

    @staticmethod
    def send_refusal_mail(request, employee_id, slot_id):
        batch_mails_sudo = request.env['mail.mail'].sudo()
        mail_values = {
            'subject': f"{employee_id.name}: Refus d'un slot du planning",
            'body_html': f"Bonjour,<br/><br/>L'utilisateur {employee_id.name} a refusé le slot du {slot_id.start_datetime.strftime('%Y-%m-%d %H:%M')} au {slot_id.end_datetime.strftime('%Y-%m-%d %H:%M')} pour le rôle {slot_id.role_id.name}.",
            'email_to': "admin@istarii.com",
            'auto_delete': False,
            'email_from': 'contact@istarii.com',
        }
        batch_mails_sudo |= request.env['mail.mail'].sudo().create(mail_values)
        batch_mails_sudo.send(auto_commit=False)