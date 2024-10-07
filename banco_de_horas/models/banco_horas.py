# hours.py

from app.db import db

class BancoHoras(db.Document):
    # Seus campos aqui
    meta = {
        'collection': 'banco_horas'
    }
