from flask_login import current_user
from app.models import AuditLog, Document
from app import db
import os
from PIL import Image
from flask import current_app

def log_audit(action, target_type=None, target_id=None, details=None):
    """
    Registra uma ação no log de auditoria.
    """
    log = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    db.session.add(log)
    db.session.commit()

def generate_thumbnail(doc_id):
    """
    Gera uma miniatura para o documento.
    Suporta imagens. Para outros tipos, define um ícone padrão.
    """
    doc = Document.query.get(doc_id)
    if not doc:
        return
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    thumb_folder = os.path.join(upload_folder, 'thumbnails')
    if not os.path.exists(thumb_folder):
        os.makedirs(thumb_folder)
        
    file_path = os.path.join(upload_folder, doc.filename)
    thumb_filename = f"thumb_{doc.id}.jpg"
    thumb_path = os.path.join(thumb_folder, thumb_filename)
    
    ext = doc.filename.split('.')[-1].lower()
    
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        try:
            with Image.open(file_path) as img:
                img.thumbnail((200, 200))
                # Convert to RGB if necessary (for RGBA/PNG to JPEG)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img.save(thumb_path, "JPEG", quality=85)
                doc.thumbnail = os.path.join('thumbnails', thumb_filename).replace('\\', '/')
        except Exception as e:
            print(f"Erro ao gerar miniatura de imagem: {e}")
            doc.thumbnail = f"icons/{ext}.png" # Fallback if error
    elif ext == 'pdf':
        doc.thumbnail = "icons/pdf.png"
    elif ext in ['doc', 'docx']:
        doc.thumbnail = "icons/word.png"
    elif ext in ['xls', 'xlsx']:
        doc.thumbnail = "icons/excel.png"
    else:
        doc.thumbnail = "icons/generic.png"
        
    db.session.commit()

from functools import wraps
from flask import abort, redirect, url_for

def permission_required(permission_slug):
    """
    Decorador para rotas que exigem uma permissão específica.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_login import current_user
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not current_user.has_permission(permission_slug):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
