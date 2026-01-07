from odoo import models, fields, api


class DocWorkspace(models.Model):
    _name = 'doc.workspace'
    _description = 'Documentation Workspace'
    _order = 'sequence, name'

    name = fields.Char(string='Workspace Name', required=True)
    description = fields.Text(string='Description')
    color = fields.Integer(string='Color Index', default=0)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)
    page_ids = fields.One2many('doc.page', 'workspace_id', string='Pages')
    page_count = fields.Integer(compute='_compute_page_count', string='Page Count')

    @api.depends('page_ids')
    def _compute_page_count(self):
        for workspace in self:
            workspace.page_count = len(workspace.page_ids)

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Workspace name must be unique!')
    ]
