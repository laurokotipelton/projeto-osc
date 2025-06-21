import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave_secreta_segura'
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/ordens_servico')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://osc:masterkey@localhost/osc'
    SQLALCHEMY_TRACK_MODIFICATIONS = False