            

from datetime import date, datetime

from flask import flash, jsonify, request
from flask_login import current_user

from app.decorators import return_json_on_error
from app.models.rotina import Rotina, Rotinas

class RotinasFunctions:
    @classmethod
    @return_json_on_error
    def ler_rotina(cls): #Leitura extraida do formulario
        try:
            registros = request.get_json()
            rotina_salva=[]                                                                
            
            dia = registros[0]
            data = dia.get('dia')

            # rotina_salva.append(data)
            for registro in registros:

                horario = registro.get('hora')
                tarefa = registro.get('atividade')
                rotinas = Rotinas (
                    horario = horario,
                    tarefa = tarefa
                    )
                   
                rotina_salva.append(rotinas)
            # print(f'linha 34 rotina_salva: {type(rotina_salva)}')
          
            return rotina_salva,data                                                                                                                                                                                                                                                                                                                                                                                                                             
        except Exception as e:
                print('erro',{e})

    @classmethod
    @return_json_on_error
    def salvar_nova_rotina(cls):  #Caso não tenha dados é chamado para criar um novo registro
        try:
            rotinas = []
            data =  date.today()
            usuario = current_user.id
            rotina_salva=[]
            
            registros = request.get_json()
            
            for registro in registros:
                horario = registro.get('hora')
                tarefa = registro.get('atividade')
    
                rotinas= Rotinas(
                    horario = horario,
                    tarefa = tarefa
                )
                rotina_salva.append(rotinas)

            nova_rotina = Rotina (  #Instancia a classe para criação apartir do modelo definido
                usuario = usuario,
                data_registro = data,
                rotina = rotina_salva
            )
            nova_rotina.save() #Cria o novo registro no banco apartir do modelo 
            print('Nova rotina salva com sucesso')
            resposta_console = jsonify({'Sucess': True}), 200
            reposta_usuario = flash(f'Sucess:{True}, Formulario criado com sucesso')
            return resposta_console, reposta_usuario
        except Exception as e:
            resposta_console = jsonify({'success': False, 'message': str(e)}), 500
            reposta_usuario = flash(f'Sucess:{False}, Erro ao criar formulario. Tente novamente!')
            return resposta_console, reposta_usuario


    @classmethod
    @return_json_on_error
    def get_rotina(cls): #Faz a consulta no banco de dados
        
        rotina_salva = []
        rotina_data = Rotina.objects()
        
        for dados in rotina_data:
            data = dados.data_registro
            data_br = data.strftime('%d/%m/%Y')

            rotinas = dados.rotina
            
                
            rotina_salva.append({
                'id': str(dados.id),
                'usuario': str(dados.usuario),
                'registro': data_br,
                'rotinas' : rotinas
            })
        return rotina_salva #Retorna os dados extraidos para a rota fazer a analise