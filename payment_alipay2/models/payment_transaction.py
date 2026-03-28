# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

from werkzeug import urls

from odoo import _, models, fields
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_alipay2.const import TRANSACTION_STATUS_MAPPING
from odoo.addons.payment_alipay2.controllers.main import AlipayController
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    alipay2_payment_status = fields.Char(_('alipay2 Transaction Status'))

    alipay2_refund_id = fields.Char(_('alipay2 Refund ID'))
    alipay2_refund_amount = fields.Char(_('alipay2 Refunded Amount'))
    alipay2_refund_currency = fields.Char(_('alipay2 Refunded Currency'))
    alipay2_refund_createdat = fields.Char(_('alipay2 Refunded Date'))

    def _get_specific_rendering_values(self, processing_values):
        """ Override of `payment` to return alipay2-specific rendering values.

        Note: self.ensure_one() from `_get_rendering_values`.

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'alipay2':
            return res

        # Initiate the payment and retrieve the payment link data.
        payload = self._alipay2_prepare_preference_request_payload()

        payment_response = self.provider_id._alipay2_make_request(
            payload
        )
        rendering_values = {
            'payment_form': payment_response,
        }
        return rendering_values

    def _alipay2_prepare_preference_request_payload(self):
        """ Create the payload for the preference request based on the transaction values.

        :return: The request payload.
        :rtype: dict
        """
        base_url = self.provider_id.get_base_url()
        return_url = urls.url_join(
            base_url, AlipayController._return_url
        )
        webhook_url = urls.url_join(
            base_url, AlipayController._webhook_url
        )

        return {
            'reference_number': self.reference,
            'amount': self.amount,
            'currency': self.currency_id.name,
            'redirect_url': return_url,
            'webhook': webhook_url,
            'name': self.partner_name,
            'email': self.partner_email,
            'channel': 'api_odoo'
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'alipay2' or len(tx) == 1:
            return tx

        out_trade_no = notification_data.get('out_trade_no')
        if not out_trade_no:
            raise ValidationError("alipay2: " + _("Received data with missing out_trade_no."))

        tx = self.search([('reference', '=', out_trade_no), ('provider_code', '=', 'alipay2')])
        if not tx:
            raise ValidationError(
                "alipay2: " + _("No transaction found matching reference %s.", out_trade_no)
            )
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'alipay2':
            return

        trade_no = notification_data.get('trade_no')

        self.alipay2_payment_status = notification_data.get('trade_status')
        self.provider_reference = trade_no

        reference_number = notification_data.get('out_trade_no')

        message = "Payment successful. Transaction Id: " + self.provider_reference + ", "
        message += f"Amount Paid: {self.amount}"

        payment_status = notification_data.get('trade_status')
        if payment_status in TRANSACTION_STATUS_MAPPING['pending']:
            self._set_pending(state_message=message)
        elif payment_status in TRANSACTION_STATUS_MAPPING['done']:
            self._set_done(state_message=message)
        elif payment_status in TRANSACTION_STATUS_MAPPING['canceled']:
            self._set_canceled()
        else:  # Classify unsupported payment status as the `error` tx state.
            _logger.warning(
                "alipay2: Received data for transaction with reference %s with invalid payment status: %s",
                reference_number, payment_status
            )
            self._set_error(
                "alipay2: " + _("Received data with invalid status: %s", payment_status)
            )

    def _send_refund_request(self, amount_to_refund=None):
        self.ensure_one()
        refund_tx = super()._send_refund_request(amount_to_refund=amount_to_refund)
        if self.provider_code != 'alipay2':
            return refund_tx

        converted_amount = payment_utils.to_minor_currency_units(
            -refund_tx.amount,  # The amount is negative for refund transactions
            refund_tx.currency_id
        )

        payload = {
            'payment_id': self.alipay2_payment_id,
            'amount': amount_to_refund,
        }

        response_content = refund_tx.provider_id._alipay2_make_request(
             payload
        )

        _logger.info(
            "alipay2 refund request response for transaction with reference %s:\n%s",
            self.reference, pprint.pformat(response_content)
        )

        # Handle the refund request response
        self.alipay2_refund_id = response_content.get('id')
        self.alipay2_refund_createdat = response_content.get('created_at')
        self.alipay2_refund_amount = response_content.get('amount_refunded')
        self.alipay2_refund_currency = response_content.get('currency')

        self.provider_reference = self.alipay2_refund_id

        message = "Refund successful. Refund Reference Id: " + self.alipay2_refund_id + ", "
        message += "Payment Id: " + self.alipay2_payment_id + ", "
        message += "Amount Refunded: " + self.alipay2_refund_amount + ", "
        message += "Payment Method: " + response_content.get('payment_method') + ", "
        message += "Created At: " + self.alipay2_refund_createdat

        self._set_done()
        self.env.ref('payment.cron_post_process_payment_tx')._trigger()

        return refund_tx
