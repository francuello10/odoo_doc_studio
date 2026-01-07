{
    'name': 'Doc Studio',
    'version': '1.1',
    'category': 'Productivity/Documentation',
    'summary': 'Confluence-like Documentation Studio with Git Sync',
    'description': """
        A Single Page Application (SPA) for managing documentation in Odoo.
        
        **Key Features:**
        - **Bidirectional Sync:** Edit in Odoo or your favorite IDE (VS Code/Obsidian). Changes sync automatically.
        - **Markdown First:** Stored as .md files, rendered as HTML. Supports Frontmatter metadata.
        - **Internal Navigation:** Use relative paths `[Procedures](../procedures/login.md)` to link documents.
        - **File System Mirroring:** Folder structure on disk matches navigation tree in Odoo.
        - **Mass Management:** Dedicated List View for bulk deletion and export.
        - **Permissions Handling:** Auto-managed file permissions (chmod) for seamless host-container interaction.
        - **Visual Editor:** WYSIWYG editor for non-technical users.
    """,
    'author': 'Francisco Cuello',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/doc_studio_security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/doc_tag_data.xml',
        'data/config_data.xml',
        'data/server_actions.xml',
        'data/doc_git_cron.xml',
        'report/doc_page_report.xml',
        'views/doc_page_views.xml',
        'views/res_config_settings_views.xml',
        'views/doc_tag_views.xml',
        'views/doc_workspace_views.xml',
        'views/doc_studio_actions.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_doc_studio/static/src/scss/doc_studio.scss',
            'odoo_doc_studio/static/src/components/**/*.js',
            'odoo_doc_studio/static/src/components/**/*.xml',
            # Explicitly ensure share dialog is included (glob covers it, but good to be aware)
        ],
    },
    'external_dependencies': {
        'python': ['markdownify', 'GitPython', 'markdown'],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
