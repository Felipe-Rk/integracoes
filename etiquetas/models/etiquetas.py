from app.db import db
from bson import ObjectId

class Etiquetas(db.Document):
    id = db.ObjectIdField(default=ObjectId, primary_key=True)
    nome = db.StringField(required=True)
    cor = db.StringField(required=True)
