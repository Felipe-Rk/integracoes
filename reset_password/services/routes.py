from datetime import datetime, timedelta
import random
import string
import logging
from app.services.chat import MensagemService
from app.services.folder_service import Folder_service
from deepface import DeepFace
import os
from flask import app, jsonify, render_template, redirect, session, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
import mongoengine

from app import db
from . import auth_bp
from ..models.user import User
import concurrent.futures
from ..cache import cache
from app.services.image_service import Image_service
from app.services.face_validator_service import Face_service
from app.services.validator_service import Validator_service
from app.services.crypto_service import Crypto_service
import threading

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits  # Apenas letras e números
    random_password = ''.join(random.choice(characters) for i in range(length))
    return random_password

@auth_bp.route('/recuperar_senha', methods=['GET', 'POST'])
def recuperar_senha():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.objects(email=email).first()
        if user:
            new_password = generate_random_password()
            user.set_password(new_password, temporary=True)  # Definir a senha como temporária
            user.save()
            print(f"Nova senha gerada para o usuário {user.email}: {new_password}")
            logging.info(f"Nova senha gerada para o usuário {user.email}: {new_password}")
            flash('Uma nova senha temporária foi gerada! Contate o administrador para validar a senha.', 'info')
            remetente = '6644e34411af901b0d8e8eab'
            destinatario = '65f07ac2dc05bb5efba7efc2'

            if remetente and destinatario:
                try:
                    mensagem = f'Senha temporária gerada para o usuário: {user.email}\n senha temporária: {new_password}'
                    try:
                        MensagemService.postar_mensagem(
                            texto_mensagem = mensagem,
                            id_destinatario = destinatario,
                            id_remetente = remetente
                        )
                        logging.info(f'Mensagem enviada para o responsavel sobre a recuperação de senha')
                    except Exception as e:
                        logging.error(f'Erro ao enviar mensagem de recuperação de senha: {str(e)}') 
                        # flash('Erro ao enviar mensagem de recuperação de senha', 'danger')
                except AttributeError as e:
                    # Tratar especificamente o erro de usuário anônimo
                    if "'AnonymousUserMixin' object has no attribute 'id'" in str(e):
                        logging.warning('A operação tentou acessar o ID de um usuário anônimo.')
                    else:
                        logging.error(f'Erro inesperado ao tentar enviar mensagem: {str(e)}')
                        # flash('Erro inesperado ao tentar enviar mensagem', 'danger')
            else:
                logging.error(f'Usuário remetente ou destinatário não encontrado')
                # flash('Erro ao enviar a mensagem de recuperação de senha.', 'danger')   
            return redirect(url_for('auth.login'))
        # else:
        #     # flash('Email não encontrado.', 'danger')
    return render_template('auth/recuperar_senha.html')


@auth_bp.route('/change_password', methods=['POST'])
@login_required  # Certifique-se de importar e aplicar o decorador de autenticação
def change_password():
    if request.method == 'POST':
        data = request.get_json()
        novo_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if novo_password != confirm_password:
            return jsonify({'success': False, 'message': 'As senhas não coincidem.'}), 400

        if current_user.is_authenticated:  # Verifica se o usuário está autenticado
            current_user.set_password(novo_password)
            current_user.temporary_password = False 
            current_user.save()
            return jsonify({'success': True, 'message': 'Senha alterada com sucesso.'}), 200
        else:
            return jsonify({'success': False, 'message': 'Usuário não autenticado.'}), 401
    

@auth_bp.route('/reset_temporary_password', methods=['POST'])
def reset_temporary_password():
    if request.method == 'POST':
        data = request.get_json()
        temp_password = data.get('temp_password')
        new_password = data.get('new_password')

        user = User.objects(temporary_password=True).first()
        if user and user.check_password(temp_password):
            # Marcar a nova senha como definitiva
            user.set_password(new_password)
            # Alterar o status da senha temporária
            user.temporary_password = False
            user.save()
            return jsonify({'success': True, 'message': 'Senha redefinida com sucesso.'}), 200
        else:
            return jsonify({'success': False, 'message': 'Senha temporária inválida ou expirada.'}), 400
          
@auth_bp.route('/reset_temporary_password_page', methods=['GET'])
def reset_temporary_password_page():
    return render_template('auth/reset_temporary_password.html')   

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Se o usuário estiver autenticado, redirecione-o para a página principal
    if current_user.is_authenticated:
        if current_user.temporary_password:
            # Se a senha for temporária, redirecione para a página de redefinição de senha temporária
            flash('Por favor, altere sua senha temporária.', 'warning')
            return redirect(url_for('auth.reset_temporary_password_page'))
        else:
            # Se a senha for definitiva, redirecione para a página principal
            return redirect(url_for('main.index'))

    if request.method == 'POST':
        user = User.objects(email=request.form.get('email')).first()
        if user and user.check_password(request.form.get('password')) and user.active:
            login_user(user, remember=True)
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=365)
            if user.temporary_password:
                # Se a senha for temporária, redirecione para a página de redefinição de senha temporária
                flash('Por favor, altere sua senha temporária.', 'warning')
                return redirect(url_for('auth.reset_temporary_password_page'))
            else:
                # Se a senha for definitiva, redirecione para a página principal
                return redirect(url_for('main.index'))
        flash('Email ou senha inválidos ou usuário desativado.', 'danger')
    return render_template('auth/login.html')

