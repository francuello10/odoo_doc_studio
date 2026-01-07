import logging
import os
import re
from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import git
    from markdownify import markdownify as md
    import markdown
except ImportError:
    git = None
    md = None
    markdown = None
    _logger.warning("External dependencies (GitPython, markdownify, markdown) not found.")

class DocPage(models.Model):
    _name = 'doc.page'
    _description = 'Documentation Page'
    _order = 'sequence, id'
    _rec_name = 'name'

    name = fields.Char(string='Title', required=True)
    parent_id = fields.Many2one('doc.page', string='Parent Page', ondelete='cascade')
    child_ids = fields.One2many('doc.page', 'parent_id', string='Sub-pages')
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Organization Fields
    workspace_id = fields.Many2one('doc.workspace', string='Workspace', ondelete='set null', index=True)
    tag_ids = fields.Many2many('doc.tag', 'doc_page_tag_rel', 'page_id', 'tag_id', string='Tags')
    is_favorited = fields.Boolean(string='Favorited', default=False, index=True)
    
    # Tracking Fields
    last_editor_id = fields.Many2one('res.users', string='Last Editor', readonly=True)
    edit_count = fields.Integer(string='Edit Count', default=0, readonly=True)

    # Sharing & Visibility
    visibility = fields.Selection([
        ('private', 'Private'),
        ('internal', 'Internal'),
        ('public', 'Public')
    ], default='internal', string="Visibility", required=True, index=True,
       help="Private: Only owner and shared users.\nInternal: All employees.\nPublic: Everyone.")
    
    share_ids = fields.One2many('doc.share', 'page_id', string='Shares')
    
    current_user_permission = fields.Selection([
        ('none', 'None'),
        ('read', 'Viewer'),
        ('write', 'Editor'),
        ('owner', 'Owner')
    ], compute='_compute_current_user_permission', string="My Permission")
    
    # Content Fields
    content_md = fields.Text(string='Content (Markdown)')
    body_html = fields.Html(string='Content (HTML)', compute='_compute_body_html', inverse='_inverse_body_html', store=True, sanitize=False)
    
    # Document Linking
    linked_page_ids = fields.Many2many('doc.page', 'doc_page_link_rel', 'source_id', 'target_id',
                                        string='Linked Documents', compute='_compute_linked_pages', store=True)
    
    # Git Integration
    file_path = fields.Char(string='File Path', compute='_compute_file_path', store=True, recursive=True)

    @api.depends('visibility', 'share_ids.user_id', 'share_ids.permission')
    def _compute_current_user_permission(self):
        for record in self:
            if record.create_uid == self.env.user:
                record.current_user_permission = 'owner'
                continue
            
            # Check explicit share - most specific first
            share = record.share_ids.filtered(lambda s: s.user_id == self.env.user)
            if share:
                # If multiple shares, take the most permissive (write > read)
                if any(s.permission == 'write' for s in share):
                    record.current_user_permission = 'write'
                else:
                    record.current_user_permission = 'read'
                continue
                
            # Check internal visibility
            if record.visibility == 'internal':
                # Default for internal pages is Editor/Writer in this wiki-like system
                record.current_user_permission = 'write' 
            elif record.visibility == 'public':
                record.current_user_permission = 'read'
            else:
                record.current_user_permission = 'none'

    @api.depends('content_md')
    def _compute_body_html(self):
        """Convert Markdown to HTML, resolving doc:// links"""
        for record in self:
            if record.content_md and markdown:
                try:
                    # Preprocess doc:// links to make them clickable
                    processed_md = record._resolve_doc_links_to_html(record.content_md)
                    # Convert Markdown to HTML
                    html_content = markdown.markdown(processed_md, extensions=['fenced_code', 'tables', 'nl2br'])
                    # CLEANUP: Ensure no full HTML doc boilerplates remain
                    html_content = record._clean_html_fragment(html_content)
                    # Ensure string type
                    record.body_html = Markup(html_content) if html_content else ""
                except Exception as e:
                    _logger.error(f"Error converting Markdown to HTML for page {record.id}: {e}")
                    record.body_html = Markup("<p>Error rendering content</p>")
            else:
                record.body_html = ""
    
    def _inverse_body_html(self):
        """Convert HTML back to Markdown when edited via Wysiwyg"""
        for record in self:
            if record.body_html and md:
                try:
                    # CLEANUP: Strip full HTML doc boilerplates if present
                    clean_html = record._clean_html_fragment(record.body_html)
                    # Convert HTML to Markdown
                    markdown_content = md(clean_html, heading_style="ATX")
                    # Ensure string type (markdownify can return objects)
                    if not isinstance(markdown_content, str):
                        markdown_content = str(markdown_content) if markdown_content else ""
                    # Convert clickable links back to doc:// scheme
                    markdown_content = record._convert_html_links_to_doc_scheme(markdown_content)
                    record.content_md = markdown_content
                except Exception as e:
                    _logger.error(f"Error converting HTML to Markdown for page {record.id}: {e}")
                    # Keep existing content_md on error
                    if not record.content_md:
                        record.content_md = ""
            else:
                record.content_md = ""

    def _clean_html_fragment(self, html_str):
        """Helper to extract only content from inside <body> if a full doc is provided"""
        if not html_str:
            return ""
        if isinstance(html_str, Markup):
            html_str = str(html_str)
            
        # Check if it looks like a full document
        if '<html' in html_str.lower() or '<body' in html_str.lower() or '<!doctype' in html_str.lower():
            # Extract content between <body> and </body>
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_str, re.IGNORECASE | re.DOTALL)
            if body_match:
                html_str = body_match.group(1).strip()
            # If no body found but has <html>, try to strip all head/meta/tags
            else:
                # Remove <head> section
                html_str = re.sub(r'<head[^>]*>.*?</head>', '', html_str, flags=re.IGNORECASE | re.DOTALL)
                # Remove all remaining tags that are NOT expected in a fragment
                html_str = re.sub(r'<!?DOCTYPE[^>]*>', '', html_str, flags=re.IGNORECASE)
                html_str = re.sub(r'</?(html|head|meta|title|link)[^>]*>', '', html_str, flags=re.IGNORECASE)
        
        return html_str.strip()
    
    @api.model
    def action_convert_md_to_html(self, md_content):
        """RPC helper to convert MD to HTML for the frontend sync"""
        if not md_content:
            return ""
        try:
            # We create a dummy record to use link resolution logic
            dummy = self.new({'content_md': md_content})
            processed_md = dummy._resolve_doc_links_to_html(md_content)
            html_content = markdown.markdown(processed_md, extensions=['fenced_code', 'tables', 'nl2br'])
            return dummy._clean_html_fragment(html_content)
        except Exception as e:
            _logger.error(f"Sync MD to HTML error: {e}")
            return "<p>Error converting content</p>"

    @api.model
    def action_convert_html_to_md(self, html_content):
        """RPC helper to convert HTML to MD for the frontend sync"""
        if not html_content:
            return ""
        try:
            # Clean first
            dummy = self.new()
            clean_html = dummy._clean_html_fragment(html_content)
            # Convert
            markdown_content = md(clean_html, heading_style="ATX")
            if not isinstance(markdown_content, str):
                markdown_content = str(markdown_content) if markdown_content else ""
            # Fix links
            return dummy._convert_html_links_to_doc_scheme(markdown_content)
        except Exception as e:
            _logger.error(f"Sync HTML to MD error: {e}")
            return "Error converting content"

    def _resolve_doc_links_to_html(self, markdown_text):
        """
        Replace:
         1. [text](doc://123) -> Internal Odoo Link
         2. [text](path/to/file.md) -> Internal Odoo Link (by searching file_path)
        """
        def get_odoo_url(page_id):
            return f"/web#action=odoo_doc_studio.action_doc_studio&active_id={page_id}"

        # 1. ID Links
        def replace_doc_link(match):
            return f"[{match.group(1)}]({get_odoo_url(match.group(2))})"
    
        pattern_id = r'\[([^\]]+)\]\(doc://([0-9]+)\)'
        markdown_text = re.sub(pattern_id, replace_doc_link, markdown_text)

        # 2. File Path Links
        def replace_file_link(match):
            text = match.group(1)
            target_path = match.group(2)
            
            # Resolve relative path using self.file_path context
            target_page = False
            
            # A. Try exact match (e.g. from root)
            target_page = self.env['doc.page'].search([('file_path', '=', target_path)], limit=1)
            
            # B. Try relative match
            if not target_page and self.file_path:
                current_dir = os.path.dirname(self.file_path)
                # target_path might be "Sedes Oficiales.md"
                abs_target = os.path.normpath(os.path.join(current_dir, target_path))
                target_page = self.env['doc.page'].search([('file_path', '=', abs_target)], limit=1)
            
            if target_page:
                return f"[{text}]({get_odoo_url(target_page.id)})"
            
            return match.group(0) # Keep original if not found

        pattern_file = r'\[([^\]]+)\]\(([^)]+\.md)\)'
        markdown_text = re.sub(pattern_file, replace_file_link, markdown_text)
        
        return markdown_text
    
    def _convert_html_links_to_doc_scheme(self, markdown_text):
        """Convert [text](/web#...&id=123) back to [text](doc://123) for storage"""
        def replace_web_link(match):
            link_text = match.group(1)
            page_id = match.group(2)
            return f"[{link_text}](doc://{page_id})"
        
        # Pattern: [text](/web#action=...&active_id=123)
        pattern = r'\[([^\]]+)\]\(/web#[^&]*&active_id=([0-9]+)\)'
        return re.sub(pattern, replace_web_link, markdown_text)
    
    @api.depends('content_md')
    def _compute_linked_pages(self):
        """Extract doc:// references and populate linked_page_ids"""
        for record in self:
            if record.content_md:
                # Find all doc://page_id references
                pattern = r'doc://([0-9]+)'
                page_ids = [int(match) for match in re.findall(pattern, record.content_md)]
                # Remove duplicates and self-references
                page_ids = list(set(page_ids))
                if record.id in page_ids:
                    page_ids.remove(record.id)
                record.linked_page_ids = [(6, 0, page_ids)]
            else:
                record.linked_page_ids = [(5, 0, 0)]

    @api.depends('name', 'parent_id.file_path')
    def _compute_file_path(self):
        if self.env.context.get('skip_file_path_compute'):
            return
            
        for record in self:
            slug = self._slugify(record.name)
            if record.parent_id:
                # If parent exists, nested folder structure
                # Parent path is a directory, current record is a directory + index.md? 
                # Or Confluence style: each page is a file, unless it has children?
                # Docusaurus style: folders for categories, files for pages.
                # Let's simple: always a folder matching the hierarchy, and the content in index.md inside it? 
                # Or just file.md if leaf, folder/index.md if parent?
                # Let's go with: /Parent/Child.md
                parent_path = record.parent_id.file_path or ""
                parent_dir = os.path.dirname(parent_path) if parent_path.endswith('.md') else parent_path
                # Wait, parent_id.file_path logic needs to be consistent.
                # Let's try: /slug.md for root. 
                # If parent is /slug.md, and we add child, parent becomes /slug/index.md?
                # Simpler: All pages are folders with index.md? No, that's messy.
                record.file_path = self._get_path_recursive(record)
            else:
                record.file_path = f"{slug}.md"

    def _get_path_recursive(self, record):
        slug = self._slugify(record.name)
        if record.parent_id:
            parent_path = self._get_path_recursive(record.parent_id)
            # Strip .md to get directory
            parent_dir = parent_path.replace('.md', '')
            return f"{parent_dir}/{slug}.md"
        return f"{slug}.md"

    def _slugify(self, text):
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text

    def _ensure_unique_name(self, name):
        """Check if name exists and append (1), (2)... if it does"""
        original_name = name
        count = 1
        # Use self.env to avoid singleton issues if self is model
        domain = [('name', '=', name)]
        if self:
            domain.append(('id', 'not in', self.ids))
            
        while self.env['doc.page'].search(domain, limit=1):
            name = f"{original_name} ({count})"
            count += 1
            domain[0] = ('name', '=', name)
        return name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' in vals:
                vals['name'] = self._ensure_unique_name(vals['name'])
        records = super().create(vals_list)
        for record in records:
            record._sync_to_git()
        return records

    def write(self, vals):
        # Handle name uniqueness if changing
        if 'name' in vals:
            for record in self:
                # Ensure each record gets a unique version of the requested name
                unique_name = record._ensure_unique_name(vals['name'])
                # Manual update for name to avoid recursion and allow unique names per record
                super(DocPage, record).write({'name': unique_name})
            # Remove name from vals to avoid re-writing the non-unique name in super() below
            vals = {k: v for k, v in vals.items() if k != 'name'}

        if not vals:
            return True

        # Track editing user
        if 'body_html' in vals or 'content_md' in vals:
            vals['last_editor_id'] = self.env.uid
        
        res = super().write(vals)
        
        # Increment edit count
        if 'body_html' in vals or 'content_md' in vals:
            for record in self:
                super(DocPage, record).write({'edit_count': record.edit_count + 1})
        
        # Sync to git
        for record in self:
            record._sync_to_git()
            
        return res

    def unlink(self):
        # Delete file from git sync before removing record
        for record in self:
            record._delete_from_git()
        return super().unlink()

    def _get_git_repo_path(self):
        path = self.env['ir.config_parameter'].sudo().get_param('odoo_doc_studio.git_repo_path')
        if not path:
             # Fallback for testing if not set
             path = '/tmp/odoo_doc_studio_repo'
        return path

    def action_sync_to_disk(self):
        """RPC wrapper for _sync_to_git"""
        for record in self:
            record._sync_to_git()
        return True

    def _sync_to_git(self):
        """Write content_md and metadata as frontmatter to the file system"""
        repo_path = self._get_git_repo_path()
        if not repo_path:
            return

        if not os.path.exists(repo_path):
            try:
                os.makedirs(repo_path, exist_ok=True)
                _logger.info(f"Created git repo path: {repo_path}")
            except OSError as e:
                _logger.error(f"Could not create git repo path {repo_path}: {e}")
                return

        full_path = os.path.join(repo_path, self.file_path)
        directory = os.path.dirname(full_path)
        
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                try:
                    os.chmod(directory, 0o777)
                except OSError: pass
            
            with open(full_path, 'w', encoding='utf-8') as f:
                # Write enhanced frontmatter
                f.write("---\n")
                f.write(f"title: {self.name}\n")
                f.write(f"author: {self.create_uid.name}\n")
                f.write(f"created_at: {self.create_date}\n")
                if self.last_editor_id:
                    f.write(f"last_editor: {self.last_editor_id.name}\n")
                f.write(f"last_edited_at: {self.write_date}\n")
                f.write("---\n\n")
                f.write(self.content_md or "")
            
            try:
                os.chmod(full_path, 0o666)
            except OSError:
                pass
                
        except OSError as e:
            _logger.error(f"Failed to write file {full_path}: {e}")

    def _parse_frontmatter(self, content):
        """Helper to extract metadata and content from markdown with frontmatter"""
        metadata = {}
        cleaned_content = content
        if content.startswith('---'):
            try:
                second_dash = content.find('\n---', 3)
                if second_dash != -1:
                    header = content[3:second_dash].strip()
                    cleaned_content = content[second_dash+4:].strip()
                    # Parse simple yaml-like pairs
                    for line in header.split('\n'):
                        if ':' in line:
                            key, val = line.split(':', 1)
                            metadata[key.strip()] = val.strip()
            except Exception:
                pass
        return metadata, cleaned_content

    def action_sync_from_disk(self):
        """Read content from the file system and update the record"""
        self.ensure_one()
        repo_path = self._get_git_repo_path()
        if not repo_path: return False
        
        full_path = os.path.join(repo_path, self.file_path)
        if not os.path.exists(full_path):
             return False
             
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
                
            metadata, content = self._parse_frontmatter(raw_content)

            vals = {}
            if content != self.content_md:
                vals['content_md'] = content
            
            # Note: We don't necessarily want to pwn local Odoo metadata (create_date) 
            # with disk metadata every sync, but we could if we wanted to enforce it.
            # For now, let's keep it simple and just update content.
            
            if vals:
                self.write(vals)
                return True
            return False
            
        except OSError as e:
            _logger.error(f"Failed to read file {full_path}: {e}")
            return False

    @api.model
    def sync_all_from_disk(self):
        """
        Full bidirectional sync (Two-Pass):
        1. Scan file system and create/update ALL records (ignoring parents initially).
        2. Resolve parent relationships ensuring all potential parents exist.
        """
        # CRITICAL: Prevent Odoo from re-computing file_path (slugifying) when we want to respect disk path
        self = self.with_context(skip_file_path_compute=True)
        
        repo_path = self._get_git_repo_path()
        if not repo_path or not os.path.exists(repo_path):
            return 0

        updated_count = 0
        created_count = 0
        
        # Pass 1: Create/Update all records
        # Map: rel_path -> doc.page (for pass 2)
        start_time = fields.Datetime.now()
        existing_paths = set(self.search([]).mapped('file_path'))
        
        # We need to collect all files first to handle them
        all_files = []
        for root, dirs, files in os.walk(repo_path):
            if '.git' in root: continue
            for filename in files:
                if not filename.endswith('.md'): continue
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, repo_path)
                all_files.append((full_path, rel_path, filename))

        for full_path, rel_path, filename in all_files:
            # Check if exists
            page = self.search([('file_path', '=', rel_path)], limit=1)
            
            if page:
                # Update content
                if page.action_sync_from_disk():
                    updated_count += 1
            else:
                # Create (no parent yet)
                title = filename[:-3]
                content = ""
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.startswith('---'):
                            try:
                                end_fm = content.find('\n---', 3)
                                if end_fm != -1:
                                    fm_lines = content[3:end_fm].split('\n')
                                    for line in fm_lines:
                                        if line.strip().startswith('title:'):
                                            title = line.split(':', 1)[1].strip()
                                            break
                            except: pass
                except Exception as e:
                    _logger.error(f"Error reading {rel_path}: {e}")
                    continue

                try:
                    self.create({
                        'name': title,
                        'content_md': content,
                        'file_path': rel_path, # Crucial: force path to match disk
                        'parent_id': False, # Resolve in Pass 2
                    })
                    created_count += 1
                except Exception as e:
                    _logger.error(f"Failed to create {rel_path}: {e}")

        # Pass 2: Link Parents
        # We iterate again to find parents based on directory structure
        # Logic: If I am 'Section/Page.md', my parent is the page at 'Section.md'
        # Or if I am 'Section/Sub/Page_2.md', parent is 'Section/Sub.md'
        
        # Reload mapping (path -> id)
        # Note: file_path is computed. If we created records, they have computed paths.
        # Hopefully they match the disk paths.
        pages = self.search([])
        path_to_id = {p.file_path: p.id for p in pages if p.file_path}
        
        for p in pages:
            # Skip if manually set (maybe?) No, sync implies adhering to disk structure.
            # But let's only update if missing or if strictly enforcing.
            # For now, let's strict enforce disk structure.
            
            if not p.file_path: continue
            
            # Expected parent path
            # 'A/B.md' -> Parent is 'A.md'
            # 'A/B/C.md' -> Parent is 'A/B.md'
            # 'Root.md' -> No parent
            
            current_dir = os.path.dirname(p.file_path) # 'A' or 'A/B' or ''
            if not current_dir:
                if p.parent_id:
                   # Moves to root? Maybe user moved it on disk.
                   p.parent_id = False
                continue
                
            parent_path_candidate = current_dir + '.md'
            if parent_path_candidate in path_to_id:
                parent_id = path_to_id[parent_path_candidate]
                if p.parent_id.id != parent_id:
                    p.parent_id = parent_id
                    
        if created_count or updated_count:
            _logger.info(f"Sync complete: {created_count} created, {updated_count} updated.")
            
        # Pass 3: Prune (Delete records whose files are gone)
        # We check all pages that have a file_path but that file_path wasn't found in current scan
        # 'path_to_id' currently has all pages
        
        # Collect actual paths found on disk from 'all_files'
        disk_paths = set(f[1] for f in all_files)
        
        deleted_count = 0
        pages_to_delete = self.env['doc.page']
        
        for p in pages:
            if not p.file_path: continue
            
            # If path not in disk_paths, it's deleted physically
            if p.file_path not in disk_paths:
                # Double check existence to be safe (maybe we missed it?)
                full_path_check = os.path.join(repo_path, p.file_path)
                if not os.path.exists(full_path_check):
                    pages_to_delete += p
        
        if len(pages_to_delete) > 0:
            deleted_count = len(pages_to_delete)
            _logger.info(f"Pruning {deleted_count} orphaned records: {pages_to_delete.mapped('file_path')}")
            # We call unlink, BUT we must ensure unlink doesn't fail trying to delete the missing file
            # We already handled that in _delete_from_git with exists check.
            pages_to_delete.unlink()
            
        if deleted_count:
             _logger.info(f"Pruned {deleted_count} records.")

        return updated_count + created_count + deleted_count

    def _delete_from_git(self):
        repo_path = self._get_git_repo_path()
        if not repo_path:
            return
        full_path = os.path.join(repo_path, self.file_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                # If directory is empty, remove it? 
                # Complexity: if we delete parent with children, children are deleted in Odoo (cascade), 
                # so we should delete their files too.
            except OSError as e:
                _logger.error(f"Failed to delete file {full_path}: {e}")

    def get_breadcrumbs(self):
        """Returns a list of dictionaries [{'id': id, 'name': name}] for ancestors"""
        self.ensure_one()
        breadcrumbs = []
        current = self.parent_id
        while current:
            breadcrumbs.insert(0, {'id': current.id, 'name': current.name})
            current = current.parent_id
        return breadcrumbs

    @api.model
    def get_nav_tree(self):
        """Returns the page tree structure for the sidebar"""
        def build_tree(pages):
            tree = []
            for page in pages:
                tree.append({
                    'id': page.id,
                    'name': page.name,
                    'file_path': page.file_path,
                    'children': build_tree(page.child_ids.sorted('sequence'))
                })
            return tree

        root_pages = self.search([('parent_id', '=', False)], order='sequence, id')
        return build_tree(root_pages)

    @api.model
    def create_demo_data(self):
        """Create some demo data for testing"""
        if not self.search([]):
            root = self.create({
                'name': 'Documentation Root',
                'content_md': '# Welcome\nThis is the root page.'
            })
            self.create({
                'name': 'Getting Started',
                'parent_id': root.id,
                'content_md': '## Getting Started\nSteps to start...'
            })
