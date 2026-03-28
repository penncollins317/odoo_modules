# Part of Odoo. See LICENSE file for full copyright and licensing details.
import hashlib
import hmac
import logging

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest

from odoo import fields, models
from odoo.addons.payment_alipay2.tools.alipay_key_loader import AlipayKeyLoader

_logger = logging.getLogger(__name__)


class Paymentprovider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('alipay2', "Alipay")], ondelete={'alipay2': 'set default'}
    )

    alipay2_appid = fields.Char(
        string="appid",
        required_if_provider='alipay2')

    alipay2_app_private_key = fields.Text("应用私钥", required_if_provider='alipay2')
    alipay2_public_key = fields.Text("支付宝公钥", required_if_provider='alipay2')

    def _get_alipay2_gateway(self):
        ctx_key = self.state
        ctx_value = 'https://openapi-sandbox.dl.alipaydev.com/gateway.do' if ctx_key  == 'test' else 'https://openapi.alipay.com/gateway.do'
        return ctx_value

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'alipay2').update({
            'support_refund': 'partial',
        })

    def _get_alipay2_public_key(self) -> str:
        return self.alipay2_public_key

    def _get_alipay2_app_private_key(self) -> str:
        return AlipayKeyLoader.load_private_key_from_str(self.alipay2_app_private_key)

    def _get_alipay2_client(self) -> DefaultAlipayClient:
        alipay_client_config = AlipayClientConfig()
        alipay_client_config.server_url = self._get_alipay2_gateway()
        alipay_client_config.app_id = self.alipay2_appid
        alipay_client_config.app_private_key = self._get_alipay2_app_private_key()
        alipay_client_config.alipay_public_key = self._get_alipay2_public_key()
        return DefaultAlipayClient(alipay_client_config=alipay_client_config)

    def _alipay2_make_request(self, payload: dict):
        self.ensure_one()
        client = self._get_alipay2_client()

        model = AlipayTradePagePayModel()
        model.out_trade_no = payload['reference_number']
        model.product_code = "FAST_INSTANT_TRADE_PAY"
        model.subject = payload['reference_number']
        model.body = payload['reference_number']
        # model.qr_pay_mode = "1"
        # model.qrcode_width = 100
        model.total_amount = str(payload['amount'])
        request = AlipayTradePagePayRequest(model)
        request.notify_url = payload['webhook']
        request.return_url = payload['redirect_url']
        response = client.page_execute(request)
        return response

    def _alipay2_calculate_signature(self, data):
        """ Compute the signature for the provided data according to the alipay2 documentation.

        :param dict data: The data to sign.
        :return: The calculated signature.
        :rtype: str
        """
        signing_string = ''
        for k in sorted(data.keys()):
            if k != 'hmac':
                signing_string += str(k) + '' + str(data[k])

        signature = hmac.new(
            bytes(self.alipay2_api_salt, 'utf-8'),
            msg=bytes(signing_string, 'utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()

        return signature
