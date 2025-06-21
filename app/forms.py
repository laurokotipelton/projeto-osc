from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DecimalField, DateField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, ValidationError

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class ClienteForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    telefone = StringField('Telefone')
    email = StringField('Email')
    endereco = StringField('Endereço')
    observacoes = TextAreaField('Observações')
    submit = SubmitField('Salvar')

class OrdemServicoForm(FlaskForm):
    titulo = StringField('Título', validators=[DataRequired()])
    descricao = TextAreaField('Descrição')
    status = SelectField('Status', choices=[('Aguardando', 'Aguardando'), ('Em andamento', 'Em andamento'), ('Finalizado', 'Finalizado')])
    data_conclusao = DateField('Data de Conclusão', format='%Y-%m-%d', validators=[], render_kw={"placeholder": "YYYY-MM-DD"})
    valor = DecimalField('Valor (R$)', places=2)
    observacoes = TextAreaField('Observações')
    cliente_id = SelectField('Cliente', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Salvar')

class ProdutoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    descricao = TextAreaField('Descrição')
    quantidade = IntegerField('Quantidade', validators=[DataRequired()])
    unidade = StringField('Unidade', default='un')
    categoria = StringField('Categoria')
    preco = DecimalField('Preço', places=2)
    submit = SubmitField('Salvar')

class MovimentacaoForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[
        ('Entrada', 'Entrada'),
        ('Saída', 'Saída'),
        ('Ajuste', 'Ajuste')
    ], validators=[DataRequired()])
    quantidade = IntegerField('Quantidade', validators=[DataRequired()])
    observacao = TextAreaField('Observação')
    submit = SubmitField('Aplicar')

class UsuarioForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Salvar')

    def validate_email(self, email):
        from app.models import Usuario
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario and (not hasattr(self, 'id') or usuario.id != self.id):
            raise ValidationError('Este e-mail já está em uso.')
