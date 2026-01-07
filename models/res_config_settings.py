from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    doc_studio_repo_path = fields.Char(
        string="Repository Path (Local)",
        config_parameter='odoo_doc_studio.git_repo_path',
        help="Absolute path to the folder containing Markdown files on the server (e.g. /mnt/docs_repo)."
    )
    
    # Future-proof: Git URL field (placeholder for now, logic to be implemented later)
    doc_studio_git_url = fields.Char(
        string="Git Repository URL",
        config_parameter='odoo_doc_studio.git_remote_url',
        help="HTTPS/SSH URL of the Git repository to clone (Features coming soon)."
    )

    def action_git_push(self):
        msg = self.env['doc.git.manager'].git_commit_push()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Git Push',
                'message': msg,
                'sticky': False,
                'type': 'success',
            }
        }

    def action_git_pull(self):
        msg = self.env['doc.git.manager'].git_pull()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Git Pull',
                'message': msg,
                'sticky': False,
                'type': 'success',
            }
        }
