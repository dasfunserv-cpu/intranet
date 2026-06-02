from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User
from app import db
from app.utils import log_audit

auth = Blueprint('auth', __name__)

@auth.before_app_request
def enforce_password_change():
    if current_user.is_authenticated and current_user.must_change_password:
        if request.endpoint and request.endpoint not in ('auth.change_password', 'auth.logout', 'static'):
            flash('Por segurança, redefina sua senha provisória antes de continuar.', 'warning')
            return redirect(url_for('auth.change_password'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('documents.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            remember = True if request.form.get('remember') else False
            if not user.is_active:
                flash('Sua conta está desativada. Entre em contato com o administrador.', 'danger')
                return redirect(url_for('auth.login'))
                
            login_user(user, remember=remember)
            log_audit('login', 'user', user.id, f'Usuário {user.username} entrou no sistema.')
            next_page = request.args.get('next')
            flash(f'Bem-vindo de volta, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('documents.index'))
        else:
            flash('Login inválido. Verifique seu usuário e senha.', 'danger')
            
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    username = current_user.username if current_user.is_authenticated else 'Desconhecido'
    user_id = current_user.id if current_user.is_authenticated else None
    logout_user()
    log_audit('logout', 'user', user_id, f'Usuário {username} saiu do sistema.')
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or not confirm_password:
            flash('Por favor, preencha todos os campos.', 'warning')
        elif new_password != confirm_password:
            flash('As senhas digitadas não coincidem.', 'danger')
        elif len(new_password) < 6:
            flash('A nova senha deve ter no mínimo 6 caracteres.', 'danger')
        else:
            current_user.set_password(new_password)
            current_user.must_change_password = False
            db.session.commit()
            log_audit('edit', 'user', current_user.id, 'Redefiniu a senha obrigatória no primeiro acesso.')
            flash('Senha atualizada com sucesso! Seu acesso foi liberado.', 'success')
            return redirect(url_for('documents.index'))
            
    return render_template('auth/change_password.html')
