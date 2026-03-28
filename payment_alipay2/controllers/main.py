# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

from alipay.aop.api.util.SignatureUtils import verify_with_rsa
from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class AlipayController(http.Controller):
    _return_url = '/payment/alipay2/return'
    _webhook_url = '/payment/alipay2/webhook'

    @http.route(_return_url, type='http', methods=['GET'], auth='public')
    def alipay2_return_from_checkout(self, **data):
        """ Process the notification data sent by alipay2 after redirection from checkout.

        :param dict data: The notification data.
        """
        # Handle the notification data.
        _logger.info("Handling redirection from alipay2 with data:\n%s", pprint.pformat(data))

        if data.get('trade_no'):
            return request.redirect('/payment/status')
        else:
            return request.redirect('/shop/payment')

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def alipay2_webhook(self, **params):
        """ Process the notification data sent by alipay2 to the webhook.

        :param dict _kwargs: The extra query parameters.
        :return: An empty string to acknowledge the notification.
        :rtype: str
        """
        data = http.request.httprequest.form.to_dict()
        _logger.info("Webhook received from alipay2 with data:\n%s", pprint.pformat(data))

        # Handle the notification data.
        try:
            # Check the integrity of the notification data.
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'alipay2', data
            )

            self._verify_notification_signature(data, tx_sudo)

            tx_sudo._handle_notification_data('alipay2', data)

        except ValidationError:  # Acknowledge the notification to avoid getting spammed.
            _logger.exception("Unable to handle the alipay2  notification data; skipping to acknowledge")

        return 'success'  # Acknowledge the notification.

    @staticmethod
    def _verify_notification_signature(notification_data, tx_sudo):
        """ Check that the received signature matches the expected one.

        :param dict notification_data: The notification data
        :param recordset tx_sudo: The sudoed transaction referenced by the notification data, as a
                                  `payment.transaction` record
        :return: None
        :raise: :class:`werkzeug.exceptions.Forbidden` if the signatures don't match
        """

        sign = notification_data.pop("sign")
        sign_type = notification_data.pop("sign_type")
        if sign_type != 'RSA2':
            raise ValidationError(
                "alipay2: Invalid sign_type received. "
                f"expected=RSA2, actual={sign_type}, "
                f"out_trade_no={notification_data.get('out_trade_no')}, "
                f"trade_no={notification_data.get('trade_no')}"
            )
        params = sorted(notification_data.items(), key=lambda e: e[0], reverse=False)
        message = "&".join(u"{}={}".format(k, v) for k, v in params).encode(notification_data.get("charset", 'utf-8'))

        if not verify_with_rsa(tx_sudo.provider_id._get_alipay2_public_key(), message, sign):
            _logger.warning(
                "alipay2: Signature verification failed. "
                f"out_trade_no={notification_data.get('out_trade_no')}, "
                f"trade_no={notification_data.get('trade_no')}, "
                f"notify_id={notification_data.get('notify_id')}"
            )
            raise Forbidden()
