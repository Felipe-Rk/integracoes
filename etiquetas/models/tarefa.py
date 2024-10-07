from datetime import datetime
from app.db import db
from app.models.etiquetas import Etiquetas
from app.models.observacao import Observacao
from app.models.registro import Registro
from bson import ObjectId


class Etiqueta(db.EmbeddedDocument): #comentar um excluir a classe antiga de etiquetas.
    nome = db.StringField()
    cor = db.StringField()

class Coluna(db.EmbeddedDocument):
    nome = db.StringField(required=True)
    cor = db.StringField(required=True)

class SubTarefa(db.EmbeddedDocument):
    id = db.ObjectIdField(default=ObjectId)
    responsaveis = db.ListField(db.ReferenceField('User'))
    titulo = db.StringField(required=True)
    arquivos = db.ListField(db.EmbeddedDocumentField('Arquivo'), required=False, default=[])
    arquivos = db.ListField(db.StringField())
    criado_por = db.ReferenceField('User')
    criado_em = db.DateTimeField(default=datetime.utcnow)
    iniciado_em = db.DateTimeField(default=None)
    concluido_em = db.DateTimeField(default=None)
    status = db.StringField()
    dias_estimados = db.IntField()
    horas_estimadas = db.IntField()
    minutos_estimados = db.IntField()
    etiqueta = db.ListField(db.ReferenceField(Etiquetas)) #nova rota etiquetar por ID
    etiquetas = db.ListField(db.EmbeddedDocumentField(Etiqueta)) #modelo antigo - apagar após migrar. 
    observacoes = db.ListField(db.ReferenceField(Observacao))
    imagem = db.StringField(max_length=255)
    registro = db.ListField(db.ReferenceField(Registro))

class Tarefa(db.Document):
    responsaveis = db.ListField(db.ReferenceField('User'))
    nome = db.StringField(required=True)
    descricao = db.StringField()
    status = db.StringField()
    arquivos = db.ListField(db.StringField())
    observacoes = db.ListField(db.ReferenceField(Observacao))
    registro = db.ListField(db.ReferenceField(Registro))
    criado_por = db.ReferenceField('User')
    criado_em = db.DateTimeField(default=datetime.utcnow)
    inicado_em = db.DateTimeField()
    estimativa_conclusao = db.DateTimeField()
    conluido_em = db.DateTimeField()
    mes = db.StringField()
    ano = db.StringField()
    subtarefas = db.ListField(db.EmbeddedDocumentField(SubTarefa), required=False)
    excluido = db.BooleanField(default=False)
    ultima_alteracao_status = db.DateTimeField(default=None)
    horas_estimadas = db.IntField()
    minutos_estimados = db.IntField()
    colunas = db.ListField(db.EmbeddedDocumentField(Coluna), default = [])