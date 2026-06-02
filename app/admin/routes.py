from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app.models import Sector, Category, Document, Announcement, AuditLog, AccessLog, User, Role, Permission
from app import db
from app.utils import log_audit, generate_thumbnail, permission_required
import os
from werkzeug.utils import secure_filename
from datetime import datetime

admin = Blueprint('admin', __name__)

@admin.before_request
def check_active():
    if current_user.is_authenticated and not current_user.is_active:
        from flask_login import logout_user
        logout_user()
        flash('Sua conta foi desativada.', 'danger')
        return redirect(url_for('auth.login'))

@admin.route('/manage')
@permission_required('view_reports')
def manage():
    sectors = Sector.query.all()
    categories = Category.query.all()
    return render_template('admin/manage.html', sectors=sectors, categories=categories)

@admin.route('/sector/add', methods=['POST'])
@permission_required('manage_sectors')
def add_sector():
    name = request.form.get('sector_name')
    if name:
        sector = Sector(name=name)
        db.session.add(sector)
        db.session.commit()
        log_audit('add', 'sector', sector.id, f'Setor "{name}" criado.')
        flash(f'Setor "{name}" adicionado!', 'success')
    return redirect(url_for('admin.manage'))

@admin.route('/sector/delete/<int:sector_id>', methods=['POST'])
@permission_required('manage_sectors')
def delete_sector(sector_id):
    sector = Sector.query.get_or_404(sector_id)
    if sector.documents:
        flash(f'Não é possível excluir o setor "{sector.name}" pois ele possui documentos vinculados.', 'danger')
    else:
        db.session.delete(sector)
        db.session.commit()
        log_audit('delete', 'sector', sector_id, f'Setor "{sector.name}" excluído.')
        flash(f'Setor "{sector.name}" excluído com sucesso!', 'success')
    return redirect(url_for('admin.manage'))

@admin.route('/sector/edit/<int:sector_id>', methods=['POST'])
@permission_required('manage_sectors')
def edit_sector(sector_id):
    sector = Sector.query.get_or_404(sector_id)
    new_name = request.form.get('sector_name')
    if new_name:
        old_name = sector.name
        sector.name = new_name
        db.session.commit()
        log_audit('edit', 'sector', sector_id, f'Setor renomeado de "{old_name}" para "{new_name}".')
        flash(f'Setor "{old_name}" renomeado para "{new_name}"!', 'success')
    return redirect(url_for('admin.manage'))

@admin.route('/category/add', methods=['POST'])
@permission_required('manage_categories')
def add_category():
    name = request.form.get('category_name')
    if name:
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        log_audit('add', 'category', category.id, f'Categoria "{name}" criada.')
        flash(f'Categoria "{name}" adicionada!', 'success')
    return redirect(url_for('admin.manage'))

@admin.route('/category/delete/<int:category_id>', methods=['POST'])
@permission_required('manage_categories')
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    # Move documents to 'No Category' or block deletion? 
    # For now, let's block if there are documents to be safe.
    if category.documents:
        flash(f'Não é possível excluir a categoria "{category.name}" pois ela possui documentos vinculados.', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        log_audit('delete', 'category', category_id, f'Categoria "{category.name}" excluída.')
        flash(f'Categoria "{category.name}" excluída!', 'success')
    return redirect(url_for('admin.manage'))

@admin.route('/category/edit/<int:category_id>', methods=['POST'])
@permission_required('manage_categories')
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    new_name = request.form.get('category_name')
    if new_name:
        old_name = category.name
        category.name = new_name
        db.session.commit()
        log_audit('edit', 'category', category_id, f'Categoria renomeada de "{old_name}" para "{new_name}".')
        flash(f'Categoria "{old_name}" renomeada para "{new_name}"!', 'success')
    return redirect(url_for('admin.manage'))

@admin.route('/upload', methods=['GET', 'POST'])
@permission_required('upload_docs')
def upload_doc():
    sectors = Sector.query.all()
    categories = Category.query.all()
    
    if request.method == 'POST':
        file = request.files.get('file')
        sector_id = request.form.get('sector_id')
        category_id = request.form.get('category_id')
        description = request.form.get('description')
        tags = request.form.get('tags')
        
        if not file or file.filename == '':
            flash('Nenhum arquivo selecionado.', 'warning')
            return redirect(request.url)
            
        if file and sector_id:
            from flask import current_app
            filename = secure_filename(file.filename)
            unique_filename = f"{int(datetime.now().timestamp())}_{filename}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            doc = Document(
                title=filename, 
                filename=unique_filename,
                original_filename=filename,
                description=description,
                sector_id=sector_id,
                category_id=category_id if category_id else None,
                tags=tags,
                user_id=current_user.id
            )
            db.session.add(doc)
            db.session.commit()
            
            # Gerar miniatura
            generate_thumbnail(doc.id)
            
            log_audit('upload', 'document', doc.id, f'Documento "{filename}" enviado.')
            flash('Documento enviado com sucesso!', 'success')
            return redirect(url_for('admin.manage'))
            
    return render_template('admin/upload.html', sectors=sectors, categories=categories)

@admin.route('/documents')
@permission_required('edit_docs')
def list_docs():
    filter_type = request.args.get('filter', 'all')
    q = request.args.get('q', '').strip()
    sector_id = request.args.get('sector_id', type=int)
    category_id = request.args.get('category_id', type=int)

    query = Document.query

    if q:
        like_pattern = f"%{q}%"
        query = query.outerjoin(Category).filter(
            (Document.title.ilike(like_pattern)) |
            (Document.original_filename.ilike(like_pattern)) |
            (Document.description.ilike(like_pattern)) |
            (Document.tags.ilike(like_pattern)) |
            (Category.name.ilike(like_pattern))
        )

    if sector_id:
        query = query.filter_by(sector_id=sector_id)
    if category_id:
        query = query.filter_by(category_id=category_id)

    if filter_type == 'no_category':
        query = query.filter(Document.category_id == None)
    elif filter_type == 'no_tags':
        query = query.filter((Document.tags == None) | (Document.tags == ''))
        
    docs = query.order_by(Document.upload_date.desc()).all()
    sectors = Sector.query.all()
    categories = Category.query.all()
    return render_template('admin/list_documents.html', documents=docs, current_filter=filter_type,
                           q=q, sectors=sectors, categories=categories,
                           current_sector=sector_id, current_category=category_id)

@admin.route('/documents/bulk_update', methods=['POST'])
@permission_required('edit_docs')
def bulk_update_docs():
    selected_ids = request.form.getlist('doc_ids')
    if not selected_ids:
        flash('Selecione ao menos um documento para aplicar a ação em lote.', 'warning')
        return redirect(url_for('admin.list_docs', **request.args))

    bulk_action = request.form.get('bulk_action', 'update')
    docs = Document.query.filter(Document.id.in_(selected_ids)).all()

    if bulk_action == 'delete':
        if not current_user.has_permission('delete_docs'):
            abort(403)

        deleted_count = 0
        for doc in docs:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(doc)
            deleted_count += 1

        if deleted_count:
            db.session.commit()
            log_audit('delete', 'document', None, f'Exclusão em lote de {deleted_count} documento(s).')
            flash(f'{deleted_count} documento(s) excluído(s) com sucesso!', 'success')
        else:
            flash('Nenhum documento encontrado para exclusão.', 'warning')

        return redirect(url_for('admin.list_docs'))

    sector_value = request.form.get('bulk_sector_id')
    category_value = request.form.get('bulk_category_id')
    bulk_tags = request.form.get('bulk_tags', '').strip()
    tag_action = request.form.get('tag_action', 'replace')

    sector_id = int(sector_value) if sector_value and sector_value.isdigit() else None
    category_id = int(category_value) if category_value and category_value.isdigit() else None

    updated_count = 0
    for doc in docs:
        updated = False

        if sector_id is not None:
            doc.sector_id = sector_id
            updated = True

        if category_value is not None and category_value != '':
            if category_value == '-1':
                doc.category_id = None
            else:
                doc.category_id = category_id
            updated = True

        if bulk_tags:
            if tag_action == 'append':
                existing_tags = [t.strip() for t in (doc.tags or '').split(',') if t.strip()]
                new_tags = [t.strip() for t in bulk_tags.split(',') if t.strip()]
                combined = existing_tags + [t for t in new_tags if t not in existing_tags]
                doc.tags = ', '.join(combined)
            else:
                doc.tags = ', '.join([t.strip() for t in bulk_tags.split(',') if t.strip()])
            updated = True

        if updated:
            updated_count += 1

    if updated_count:
        db.session.commit()
        flash(f'Ações em lote aplicadas a {updated_count} documento(s).', 'success')
    else:
        flash('Nenhuma alteração foi aplicada. Verifique as opções selecionadas.', 'warning')

    return redirect(url_for('admin.list_docs'))

@admin.route('/document/edit/<int:doc_id>', methods=['GET', 'POST'])
@permission_required('edit_docs')
def edit_doc(doc_id):
    doc = Document.query.get_or_404(doc_id)
    sectors = Sector.query.all()
    categories = Category.query.all()
    
    if request.method == 'POST':
        doc.title = request.form.get('title')
        doc.description = request.form.get('description')
        doc.sector_id = request.form.get('sector_id')
        doc.category_id = request.form.get('category_id')
        doc.tags = request.form.get('tags')
        
        if not doc.category_id: # Handle empty selection
            doc.category_id = None
            
        db.session.commit()
        log_audit('edit', 'document', doc.id, f'Metadados do documento "{doc.title}" atualizados.')
        flash(f'Documento "{doc.title}" atualizado!', 'success')
        return redirect(url_for('admin.list_docs'))
        
    return render_template('admin/edit_document.html', doc=doc, sectors=sectors, categories=categories)
@admin.route('/document/delete/<int:doc_id>', methods=['POST'])
@permission_required('delete_docs')
def delete_doc(doc_id):
    doc = Document.query.get_or_404(doc_id)
    title = doc.title
    
    # Remover arquivo físico
    from flask import current_app
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Remover do Banco de Dados
    db.session.delete(doc)
    db.session.commit()
    log_audit('delete', 'document', doc_id, f'Documento "{title}" excluído do sistema.')
    
    flash(f'Documento "{title}" excluído com sucesso!', 'success')
    return redirect(url_for('admin.list_docs'))
@admin.route('/announcements')
@permission_required('manage_announcements')
def manage_announcements():
    announcements = Announcement.query.order_by(Announcement.date_posted.desc()).all()
    return render_template('admin/manage_announcements.html', announcements=announcements)

@admin.route('/announcement/add', methods=['POST'])
@permission_required('manage_announcements')
def add_announcement():
    title = request.form.get('title')
    content = request.form.get('content')
    is_important = 'is_important' in request.form
    
    if title and content:
        announcement = Announcement(
            title=title,
            content=content,
            is_important=is_important,
            user_id=current_user.id
        )
        db.session.add(announcement)
        db.session.commit()
        log_audit('add', 'announcement', announcement.id, f'Aviso "{title}" publicado.')
        flash('Aviso publicado com sucesso!', 'success')
    else:
        flash('Título e conteúdo são obrigatórios.', 'warning')
        
    return redirect(url_for('admin.manage_announcements'))

@admin.route('/announcement/delete/<int:ann_id>', methods=['POST'])
def delete_announcement(ann_id):
    announcement = Announcement.query.get_or_404(ann_id)
    title = announcement.title
    db.session.delete(announcement)
    db.session.commit()
    log_audit('delete', 'announcement', ann_id, f'Aviso "{title}" excluído.')
    flash('Aviso excluído com sucesso!', 'success')
    return redirect(url_for('admin.manage_announcements'))

@admin.route('/announcement/edit/<int:ann_id>', methods=['GET', 'POST'])
def edit_announcement(ann_id):
    announcement = Announcement.query.get_or_404(ann_id)
    if request.method == 'POST':
        announcement.title = request.form.get('title')
        announcement.content = request.form.get('content')
        announcement.is_important = 'is_important' in request.form
        db.session.commit()
        log_audit('edit', 'announcement', ann_id, f'Aviso "{announcement.title}" atualizado.')
        flash('Aviso atualizado!', 'success')
        return redirect(url_for('admin.manage_announcements'))
    return render_template('admin/edit_announcement.html', announcement=announcement)

@admin.route('/reports')
@permission_required('view_reports')
def reports():
    from sqlalchemy import func
    import sqlalchemy as sa
    
    # Statistics
    total_docs = Document.query.count()
    total_sectors = Sector.query.count()
    total_categories = Category.query.count()
    
    # Top accessed documents (last 30 days or all time)
    top_docs = db.session.query(
        Document, func.count(AccessLog.id).label('access_count')
    ).join(AccessLog).group_by(Document.id).order_by(sa.text('access_count DESC')).limit(10).all()
    
    # Recent audit logs
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(50).all()
    
    return render_template('admin/reports.html', 
                           total_docs=total_docs,
                           total_sectors=total_sectors,
                           total_categories=total_categories,
                           top_docs=top_docs,
                           recent_logs=recent_logs)

# --- USER MANAGEMENT ---

@admin.route('/users')
@permission_required('manage_users')
def list_users():
    users = User.query.all()
    roles = Role.query.all()
    return render_template('admin/users.html', users=users, roles=roles)

@admin.route('/user/add', methods=['POST'])
@permission_required('manage_users')
def add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role_id = request.form.get('role_id', type=int)
    
    if User.query.filter_by(username=username).first():
        flash('Nome de usuário já existe.', 'danger')
        return redirect(url_for('admin.list_users'))
        
    user = User(username=username, email=email, role_id=role_id)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    log_audit('add', 'user', user.id, f'Novo usuário "{username}" criado.')
    flash(f'Usuário "{username}" criado com sucesso!', 'success')
    return redirect(url_for('admin.list_users'))

@admin.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@permission_required('manage_users')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        role_id = request.form.get('role_id', type=int)
        user.role_id = role_id
        
        password = request.form.get('password')
        if password:
            user.set_password(password)
            
        db.session.commit()
        log_audit('edit', 'user', user.id, f'Usuário "{user.username}" atualizado.')
        flash(f'Usuário "{user.username}" atualizado!', 'success')
        return redirect(url_for('admin.list_users'))
        
    roles = Role.query.all()
    return render_template('admin/edit_user.html', user=user, roles=roles)

@admin.route('/user/toggle/<int:user_id>', methods=['POST'])
@permission_required('manage_users')
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode desativar sua própria conta!', 'danger')
        return redirect(url_for('admin.list_users'))
        
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "ativado" if user.is_active else "desativado"
    log_audit('edit', 'user', user.id, f'Usuário "{user.username}" {status}.')
    flash(f'Usuário "{user.username}" {status}!', 'success')
    return redirect(url_for('admin.list_users'))

@admin.route('/user/delete/<int:user_id>', methods=['POST'])
@permission_required('manage_users')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode excluir sua própria conta!', 'danger')
        return redirect(url_for('admin.list_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    log_audit('delete', 'user', user_id, f'Usuário "{username}" excluído.')
    flash(f'Usuário "{username}" removido do sistema.', 'success')
    return redirect(url_for('admin.list_users'))

# --- ROLE MANAGEMENT ---

@admin.route('/roles')
@permission_required('manage_users') # Only admins manage roles
def manage_roles():
    roles = Role.query.all()
    permissions = Permission.query.all()
    return render_template('admin/roles.html', roles=roles, permissions=permissions)

@admin.route('/role/permissions/<int:role_id>', methods=['POST'])
@permission_required('manage_users')
def update_role_permissions(role_id):
    role = Role.query.get_or_404(role_id)
    perm_ids = request.form.getlist('permissions', type=int)
    
    perms = Permission.query.filter(Permission.id.in_(perm_ids)).all()
    role.permissions = perms
    db.session.commit()
    
    log_audit('edit', 'role', role.id, f'Permissões do perfil "{role.name}" atualizadas.')
    flash(f'Permissões do perfil "{role.name}" atualizadas!', 'success')
    return redirect(url_for('admin.manage_roles'))
