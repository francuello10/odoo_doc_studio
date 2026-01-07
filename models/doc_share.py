from odoo import models, fields

class DocShare(models.Model):
    _name = 'doc.share'
    _description = 'Document Share'
    
    page_id = fields.Many2one('doc.page', string='Document', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Shared With', required=True)
    permission = fields.Selection([
        ('read', 'Viewer'),
        ('write', 'Editor')
    ], string='Permission', default='read', required=True)
    
    _sql_constraints = [
        ('unique_share', 'unique(page_id, user_id)', 'User already has access to this document')
    ]
