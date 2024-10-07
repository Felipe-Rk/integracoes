from bson import ObjectId
from app.db import db


class Rotinas(db.EmbeddedDocument):
    horario = db.StringField()
    tarefa = db.StringField()

class Rotina(db.Document):
    id = db.ObjectIdField(default=ObjectId, primary_key=True)
    usuario = db.ObjectIdField()
    data_registro = db.DateTimeField()
    rotina = db.ListField(db.EmbeddedDocumentField(Rotinas), required=False)
