from flask import Blueprint, render_template, request, send_from_directory, current_app, redirect, url_for
from flask_login import login_required
from app.models import Document, Sector, Category, AccessLog, Announcement
from app import db
from app.utils import permission_required
import os

documents = Blueprint('documents', __name__)

@documents.route('/')
@documents.route('/index')
def index():
    q = request.args.get('q', '').strip()
    if q:
        return redirect(url_for('documents.browse_all', q=q))
    
    sectors = Sector.query.all()
    recent_docs = Document.query.order_by(Document.upload_date.desc()).limit(5).all()
    announcements = Announcement.query.order_by(Announcement.date_posted.desc()).limit(3).all()
    return render_template('documents/dashboard.html', 
                           sectors=sectors, 
                           recent_docs=recent_docs,
                           announcements=announcements)

@documents.route('/sector/<int:sector_id>')
def list_by_sector(sector_id):
    sector = Sector.query.get_or_404(sector_id)
    return redirect(url_for('documents.browse_all', sector_id=sector_id))

@documents.route('/all')
def browse_all():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    sector_id = request.args.get('sector_id', type=int)
    category_id = request.args.get('category_id', type=int)
    file_type = request.args.get('file_type', '').lower()
    q = request.args.get('q', '').strip()
    
    query = Document.query.filter_by(is_active=True)
    
    if sector_id:
        query = query.filter_by(sector_id=sector_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if file_type:
        query = query.filter(Document.filename.ilike(f'%.{file_type}'))
    if q:
        query = query.filter(
            (Document.title.contains(q)) | 
            (Document.description.contains(q)) | 
            (Document.tags.contains(q))
        )
        
    pagination = query.order_by(Document.upload_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items
    sectors = Sector.query.all()
    categories = Category.query.all()
    
    return render_template('documents/browse.html', 
                           pagination=pagination,
                           results=results, 
                           sectors=sectors, 
                           categories=categories,
                           current_sector=sector_id,
                           current_category=category_id,
                           current_type=file_type,
                           current_per_page=per_page,
                           q=q)

@documents.route('/view/<int:doc_id>')
def view_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    
    # Log access
    from flask_login import current_user
    access = AccessLog(document_id=doc.id, user_id=current_user.id if current_user.is_authenticated else None)
    db.session.add(access)
    db.session.commit()
    
    return render_template('documents/view.html', doc=doc)

@documents.route('/raw/<int:doc_id>')
def serve_file(doc_id):
    doc = Document.query.get_or_404(doc_id)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], doc.filename)

@documents.route('/thumbnail/<int:doc_id>')
def serve_thumbnail(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if not doc.thumbnail:
        return redirect(url_for('static', filename='img/generic-icon.png'))
    
    # If thumbnail is a path relative to UPLOAD_FOLDER
    if doc.thumbnail.startswith('thumbnails/'):
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], doc.thumbnail)
    
    # Fallback to a static icon if it's just a string like 'icons/pdf.png'
    # The path in DB is 'icons/pdf.png', but they are in static/img/icons/pdf.png
    return redirect(url_for('static', filename='img/' + doc.thumbnail))
