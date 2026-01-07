import logging
import os
from odoo import models, api, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import git
except ImportError:
    git = None

class DocGitManager(models.AbstractModel):
    _name = 'doc.git.manager'
    _description = 'Git Operations Manager'

    @api.model
    def _get_repo(self):
        if not git:
            raise UserError("GitPython library is not installed.")
        
        repo_path = self.env['doc.page']._get_git_repo_path()
        if not os.path.isdir(os.path.join(repo_path, '.git')):
            raise UserError(f"Directory {repo_path} is not a valid Git repository. Please initialize it first.")
        
        return git.Repo(repo_path)

    @api.model
    def git_commit_push(self, commit_message="Update from Odoo Doc Studio"):
        """Stage all changes, commit, and push to remote."""
        repo = self._get_repo()
        
        try:
            # 1. Add all changes
            repo.git.add(A=True)
            
            # 2. Check if there are changes to commit
            if not repo.is_dirty(untracked_files=True):
                return "No changes to commit."

            # 3. Commit
            # Configure user based on current Odoo user
            author = git.Actor(self.env.user.name, self.env.user.email or "odoo@example.com")
            committer = git.Actor("Odoo Doc Studio", "bot@odoo-doc-studio")
            
            repo.index.commit(commit_message, author=author, committer=committer)
            
            # 4. Push (Assuming 'origin' and current branch)
            if hasattr(repo.remotes, 'origin'):
                origin = repo.remotes.origin
                result = origin.push()
                summary = result[0].summary
                _logger.info(f"Git Push Result: {summary}")
                return f"Success: {summary}"
            else:
                # If no origin, check if doc_studio_git_url is set and create it
                remote_url = self.env['ir.config_parameter'].sudo().get_param('odoo_doc_studio.git_remote_url')
                if remote_url:
                    origin = repo.create_remote('origin', url=remote_url)
                    result = origin.push(set_upstream=True, refspec='HEAD')
                    return f"Remote 'origin' created and pushed: {result[0].summary}"
                
                return "Commit successful. (No remote 'origin' configured, skipped push)"

        except Exception as e:
            _logger.error(f"Git Error: {e}")
            raise UserError(f"Git Operation Failed: {e}")

    @api.model
    def git_pull(self):
        """Pull latest changes from remote using rebase to maintain a clean linear history."""
        repo = self._get_repo()
        try:
            if not hasattr(repo.remotes, 'origin'):
                return "Skipped pull: No remote 'origin' configured."
            
            origin = repo.remotes.origin
            # Pull with rebase enabled (git pull --rebase)
            origin.pull(rebase=True)
            
            # After pull, we should re-sync Odoo DB
            self.env['doc.page'].sync_all_from_disk()
            return "Successfully pulled updates and synced Odoo."
        except Exception as e:
            _logger.error(f"Git Pull Failed: {e}")
            raise UserError(f"Git Pull Failed: {e}")

    @api.model
    def _cron_auto_sync(self):
        """Cron job to sync git (Push local changes, Pull remote changes)"""
        try:
            # 1. First Push any local pending changes
            # We catch specific push errors (e.g. nothing to push) inside git_commit_push logic ideally, 
            # or rely on its output.
            try:
                # Use a specific bot user for auto-commits if desired, currently uses admin (env.user)
                msg_push = self.git_commit_push(commit_message="Auto-sync from Odoo")
                _logger.info(f"Cron Git Push: {msg_push}")
            except Exception as pe:
                # If push fails (e.g. rejected non-fast-forward), we might need to pull first.
                _logger.warning(f"Cron Push skipped/failed: {pe}")

            # 2. Then Pull remote changes
            msg_pull = self.git_pull()
            _logger.info(f"Cron Git Pull: {msg_pull}")
            
        except Exception as e:
            # We catch exceptions to prevent Cron from failing hard, but we log them.
            _logger.warning(f"Git Auto-Sync encountered an issue: {e}")
