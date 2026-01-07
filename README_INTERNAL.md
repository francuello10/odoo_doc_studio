# Doc Studio - Internal Technical Documentation

**Version:** 1.1  
**Odoo Version:** 19.0  
**Last Updated:** 2026-01-07

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Security Implementation](#security-implementation)
3. [Code Quality & Best Practices](#code-quality--best-practices)
4. [Performance Optimizations](#performance-optimizations)
5. [Testing Strategy](#testing-strategy)
6. [Deployment Guide](#deployment-guide)
7. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

### Module Structure

```
odoo_doc_studio/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── doc_page.py          # Main document model
│   ├── doc_workspace.py     # Workspace organization
│   ├── doc_tag.py           # Tagging system
│   ├── doc_share.py         # Sharing & permissions
│   ├── doc_git.py           # Git operations
│   └── res_config_settings.py
├── views/
│   ├── doc_page_views.xml
│   ├── doc_workspace_views.xml
│   ├── doc_tag_views.xml
│   └── res_config_settings_views.xml
├── security/
│   ├── doc_studio_security.xml  # Groups & categories
│   ├── ir.model.access.csv      # Model access rights
│   └── ir_rule.xml              # Record rules
├── data/
│   ├── doc_tag_data.xml         # Default tags
│   ├── config_data.xml          # System parameters
│   └── doc_git_cron.xml         # Scheduled actions
├── static/
│   └── src/
│       ├── components/          # OWL components
│       └── scss/                # Styles
└── i18n/                        # Translations
    ├── es.po
    ├── es_AR.po
    └── en_US.po
```

### Data Flow

```
User Action (Browser)
    ↓
OWL Component (JavaScript)
    ↓
RPC Call to Odoo Backend
    ↓
Python Model Method
    ↓
ORM Operations
    ↓
Database / Filesystem
```

### Key Models

#### 1. `doc.page` - Core Document Model
- **Purpose:** Stores documentation pages
- **Storage:** Dual (DB + Filesystem)
- **Key Fields:**
  - `name`: Document title
  - `body_html`: Rendered HTML content
  - `content_md`: Markdown source
  - `file_path`: Path on disk
  - `parent_id`: Hierarchical structure
  - `workspace_id`: Organization
  - `tag_ids`: Categorization
  - `visibility`: Access level (private/internal/public)

#### 2. `doc.workspace` - Organization
- **Purpose:** Group documents by project/team
- **Features:** Color coding, archiving, page count

#### 3. `doc.share` - Permissions
- **Purpose:** Fine-grained access control
- **Permissions:** read, write, owner

#### 4. `doc.git` - Version Control
- **Purpose:** Git operations (pull/push/sync)
- **Features:** Automated sync via cron

---

## 🔒 Security Implementation

### 1. Access Control

#### Groups (security/doc_studio_security.xml)
```xml
- group_doc_studio_user: Basic users (read/write own docs)
- group_doc_studio_manager: Administrators (full access)
```

#### Model Access Rights (security/ir.model.access.csv)
- All models accessible to `base.group_user`
- Fine-tuned via record rules

#### Record Rules (security/ir_rule.xml)
```python
# Users can only see:
# 1. Public documents
# 2. Internal documents (if employee)
# 3. Private documents they own or are shared with
```

### 2. Input Sanitization

**Implemented in:**
- `doc_page.py`: HTML sanitization using `markdownify`
- Path validation in file operations
- SQL injection prevention via ORM

**Example:**
```python
def _sanitize_path(self, path):
    """Prevent directory traversal attacks"""
    clean_path = os.path.normpath(path)
    if '..' in clean_path or clean_path.startswith('/'):
        raise ValidationError(_("Invalid path"))
    return clean_path
```

### 3. XSS Protection

- All user input escaped in templates
- HTML content sanitized before storage
- CSP headers enforced by Odoo

### 4. CSRF Protection

- Odoo's built-in CSRF tokens
- All state-changing operations use POST
- Session validation on every request

---

## 💎 Code Quality & Best Practices

### Odoo v19 Compliance

#### ✅ ORM Best Practices
```python
# ✓ Good: Batch operations
self.env['doc.page'].search([...]).write({...})

# ✗ Bad: Loop with individual writes
for page in pages:
    page.write({...})
```

#### ✅ API Decorators
```python
@api.depends('body_html')
def _compute_reading_time(self):
    """Computed fields with proper depends"""
    ...

@api.constrains('name', 'parent_id')
def _check_unique_name(self):
    """Constraints for data validation"""
    ...

@api.model
def create(self, vals):
    """Model-level methods"""
    ...
```

#### ✅ Field Definitions
```python
# Proper field attributes
name = fields.Char(
    string="Title",
    required=True,
    index=True,  # For performance
    translate=True  # For i18n
)
```

### Code Style

- **PEP 8** compliance
- **Docstrings** for all public methods
- **Type hints** where applicable
- **Logging** for debugging (not print statements)

```python
import logging
_logger = logging.getLogger(__name__)

def sync_from_disk(self):
    """Sync documents from filesystem to database.
    
    Returns:
        int: Number of documents synchronized
    """
    _logger.info("Starting disk sync...")
    ...
```

---

## ⚡ Performance Optimizations

### 1. Database Indexes

```python
# In model definitions
name = fields.Char(index=True)  # Frequently searched
file_path = fields.Char(index=True)  # Used in lookups
```

### 2. Lazy Loading

```python
# Use sudo() sparingly
# Prefer domain filters over post-processing
pages = self.env['doc.page'].search([
    ('workspace_id', '=', workspace_id)
], limit=100)  # Limit results
```

### 3. Caching

```python
@tools.ormcache('self.id')
def _get_breadcrumbs(self):
    """Cache expensive computations"""
    ...
```

### 4. Batch Operations

```python
# ✓ Good: Single DB query
self.env['doc.page'].search([...]).unlink()

# ✗ Bad: Multiple queries
for page in pages:
    page.unlink()
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/test_doc_page.py
from odoo.tests import TransactionCase

class TestDocPage(TransactionCase):
    def setUp(self):
        super().setUp()
        self.DocPage = self.env['doc.page']
    
    def test_create_page(self):
        page = self.DocPage.create({'name': 'Test'})
        self.assertTrue(page.exists())
```

### Integration Tests

- Test Git sync operations
- Test file system operations
- Test permission rules

### Security Tests

- Test unauthorized access attempts
- Test SQL injection prevention
- Test XSS prevention

---

## 🚀 Deployment Guide

### Production Checklist

- [ ] Set `doc_studio_repo_path` in system parameters
- [ ] Configure Git credentials (if using remote sync)
- [ ] Set up automated backups
- [ ] Review and adjust cron job frequency
- [ ] Enable logging for monitoring
- [ ] Test permissions with different user roles
- [ ] Verify dark mode compatibility
- [ ] Test all translations

### Environment Variables

```bash
# In odoo.conf or environment
ODOO_DOC_STUDIO_REPO_PATH=/mnt/docs
ODOO_DOC_STUDIO_GIT_URL=https://github.com/org/docs.git
```

### Docker Deployment

```dockerfile
# Ensure dependencies are installed
RUN pip install markdownify GitPython markdown

# Mount docs volume
VOLUME ["/mnt/docs"]
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Permission Denied" on File Operations

**Cause:** Odoo user doesn't have write access to repo path

**Solution:**
```bash
sudo chown -R odoo:odoo /mnt/docs
sudo chmod -R 755 /mnt/docs
```

#### 2. Git Sync Fails

**Cause:** Missing Git credentials or network issues

**Solution:**
- Check Git URL configuration
- Verify SSH keys or HTTPS credentials
- Check network connectivity
- Review cron job logs

#### 3. Translations Not Showing

**Cause:** Module not updated after adding translations

**Solution:**
```bash
# Update module
odoo -u odoo_doc_studio -d your_database

# Or via UI: Apps → Doc Studio → Upgrade
```

#### 4. Dark Mode Issues

**Cause:** Hardcoded colors in custom CSS

**Solution:**
- Use Odoo CSS variables: `var(--body-color)`, `var(--View-bg)`
- Avoid fixed color values

### Debug Mode

Enable debug logging:
```python
# In code
import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
```

---

## 📊 Monitoring & Metrics

### Key Metrics to Track

1. **Document Count:** Total active documents
2. **Sync Frequency:** Git sync success/failure rate
3. **User Activity:** Document views/edits per day
4. **Storage Usage:** Disk space consumed
5. **Performance:** Average page load time

### Logging

```python
# Important events to log
_logger.info("Document created: %s", page.name)
_logger.warning("Sync failed: %s", error)
_logger.error("Permission denied: %s", user.name)
```

---

## 🔄 Maintenance

### Regular Tasks

- **Daily:** Review sync logs
- **Weekly:** Check disk usage
- **Monthly:** Review permissions
- **Quarterly:** Update dependencies

### Backup Strategy

1. **Database:** Odoo's built-in backup
2. **Files:** Git repository (automatic)
3. **Configuration:** Export system parameters

---

## 📚 References

- [Odoo 19 Documentation](https://www.odoo.com/documentation/19.0/)
- [OWL Framework](https://github.com/odoo/owl)
- [Markdown Specification](https://commonmark.org/)
- [Git Best Practices](https://git-scm.com/book/en/v2)

---

## 🤝 Contributing

### Code Review Checklist

- [ ] Follows Odoo coding guidelines
- [ ] Includes docstrings
- [ ] Has appropriate logging
- [ ] Includes security checks
- [ ] Performance optimized
- [ ] Translations updated
- [ ] Tests added/updated

### Commit Message Format

```
type(scope): subject

body

footer
```

**Types:** feat, fix, docs, style, refactor, perf, test, chore

**Example:**
```
feat(doc_page): add automatic title generation

- Implement slug-based title generation
- Add uniqueness validation
- Update translations

Closes #123
```

---

**Last Review:** 2026-01-07  
**Next Review:** 2026-04-07  
**Maintainer:** Francisco Cuello
