from typing import Union

from flask import jsonify
from app.models.etiquetas import Etiquetas
from app.models.tarefa import Coluna, Tarefa
from bson.objectid import ObjectId

class SubtarefaService:

    @staticmethod
    def converter_etiquetas(etiqueta_ids):
        etiquetas = []
        for etiqueta_id in etiqueta_ids:
            etiqueta = Etiquetas.objects(id=ObjectId(etiqueta_id)).first()
            if etiqueta:
                etiquetas.append({
                    'id': str(etiqueta.id),
                    'nome': etiqueta.nome,
                    'cor': etiqueta.cor
                })
        return etiquetas
        
    
    @staticmethod
    def get_etiquetas():
        etiquetas = Etiquetas.objects()
        etiquetas_serializadas = []
        for etiqueta in etiquetas:
            print(f"Etiqueta ID: {etiqueta.id}, Nome: {etiqueta.nome}, Cor: {etiqueta.cor}")  # Debug
            etiquetas_serializadas.append({
                'id': str(etiqueta.id),  # Converte ObjectId para string
                'nome': etiqueta.nome,
                'cor': etiqueta.cor
            })
        return etiquetas_serializadas
        