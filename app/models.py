from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Tabela associativa para many-to-many entre Role e Permission
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # Ex: "Upload Documentos"
    slug = db.Column(db.String(50), unique=True, nullable=False) # Ex: "upload_docs"

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # Ex: "Admin", "Gestor"
    description = db.Column(db.String(255))
    permissions = db.relationship('Permission', secondary=role_permissions, lazy='subquery',
                                  backref=db.backref('roles', lazy=True))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=True)
    
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=True)
    role_rel = db.relationship('Role', backref='users', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, perm_slug):
        if not self.role_rel:
            return False
        return any(p.slug == perm_slug for p in self.role_rel.permissions)

    @property
    def is_admin(self):
        return self.role_rel and self.role_rel.name == 'Admin'

class Sector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    documents = db.relationship('Document', backref='sector_rel', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # e.g., 'Portaria', 'Ata'
    documents = db.relationship('Document', backref='category_rel', lazy=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    description = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    sector_id = db.Column(db.Integer, db.ForeignKey('sector.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Who uploaded it
    
    tags = db.Column(db.String(255)) # Simple comma-separated tags for now
    is_active = db.Column(db.Boolean, default=True)
    thumbnail = db.Column(db.String(255)) # Path to the thumbnail image

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_important = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='announcements', lazy=True)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # None for system actions
    action = db.Column(db.String(50), nullable=False) # 'upload', 'edit', 'delete', 'download', 'login'
    target_type = db.Column(db.String(50)) # 'document', 'category', 'announcement', etc.
    target_id = db.Column(db.Integer)
    details = db.Column(db.String(255))
    user = db.relationship('User', backref='logs', lazy=True)

class AccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Anonymous access if allowed
    
    document = db.relationship('Document', backref=db.backref('access_logs', lazy=True, cascade='all, delete-orphan', passive_deletes=True))
    user = db.relationship('User', backref='access_history', lazy=True)


class PageView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    path = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    method = db.Column(db.String(10), default='GET')

    user = db.relationship('User', backref='page_views', lazy=True)
