import calendar
from datetime import date, datetime
from time import strftime
from flask import flash, jsonify, render_template, request
from flask_login import current_user, login_required
from app.ferramentas import ferramentas_bp
from app.ferramentas.routes.ponto import get_months
from app.models.rotina import Rotina, Rotinas
from app.services.rotinas import RotinasFunctions
from app.models.user import User

import locale


locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')


@ferramentas_bp.route('/rotina', methods=['GET']) #Rota para abrir a adição de um novo relatório apartir da page inicial 
@login_required
def rotina():
    dados = Rotina.objects()
    registros = []
    d = datetime.now()
    day = d.strftime('%d/%m/%Y')
    for n in dados:
        reg = n.data_registro
        data = reg.strftime('%d/%m/%Y')
        registros.append({
            'dia': day,
            'registro': data
            })
        
    return render_template('ferramentas/rotina.html', registros = registros)

@ferramentas_bp.route('/rotina_selecao') #Rota para page de consultas
@login_required
def rotina_selecao():
    dados = User.objects()
    users =[]
    for dado in dados:

        users.append({
            'id': str(dado.id),
            'nome': str(dado.nome)
        })
    
    months = get_months()

    return render_template('ferramentas/rotina_selecao.html', months = months, users = users)

@ferramentas_bp.route('/rotina_relatorio', methods=['GET','POST'])
@login_required
def rotina_relatorio():

    rotina_salva = Rotina.objects()#Instancia de registros Banco de dados
    rotina = []
    resultado = []     

    if request.method: #extrai dados da consulta enviada

        user= request.args.get('user')
        user_id, user_nome = user.split('|')
        month = request.args.get('month')
        data = request.args.get('data')        
        print(f'linha 64 request:{data} ')
        for dados in rotina_salva: #extrai dados de relatorios do banco de dados
            id_rotina = str(dados.id)
            id_user = str(dados.usuario)
            registros = dados.data_registro
            data_reg = registros.strftime('%d/%m/%Y')
            print(f'linha 66 data = {data}')


            if data: # caso selecionado data na consulta do relatorio 
                partes = data.split('-')
                data_request = f'{partes[2]}/{partes[1]}/{partes[0]}'
                print(f' data_request: {data_request} data_req: {data_reg}')
                if data_request == data_reg: #Verifica se tem algum registro no banco com a data selecionada
                        print(f'linha 100 data request:{data_request} | registro: {data_reg}')
                        rotina.append({
                            'user_nome': user_nome,
                            'data': data_reg,   
                        })

                        if user_id == id_user:#Verifica se a data encontrada é do usuario selecionado
                    
                            for rot in dados.rotina:
                                horario = rot.horario
                                tarefa = rot.tarefa
                                rotina.append({
                                    'horario':horario,
                                    'tarefa':tarefa
                                    }) #adiciona ao dicionario para envio do relatorio

            else: # caso seja selecionado mes na consulta do relatorio
                mes_request = int(month.split('-')[1])

                ano_request = int(month.split('-')[0])  
                data_convertida = date(ano_request, mes_request, 1)
                ano_data = data_convertida.year
                mes_data = data_convertida.month
                num_dias = calendar.monthrange(mes_data,mes_data)[1]
                dia = 1
                for n in range(num_dias):#Verifica quantos dias tem no mes e acrecenta um dia a cada consulta ao banco 
                    
                    data_r= f'{dia}/{mes_data}/{ano_data}'
                    dia += 1
                    data_re = datetime.strptime(data_r,'%d/%m/%Y').date()
                    data_request = data_re.strftime('%d/%m/%Y')

                    if data_request == data_reg:# Verifica se o banco possui data igual a consulta
                        rotina.append({
                            'user_nome': user_nome,
                            'data': data_reg,   
                        })
                        if user_id == id_user: #verifica se o usuario possui registro na data encontrada
                            print(f'user id = {user_id} id_user= {id_user}')
                            for rot in dados.rotina:
                                horario = rot.horario
                                tarefa = rot.tarefa
                                print(f'linha 112 horario: {rot.horario}')
                                print(f'linha 113 tarefa:{rot.tarefa}')
                                rotina.append({
                                    'horario':horario,
                                    'tarefa':tarefa
                                    })

    if rotina: #Caso o dicionario contenha registros salvo, retorna os dados para a interface
        print(f'linha 142 resultado: {resultado} Rotina: {rotina}')
        return render_template('ferramentas/rotina_relatorio.html',resultado = resultado, rotinas = rotina)

    else:
        flash('O usuário não possui registro para esse mês!', 'error')
        return rotina_selecao() #se não tiver, informa que nao foi encontrando 

@login_required
@ferramentas_bp.route('rotina/form_atividades' , methods=['GET','POST']) #rota de analise precisar criar novo relatorio ou ataulizar existente
def analisar_rotina_relatorio(): 

    rotina_salva = RotinasFunctions.get_rotina() #Rotina salva no banco de dados 
    
    nova_rotina = RotinasFunctions.ler_rotina() #Rotina enviada por formulario atual 
    
    data_atual = nova_rotina[1]
    rotina_ext = nova_rotina[0]

    if rotina_salva:
        
        for salva in rotina_salva:
            id_salva = salva['id']
            data_salva = salva['registro']
            rotina = Rotina.objects(id=id_salva).first() 

            if data_salva == data_atual: #verifica se existe algum registro no servidor com a data igual ao form
                
                for serv in rotina.rotina:
                    horario_salvo = serv.horario
                    tarefa_salva = serv.tarefa
                    
                    if tarefa_salva == "": # Verifica se tem horarios vazios
                    
                        for rot in rotina_ext:
                            novo_horario = rot.horario
                            nova_tarefa = rot.tarefa
                                                                                                        
                            if novo_horario == horario_salvo and nova_tarefa != "": #caso o horario seja vazio e o novo horario esteja preenchido
                                print(f'novo horario: {novo_horario} nova targea: {nova_tarefa}')
                                serv.tarefa = nova_tarefa

                            rotina.save()
                            
                print('Tarefa atualizada com sucesso')
                # RotinasFunctions.salvar_nova_rotina() 
                return jsonify(f'Sucess:{True}, Formulario atualizado com sucesso')
        else:
            RotinasFunctions.salvar_nova_rotina() #Caso não encontre a data ou registro do usuario, ele cria um novo
            return jsonify(f'Sucess:{True}, Formulario criado com sucesso')
                         
                    
                    




