# Odoo Doc Studio 📚

**Professional Documentation Management for Odoo v19**

Doc Studio transforms Odoo into a powerful, modern documentation platform that delights both developers and business users. It combines the simplicity of a Wiki with the power of **Git and Markdown** workflows.

[![Odoo Version](https://img.shields.io/badge/Odoo-19.0-blue)](https://www.odoo.com/)
[![License](https://img.shields.io/badge/License-LGPL--3-green)](https://www.gnu.org/licenses/lgpl-3.0.html)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)

## 🚀 Why Doc Studio?

### Hybrid Editing Experience
- **Business Users:** Comfortable WYSIWYG visual editor
- **Technical Writers:** Direct Markdown source editing
- **Advanced Users:** Full HTML source access for fine-tuning

### Markdown-First Approach
- All content stored as standard `.md` files
- 100% compatible with Obsidian, VS Code, and GitHub
- No proprietary database lock-in

### Bidirectional Sync
- Changes on disk update Odoo automatically
- Changes in Odoo update files on disk
- Perfect mirror synchronization

## ✨ Key Features

### 1. **Bidirectional Synchronization**
- Mirror effect: Delete a file on disk, it disappears from Odoo
- Auto-import: Drop a Markdown folder and Odoo rebuilds the entire hierarchy
- Real-time updates with configurable Git sync

### 2. **Smart Internal Navigation**
- Link documents using standard relative paths: `[Guide](../folder/doc.md)`
- Automatic conversion to navigable Odoo links
- Breadcrumb navigation for easy context

### 3. **Enterprise-Grade Security**
- Role-based access control (RBAC)
- Document-level permissions (Private/Internal/Public)
- Share documents with specific users
- Audit trail for all changes

### 4. **Multi-Language Support**
- Full internationalization (i18n)
- Translations: English, Spanish (ES/AR)
- Easy to add more languages

### 5. **Dark Mode Compatible**
- Seamless light/dark theme switching
- Follows Odoo's native theme system
- Optimized for readability in both modes

### 6. **Git Integration**
- Sync with remote repositories (GitHub/GitLab)
- Version control built-in
- Automated backup and restore

## 📊 Comparison: Doc Studio vs Others

| Feature | **Doc Studio** | Confluence | Google Docs | Docusaurus | Odoo Knowledge |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Storage Format** | **Markdown (.md)** | Proprietary | Proprietary | Markdown | Proprietary (HTML) |
| **Version Control** | **Native Git** | Internal history | Internal history | Git | Internal history |
| **Editor** | **Hybrid (Visual/MD/HTML)** | Visual | Visual | Code only | Visual |
| **ERP Integration** | **Total (Native Odoo)** | None | None | None | Total |
| **Offline-first** | **Yes (via VS Code/Git)** | No | Limited | Yes | No |
| **Portability** | **Maximum (Filesystem)** | Low | Low | High | Low |
| **Multi-language** | **Yes** | Yes | Yes | Yes | Limited |
| **Dark Mode** | **Yes** | Limited | No | Yes | Yes |

## 🛠️ Installation

### Requirements
- Odoo 19.0+
- Python 3.12+
- Git (for sync features)
- Python packages: `markdownify`, `GitPython`, `markdown`

### Quick Install

1. Clone the repository:
```bash
git clone git@github.com:francuello10/odoo_doc_studio.git
```

2. Copy to your Odoo addons directory:
```bash
cp -r odoo_doc_studio /path/to/odoo/addons/
```

3. Update module list in Odoo
4. Install "Doc Studio" from Apps

### Configuration

1. Go to **Settings → Doc Studio**
2. Set **Repository Path**: Absolute path to your docs folder (e.g., `/mnt/docs_repo`)
3. (Optional) Set **Git Repository URL** for remote sync

## 👩‍💻 User Workflow

### Creating Documents
1. Click **"New"** and start writing immediately
2. Choose parent page for hierarchy
3. Add tags for categorization
4. Set visibility (Private/Internal/Public)

### Importing Existing Docs
1. Click **"Edit"** on any page
2. Switch to **"Markdown"** tab
3. Paste your Markdown content
4. Save and it's automatically converted

### Linking Documents
- Use relative paths: `[Name](../folder/doc.md)`
- Or use doc IDs: `[Name](doc://123)`
- Internal links are automatically resolved

### Syncing with Git
1. Edit files in VS Code or any editor
2. Click **"Sync"** in Odoo
3. Changes are reflected immediately

## 🔒 Security Features

- **Access Control Lists (ACL)**: Fine-grained permissions
- **Record Rules**: Row-level security
- **Input Sanitization**: Protection against XSS/SQL injection
- **Path Validation**: Prevention of directory traversal attacks
- **Audit Logging**: Track all document changes

## 🌍 Internationalization

Fully translated interface:
- 🇺🇸 English (US)
- 🇪🇸 Spanish (ES)
- 🇦🇷 Spanish (Argentina)

Add more languages by contributing `.po` files!

## 📝 Best Practices

### For Business Users
- Use the visual editor for rich formatting
- Organize docs with workspaces and tags
- Share documents with specific teams
- Use breadcrumbs for navigation

### For Developers
- Edit Markdown files directly in your IDE
- Use Git for version control
- Link docs using relative paths
- Keep frontmatter metadata updated

### For Administrators
- Regular Git backups
- Monitor sync cron jobs
- Review access permissions periodically
- Keep dependencies updated

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Follow Odoo coding guidelines
4. Add tests for new features
5. Submit a pull request

## 📄 License

This module is licensed under LGPL-3.0.

## 🙏 Credits

**Author:** Francisco Cuello  
**Version:** 1.1  
**Category:** Productivity/Documentation

## 📞 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Contact: frcuello@ubp.edu.ar

---

**Made with ❤️ for the Odoo Community**
