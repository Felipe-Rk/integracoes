from flask import Blueprint, Flask, request, jsonify
from flask_login import login_required
from app.decorators import return_json_on_error
from app.models.etiquetas import Etiquetas
from app.routes.api import api_bp
from app.services.tarefa import SubtarefaService

@api_bp.route('/etiquetas/criar', methods=['POST'])
@login_required
@return_json_on_error
def add_etiqueta():
    try:
        data = request.get_json()
        etiquetas = data.get('etiquetas', [])

        if not etiquetas:
            return jsonify({'success': False, 'message': 'Nenhuma etiqueta fornecida'}), 400

        for etiqueta in etiquetas:
            nome = etiqueta.get('nome')
            cor = etiqueta.get('cor')

            if not nome or not cor:
                continue

            etiqueta_existente = Etiquetas.objects(nome=nome).first()
            if not etiqueta_existente:
                nova_etiqueta = Etiquetas(nome=nome, cor=cor)
                nova_etiqueta.save()

        return jsonify({'success': True, 'message': 'Etiquetas salvas com sucesso'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/etiquetas/consultar', methods=['GET'])
@login_required
@return_json_on_error
def get_etiquetas_route():
    try:
        etiquetas = SubtarefaService.get_etiquetas()
        print('etiquetas', etiquetas)
        for etiqueta in etiquetas:
            print(f"ID: {etiqueta['id']}, Nome: {etiqueta['nome']}, Cor: {etiqueta['cor']}")
        return jsonify({"success": True, "etiquetas": etiquetas})
    except Exception as e:
        print(f"Erro ao consultar etiquetas: {e}")
        return jsonify({"success": False, "message": str(e)})
