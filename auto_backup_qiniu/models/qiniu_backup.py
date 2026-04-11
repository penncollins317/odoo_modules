import logging
import os
from datetime import datetime, timezone, timedelta

from odoo import models, fields, api
from odoo.service import db

_logger = logging.getLogger(__name__)

tz = timezone(timedelta(hours=8))

import qiniu


class QiniuBackup(models.Model):
    _name = 'qiniu.backup'
    _order = 'id desc'
    name = fields.Char(string='Name', required=True)
    bucket_name = fields.Char(string='Bucket name', required=True)

    def _get_api_keys(self):
        qiniu_access_key_id = self.env['ir.config_parameter'].sudo(
        ).get_param('qiniu_backup_access_key')
        qiniu_secret_access_key = self.env['ir.config_parameter'].sudo(
        ).get_param('qiniu_backup_secret_key')
        return qiniu_access_key_id, qiniu_secret_access_key

    def _get_bucket(self) -> str:
        return self.env['ir.config_parameter'].sudo().get_param("qiniu_backup_bucket")

    def _qiniu_token(self, key: str) -> str:
        qiniu_access_key_id, qiniu_secret_access_key = self._get_api_keys()
        auth = qiniu.Auth(qiniu_access_key_id, qiniu_secret_access_key)
        return auth.upload_token(self._get_bucket(), key)

    @api.model
    def action_backup(self):
        db_name = self.env.cr.dbname
        fname = "{:%Y_%m_%d_%H_%M_%S}-{}-backup.zip".format(
            datetime.now(tz), db_name)
        qiniu_backup_prefix = self.env['ir.config_parameter'].sudo().get_param("qiniu_backup_prefix", '')
        backup_method = self.env['ir.config_parameter'].sudo().get_param("qiniu_backup_method")
        if backup_method == 'local':
            backup_path = self.env['ir.config_parameter'].sudo().get_param("qiniu_backup_local_path")
            if not backup_path:
                _logger.warning("qiniu local backup path not set")
                return
            file_path = os.path.join(backup_path, fname)
            with open(file_path, 'wb') as f:
                db.dump_db(db_name, f)
            _logger.info(f'qiniu local backup success, {file_path}')

        elif backup_method == 'qiniu':
            object_Key = f'{qiniu_backup_prefix}/{fname}'
            backup_file = db.dump_db(db_name, None)
            try:
                token = self._qiniu_token(object_Key)
                res = qiniu.put_data(token, object_Key, backup_file)
                _logger.info(f"qiniu upload res:{res}")
                self.create({
                    'name': fname,
                    'bucket_name': self._get_bucket(),
                })
            except Exception as e:
                logging.error(e)
            finally:
                backup_file.close()

    @api.model
    def action_backup_all(self):
        """Run all scheduled backups."""
        if self.env['ir.config_parameter'].sudo().get_param("qiniu_backup_enable"):
            self.action_backup()
