from odoo import fields, models


class ResConfigSettionsExtend(models.TransientModel):
    _inherit = 'res.config.settings'
    qiniu_backup_enable = fields.Boolean("Enable Qiniu Backup", default=False, config_parameter='qiniu_backup_enable')
    qiniu_backup_method = fields.Selection([
        ('local', 'Local'),
        ('qiniu', 'Qiniu'),
    ], default='local', config_parameter='qiniu_backup_method', string='Qiniu Backup Method')
    qiniu_backup_local_path = fields.Char(string='Backup local path', config_parameter='qiniu_backup_local_path')
    qiniu_backup_bucket = fields.Char("bucket", config_parameter='qiniu_backup_bucket')
    qiniu_backup_access_key = fields.Char("access_key", config_parameter='qiniu_backup_access_key')
    qiniu_backup_secret_key = fields.Char("secret_key", config_parameter='qiniu_backup_secret_key')
    qiniu_backup_prefix = fields.Char("Prefix", config_parameter='qiniu_backup_prefix', default='odoo_db_backup')
