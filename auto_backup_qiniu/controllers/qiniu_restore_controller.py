from odoo import http
from odoo.service import db
from werkzeug.datastructures import FileStorage


class QiniuBackupRestoreController(http.Controller):
    @http.route("/api/qiniu/backup/restore", type="http", auth="public", methods=['POST'], csrf=False)
    def backup_restore(self, **params):
        dbname = params.get("dbname")
        file = params.get("file")
        if not all([dbname, file]):
            return "params error", 400
        if not isinstance(file, FileStorage):
            return "file is not a FileStorage object", 400
        db.restore_db(dbname, file)
        return "ok"
