from datetime import datetime, timedelta
import os
from flask import current_app, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_login import login_required, current_user
from bson.objectid import ObjectId
import pytz
import requests
from app.create_thumbnail import create_document_thumbnail
from app.decorators import requires_permission
from bson import DBRef
from app.functions.datetime import calculate_time_elapsed, datetime_local_parse, format_date_from_br_full_timezone, format_date_from_br_short, get_current_date, timezone
from app.extensions import socketio
from app.models.etiquetas import Etiquetas
from app.services.tarefa import SubtarefaService
from .. import ferramentas_bp
from ...models.registro import Registro
from ...models.observacao import Observacao
from ...models.tarefa import SubTarefa, Tarefa
from ...models.user import User
from app.services.user import UserService
from mongoengine import Q
from unidecode import unidecode
from app.functions import tarefas as tarefas_functions

@ferramentas_bp.route('/tarefas')
# Adicionando um parâmetro opcional para o ano na rota
@ferramentas_bp.route('/tarefas/<int:ano>')
@ferramentas_bp.route('/tarefas/<int:ano>/<int:mes_arg>')
@login_required
@requires_permission('tarefas')
def tarefas(ano=None, mes_arg=None): 
    tarefa_id = request.args.get('tarefa_id', '')
    user_permissions = [role.name for role in current_user.roles]
    status_search = request.args.get('status', '')
    data_search = request.args.get('data_search', '')
    responsavel_search = request.args.get('responsavel', '')
    excluidos_search = request.args.get('excluidos', '') == 'true'

    modo_data = request.args.get('data')

    meses = [ ('Janeiro', 'jan'), ('Fevereiro', 'fev'), ('Março',
        'mar'), ('Abril', 'abr'), ('Maio', 'mai'), ('Junho', 'jun'), ('Julho',
        'jul'), ('Agosto', 'ago'), ('Setembro', 'set'), ('Outubro', 'out'),
        ('Novembro', 'nov'), ('Dezembro', 'dez') ]
    
    current_date = get_current_date()

    if ano is None:
        ano = str(current_date.year)
    else:
        ano = str(ano) 

    if mes_arg is None:
        mes_arg = current_date.month
    mes_str = meses[mes_arg-1][1]


    if tarefa_id != '':
        if 'adm' in user_permissions:
            tarefas = Tarefa.objects.filter(id=tarefa_id)
        else:
            tarefas = Tarefa.objects.filter(responsaveis=current_user, id=tarefa_id)
    else:

        if 'adm' in user_permissions:
            tarefas = Tarefa.objects.filter(ano=ano, mes=mes_str)
        else:
            # Comentado para não da erro caso o usuário não seja admin nem responsável
            # responsaveis_ids = [user.id for sublist in [tarefa.responsaveis for tarefa in Tarefa.objects.filter(ano=ano, mes=mes_str)] for user in sublist]
            # if current_user.id in responsaveis_ids:
            tarefas = Tarefa.objects.filter(responsaveis=current_user, ano=ano, mes=mes_str).all()

        if excluidos_search:
            tarefas = tarefas.filter(excluido=True)
        else:
            tarefas = tarefas.filter(Q(excluido=False) | Q(excluido__exists=False))

        data_atual = datetime.now().date()
        ontem = data_atual + timedelta(days=-1)
        if modo_data == 'hoje':

            tarefas = tarefas.filter(estimativa_conclusao__gte=data_atual, estimativa_conclusao__lt=data_atual + timedelta(days=1))
        elif modo_data == 'ontem':
            tarefas = tarefas.filter(estimativa_conclusao__gte=ontem, estimativa_conclusao__lt=ontem + timedelta(days=1))
        elif modo_data == 'outras':
            tarefas = tarefas.filter(
                Q(estimativa_conclusao__gte=data_atual) | Q(estimativa_conclusao__lt=ontem) | Q(estimativa_conclusao__exists=False)
            )

        if status_search:
            tarefas = tarefas.filter(status=status_search)
        if data_search:
            try:
                ultimo_registro_date = datetime.strptime(data_search, '%Y-%m-%d')
                tarefas = tarefas.filter(
                    estimativa_conclusao__gte=ultimo_registro_date, 
                    estimativa_conclusao__lt=ultimo_registro_date + timedelta(days=1))
            except ValueError:
                flash('Data inválida.', 'error')
                return redirect(url_for('ferramentas_bp.tarefas'))
        if responsavel_search:
            responsavel_id = ObjectId(responsavel_search)
            tarefas = tarefas.filter(responsaveis=responsavel_id)

    tarefas = tarefas.all()

    tarefas_por_dia = {0: []}

    status_ordenacao = [
        'em andamento',
        'criado',
        'concluido'
    ]

    tarefas_status = {'total': 0, 'criado': 0, 'em-andamento': 0, 'concluido': 0, 'parado': 0}

    for tarefa in tarefas:
        if tarefa.ultima_alteracao_status:
            dia = tarefa.ultima_alteracao_status.day
        elif tarefa.estimativa_conclusao:
            dia = tarefa.estimativa_conclusao.day
        else:
            dia = 0

        if tarefa.criado_por:
            tarefa.usuario_criador_imagem = tarefa['criado_por'].imagem
        else:
            tarefa.usuario_criador_imagem = None
        # tarefas_por_ano[tarefa.mes].append(tarefa)
        if dia not in tarefas_por_dia:
            tarefas_por_dia[dia] = []
        tarefas_por_dia[dia].append(tarefa)
        status_taf = unidecode(tarefa.status.lower()).replace(' ', '-')
        if status_taf not in tarefas_status:
            tarefas_status[status_taf] = 0
        tarefas_status[status_taf] += 1
        tarefas_status['total'] += 1
        tarefa.criado_em = format_date_from_br_short(tarefa.criado_em)

    # for mes in tarefas_por_ano.keys():
    #     tarefas_por_ano[mes].sort(key=lambda t: status_ordenacao.index(t.status.lower()) if t.status.lower() in status_ordenacao else len(status_ordenacao))
    for dia in tarefas_por_dia.keys():
        tarefas_por_dia[dia].sort(key=lambda t: status_ordenacao.index(t.status.lower()) if t.status.lower() in status_ordenacao else len(status_ordenacao))

    tarefas_por_dia = dict(sorted(tarefas_por_dia.items(), reverse=True))

    for dia in tarefas_por_dia.keys():
        tarefas_por_dia[dia].reverse()

    return render_template('ferramentas/tarefas.html',
                        #    tarefas_por_ano=tarefas_por_ano,
                           tarefas_por_dia=tarefas_por_dia,
                           tarefas_status=tarefas_status,
                           anoVerificado=str(ano),
                           mes=mes_arg,
                           meses=meses,
                           ano=int(ano),
                           format_date_from_br_full_timezone=format_date_from_br_full_timezone,
                           lixeira=excluidos_search,
                           user_permissions=user_permissions
                           )

@ferramentas_bp.route('/tarefas/subtarefas/<tarefa_id>', methods=['GET'])
@login_required
@requires_permission('tarefas')
def get_subtarefas(tarefa_id):
    tarefa = Tarefa.objects(id=tarefa_id).first_or_404()
    user_permissions = [role.name for role in current_user.roles]
    
    subtarefas = []

    for subtarefa in tarefa.subtarefas:
        # Filtrar subtarefas para usuários não administradores
        if 'adm' not in user_permissions:
            if not any(current_user.id == responsavel.id for responsavel in subtarefa.responsaveis):
                continue

        subtarefa_data = subtarefa.to_mongo().to_dict()
        
        # Converte ObjectId para string
        subtarefa_data['id'] = str(subtarefa_data['id'])
        subtarefa_data['responsaveis'] = [str(responsavel) for responsavel in subtarefa_data['responsaveis']]
        subtarefa_data['registro'] = [str(registro) for registro in subtarefa_data['registro']]

        # Converte o documento Observacao para um dicionário
        if subtarefa.criado_por:
            subtarefa_data['criado_por'] = subtarefa['criado_por'].nome
            # subtarefa_data['usuario_criador_imagem'] = subtarefa['criado_por'].imagem
            subtarefa_data['criado_por_usuario_atual'] = subtarefa.criado_por.id == current_user.id
        else:
            subtarefa_data['criado_por'] = "Usuário Excluído"
            subtarefa_data['usuario_criador_imagem'] = None

        if subtarefa.imagem:
            subtarefa_data['subtarefa_imagem'] = subtarefa['imagem']
        else:
            if subtarefa.criado_por:
                subtarefa_data['subtarefa_imagem'] = subtarefa['criado_por'].imagem
            else:
                subtarefa_data['subtarefa_imagem'] = None

        # Buscar o documento User associado e incluir o nome do usuário
        if subtarefa.criado_por:
            if subtarefa.criado_por.id == current_user.id:
                subtarefa_data['criado_por'] = 'Você'
            else:
                usuario = User.objects(id=subtarefa.criado_por.id).first()
                subtarefa_data['criado_por'] = usuario.nome if usuario else 'Usuário desconhecido'

        if 'criado_em' in subtarefa_data:
            subtarefa_data['criado_em'] = subtarefa_data['criado_em'].strftime(
                '%Y-%m-%d %H:%M:%S')
            
        if 'observacoes' in subtarefa_data:
            subtarefa_data['observacoes'] = [{'id': str(obs.id)} for obs in subtarefa.observacoes]

        # Processar etiquetas usando a função auxiliar
        subtarefa_data['etiqueta'] = SubtarefaService.converter_etiquetas(subtarefa_data['etiqueta'])

        subtarefas.append(subtarefa_data)

    return jsonify({"success": True, "subtarefas": subtarefas, "colunas": tarefa.colunas})

@ferramentas_bp.route('/tarefa/subtarefas/<status>/<tarefa_id>', methods=['GET'])
@login_required
@requires_permission('tarefas')
def get_subtarefa_status(tarefa_id, status):
    tarefa = Tarefa.objects(id=tarefa_id).first_or_404()
    status = status

    subtarefas = []

    try: 
        if tarefa:

            for subtarefa in tarefa.subtarefas:

                if subtarefa.status == status:

                    subtarefa_data = subtarefa.to_mongo().to_dict()

                    # Converte o documento Observacao para um dicionário
                    if subtarefa.criado_por:
                        subtarefa_data['criado_por'] = subtarefa['criado_por'].nome
                        subtarefa_data['criado_por_usuario_atual'] = subtarefa.criado_por.id == current_user.id
                    else:
                        subtarefa_data['criado_por'] = "Usuário Excluído"
                        subtarefa_data['usuario_criador_imagem'] = None

                    if subtarefa.imagem:
                        subtarefa_data['subtarefa_imagem'] = subtarefa['imagem']
                    else:
                        if subtarefa.criado_por:
                            subtarefa_data['subtarefa_imagem'] = subtarefa['criado_por'].imagem
                        else:
                            subtarefa_data['subtarefa_imagem'] = None
                    # Converte ObjectId para string
                    subtarefa_data['id'] = str(subtarefa_data['id'])
                    subtarefa_data['responsaveis'] = [
                        str(responsavel) for responsavel in subtarefa_data['responsaveis']]
                    subtarefa_data['registro'] = [
                        str(registro) for registro in subtarefa_data['registro']]
                    if 'criado_em' in subtarefa_data:
                        subtarefa_data['criado_em'] = subtarefa_data['criado_em'].strftime(
                            '%Y-%m-%d %H:%M:%S')
                    if 'observacoes' in subtarefa_data:
                        subtarefa_data['observacoes'] = [{'id': str(obs.id)} for obs in subtarefa.observacoes]

                    if subtarefa_data != None:
                        subtarefas.append(subtarefa_data)

                    # Processar etiquetas usando a função auxiliar
                    subtarefa_data['etiqueta'] = SubtarefaService.converter_etiquetas(subtarefa_data['etiqueta'])

            
            return jsonify({"success": True, "subtarefas": subtarefas, "message": "subtarefa encontrada"})
        else:
            return jsonify({"success": False, "message": "subtarefa não encontrada"})

    except Exception as e:
        return jsonify({"success": False, "message": f"Ocorreu um erro: {str(e)}"}), 500




@ferramentas_bp.route('/tarefa/subtarefa/<tarefa_id>/<subtarefa_id>', methods=['GET'])
@login_required
@requires_permission('tarefas')
def get_subtarefa(tarefa_id, subtarefa_id):
    
    tarefa = Tarefa.objects(id=tarefa_id).first_or_404()

    subtarefa_data = None
    try: 
        if tarefa:
            for subtarefa in tarefa.subtarefas:
                if str(subtarefa.id) == subtarefa_id:

                    subtarefa_data = subtarefa.to_mongo().to_dict()

                    # Converte o documento Observacao para um dicionário
                    if subtarefa.criado_por:
                        subtarefa_data['criado_por'] = subtarefa['criado_por'].nome
                        subtarefa_data['criado_por_usuario_atual'] = subtarefa.criado_por.id == current_user.id
                    else:
                        subtarefa_data['criado_por'] = "Usuário Excluído"
                        subtarefa_data['usuario_criador_imagem'] = None

                    if subtarefa.imagem:
                        subtarefa_data['subtarefa_imagem'] = subtarefa['imagem']
                    else:
                        if subtarefa.criado_por:
                            subtarefa_data['subtarefa_imagem'] = subtarefa['criado_por'].imagem
                        else:
                            subtarefa_data['subtarefa_imagem'] = None
                    # Converte ObjectId para string
                    subtarefa_data['id'] = str(subtarefa_data['id'])
                    subtarefa_data['responsaveis'] = [
                        str(responsavel) for responsavel in subtarefa_data['responsaveis']]
                    subtarefa_data['registro'] = [
                        str(registro) for registro in subtarefa_data['registro']]
                    if 'criado_em' in subtarefa_data:
                        subtarefa_data['criado_em'] = subtarefa_data['criado_em'].strftime(
                            '%Y-%m-%d %H:%M:%S')
                    if 'observacoes' in subtarefa_data:
                        subtarefa_data['observacoes'] = [{'id': str(obs.id)} for obs in subtarefa.observacoes]
                    
                    # Processar etiquetas usando a função auxiliar
                    subtarefa_data['etiqueta'] = SubtarefaService.converter_etiquetas(subtarefa_data['etiqueta'])

        if subtarefa_data != None:
            #print(subtarefa_data)
            return jsonify({"success": True, "subtarefa": subtarefa_data, "message": "subtarefa encontrada"})
        else:
            return jsonify({"success": False, "message": "subtarefa não encontrada"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Ocorreu um erro: {str(e)}"}), 500

@ferramentas_bp.route('tarefas/subtarefas/etiquetas/buscar/<tarefa_id>/<subtarefa_id>', methods=['GET'])
@login_required
@requires_permission('tarefas')
def tarefas_subtarefas_etiquetas_buscar(tarefa_id, subtarefa_id):
    try:
        # Obter a tarefa pelo ID
        tarefa = Tarefa.objects.get(id=ObjectId(tarefa_id))
        
        # Encontrar a subtarefa dentro da tarefa
        subtarefa = next((st for st in tarefa.subtarefas if str(st.id) == subtarefa_id), None)
        if not subtarefa:
            return jsonify(success=False, message="Subtarefa não encontrada."), 404

        # Serializar as etiquetas da subtarefa
        etiquetas_data = [{"id": str(etiqueta.id), "nome": etiqueta.nome, "cor": etiqueta.cor} for etiqueta in subtarefa.etiqueta]

        return jsonify(success=True, etiquetas=etiquetas_data), 200
    except Exception as e:
        print(f"Erro ao buscar etiquetas da subtarefa: {e}")
        return jsonify(success=False, message=str(e)), 500
    
@ferramentas_bp.route('tarefas/subtarefas/etiquetas/adicionar/<tarefa_id>/<subtarefa_id>', methods=['POST'])
@login_required
@requires_permission('tarefas')
def tarefas_subtarefas_etiquetas_adicionar(tarefa_id, subtarefa_id):
    try:
        # Obter dados da requisição
        data = request.get_json()
        etiquetas = data.get('etiquetas', [])

        if not etiquetas:
            return jsonify(success=False, message="Nenhuma etiqueta fornecida."), 400

        # Encontrar a tarefa no banco de dados
        tarefa = Tarefa.objects.get(id=ObjectId(tarefa_id))
        
        # Encontrar a subtarefa dentro da tarefa
        subtarefa = next((st for st in tarefa.subtarefas if str(st.id) == subtarefa_id), None)
        if not subtarefa:
            return jsonify(success=False, message="Subtarefa não encontrada."), 404

        # Limpar etiquetas antigas
        subtarefa.etiqueta.clear()

        # Adicionar novas etiquetas
        for etiqueta_data in etiquetas:
            etiqueta_id = etiqueta_data.get('id')
            if etiqueta_id:
                try:
                    etiqueta = Etiquetas.objects.get(id=ObjectId(etiqueta_id))
                    subtarefa.etiqueta.append(etiqueta)
                except Exception as e:
                    print(f"Erro ao buscar etiqueta com id {etiqueta_id}: {e}")
                    continue

        # Salvar as mudanças
        tarefa.save()

        return jsonify(success=True, message="Etiquetas adicionadas com sucesso."), 200
    except Exception as e:
        print(f"Erro ao adicionar etiquetas: {e}")
        return jsonify(success=False, message=str(e)), 500

@ferramentas_bp.route('tarefas/subtarefas/etiquetas/remover/<tarefa_id>/<subtarefa_id>', methods=['POST'])
@login_required
@requires_permission('tarefas')
def tarefas_subtarefas_etiquetas_remover(tarefa_id, subtarefa_id):
    try:
        tarefa = Tarefa.objects(id=tarefa_id).first_or_404()

        subtarefa = None
        for st in tarefa.subtarefas:
            if str(st.id) == subtarefa_id:
                subtarefa = st
                break

        if subtarefa is None:
            return jsonify({"success": False, "message": "Subtarefa não encontrada."}), 404

        data = request.json
        etiquetas_a_remover = data.get('etiquetas', [])
        print(etiquetas_a_remover)
        if not isinstance(etiquetas_a_remover, list):
            return jsonify({"success": False, "message": "Etiquetas devem ser fornecidas em uma lista."}), 400

        def etiqueta_igual(e1, e2):
            return e1['nome'] == e2['nome'] and e1['cor'] == e2['cor']

        subtarefa.etiqueta = [etiqueta for etiqueta in subtarefa.etiqueta if not any(etiqueta_igual(etiqueta, e) for e in etiquetas_a_remover)]
        
        tarefa.save()
        return jsonify({"success": True, "message": "Etiquetas removidas com sucesso."}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Ocorreu um erro: {str(e)}"}), 500
#--------------------------------------------------------------------------------------------------------
#Função temporaria para conversão dos modelos de etiquetas e atualização das subtarefas ja existentes
@ferramentas_bp.route('tarefas/subtarefas/atualizar-subtarefas', methods=['GET'])
def atualizar_subtarefas():
    try:
        # Recuperar todas as tarefas
        tarefas = Tarefa.objects()

        # Iterar sobre cada tarefa
        for tarefa in tarefas:
            # Iterar sobre cada subtarefa dentro da tarefa
            for subtarefa in tarefa.subtarefas:
                # Inicializar o mapeamento de etiquetas antigas
                etiquetas_map = {}
                novas_etiquetas_refs = []

                # Preencher o mapeamento com etiquetas antigas
                for etiqueta_antiga in subtarefa.etiquetas:
                    etiquetas_map[(etiqueta_antiga.nome, etiqueta_antiga.cor)] = etiqueta_antiga

                # Iterar sobre cada etiqueta antiga no mapeamento
                for (nome, cor), etiqueta_antiga in etiquetas_map.items():
                    # Encontrar a etiqueta nova correspondente
                    etiqueta_nova = Etiquetas.objects(nome=nome, cor=cor).first()

                    if not etiqueta_nova:
                        # Se não encontrar, adicionar a nova etiqueta ao banco de dados
                        etiqueta_nova = Etiquetas(nome=nome, cor=cor)
                        etiqueta_nova.save()
                        
                    if etiqueta_nova and etiqueta_nova.id:
                        # Adicionar a referência da nova etiqueta na lista de novas etiquetas
                        novas_etiquetas_refs.append(etiqueta_nova.id)
                        print(f'ID adicionado: {etiqueta_nova.id}')
                    else:
                        print('Erro: ID da etiqueta nova é None', etiqueta_nova)

                subtarefa.etiqueta = novas_etiquetas_refs
                # print('linha 1956 subtarefa após atualização:', subtarefa.to_json())

                subtarefa.etiquetas = []  # Limpar as etiquetas antigas

                # Salvar a tarefa para persistir as mudanças na subtarefa
                tarefa.save()


        return jsonify({"message": "Atualização das subtarefas concluída"}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
