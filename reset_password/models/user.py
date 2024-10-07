from datetime import datetime
from app.db import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user



class User(UserMixin, db.Document):
    email = db.EmailField(unique=True, required=True)
    password_hash = db.StringField(required=True)
    temporary_password = db.BooleanField(default=False)
    roles = db.ListField(db.ReferenceField(Role), default=[])
    nome = db.StringField(max_length=255)
    data_nascimento = db.DateTimeField()
    data_admissao = db.DateTimeField()
    data_final = db.DateTimeField()
    data_registro = db.DateTimeField(default=datetime.utcnow)
    data_termino = db.DateTimeField()
    horario_entrada = db.StringField(max_length=8)
    horario_almoco = db.StringField(max_length=8)
    horario_retorno = db.StringField(max_length=8)
    horario_saida = db.StringField(max_length=8)
    comeco_semana_trabalho = db.IntField()
    fim_semana_trabalho = db.IntField()
    user_id_extensao = db.StringField(max_length=255)
    active = db.BooleanField(default=True, required=False)

    def set_password(self, password, temporary=True):
        self.password_hash = generate_password_hash(password)
        self.temporary_password = temporary
        self.save()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def checkIfHasImage(self):
        return bool(self.imagemReconhecimentoFacial)

    @classmethod
    def get_users(cls):
        return cls.objects.all()
    
    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)
    
    def is_admin(self):
        return self.has_role('adm')
