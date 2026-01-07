from odoo import models, fields, api


class DocTag(models.Model):
    _name = 'doc.tag'
    _description = 'Documentation Tag'
    _order = 'sequence, name'

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color Index', default=0)
    sequence = fields.Integer(string='Sequence', default=10)
    page_ids = fields.Many2many('doc.page', 'doc_page_tag_rel', 'tag_id', 'page_id', string='Pages')
    page_count = fields.Integer(compute='_compute_page_count', string='Page Count')

    @api.depends('page_ids')
    def _compute_page_count(self):
        for tag in self:
            tag.page_count = len(tag.page_ids)

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Tag name must be unique!')
    ]
