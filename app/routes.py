from flask import render_template, redirect, url_for, flash, request, make_response
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Usuario,Cliente,OrdemServico,Produto,MovimentacaoEstoque,Usuario
from app.forms import LoginForm,ClienteForm,OrdemServicoForm,ProdutoForm,MovimentacaoForm,UsuarioForm
from weasyprint import HTML
from io import BytesIO
from datetime import datetime
from werkzeug.security import generate_password_hash

def configurar_rotas(app):
    @app.route('/', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            usuario = Usuario.query.filter_by(email=form.email.data).first()
            if usuario and usuario.verificar_senha(form.senha.data):
                login_user(usuario)
                return redirect(url_for('dashboard'))
            flash('Usuário ou senha inválidos')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        total_clientes = Cliente.query.count()
        total_ordens = OrdemServico.query.count()
        ordens_aguardando = OrdemServico.query.filter_by(status='Aguardando').count()
        ordens_andamento = OrdemServico.query.filter_by(status='Em andamento').count()
        ordens_finalizadas = OrdemServico.query.filter_by(status='Finalizado').count()

        return render_template(
            'dashboard.html',
            total_clientes=total_clientes,
            total_ordens=total_ordens,
            ordens_aguardando=ordens_aguardando,
            ordens_andamento=ordens_andamento,
            ordens_finalizadas=ordens_finalizadas
        )
    
    @app.route('/clientes')
    @login_required
    def listar_clientes():
        clientes = Cliente.query.all()
        return render_template('clientes/listar.html', clientes=clientes)

    @app.route('/clientes/novo', methods=['GET', 'POST'])
    @login_required
    def novo_cliente():
        form = ClienteForm()
        if form.validate_on_submit():
            cliente = Cliente(
                nome=form.nome.data,
                telefone=form.telefone.data,
                email=form.email.data,
                endereco=form.endereco.data,
                observacoes=form.observacoes.data
            )
            db.session.add(cliente)
            db.session.commit()
            flash('Cliente cadastrado com sucesso!')
            return redirect(url_for('listar_clientes'))
        return render_template('clientes/novo.html', form=form)

    @app.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
    @login_required
    def editar_cliente(id):
        cliente = Cliente.query.get_or_404(id)
        form = ClienteForm(obj=cliente)
        if form.validate_on_submit():
            form.populate_obj(cliente)
            db.session.commit()
            flash('Cliente atualizado com sucesso!')
            return redirect(url_for('listar_clientes'))
        return render_template('clientes/editar.html', form=form, cliente=cliente)

    @app.route('/clientes/<int:id>/excluir', methods=['POST'])
    @login_required
    def excluir_cliente(id):
        cliente = Cliente.query.get_or_404(id)

        if cliente.ordens:
            flash("Não é possível excluir este cliente. Ele possui ordens de serviço vinculadas.")
            return redirect(url_for('listar_clientes'))
        
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente excluído com sucesso!')
        return redirect(url_for('listar_clientes'))

    @app.route('/ordens')
    @login_required
    def listar_ordens():
        status = request.args.get('status')
        cliente_id = request.args.get('cliente_id', type=int)
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')

        query = OrdemServico.query

        if status:
            query = query.filter_by(status=status)
        if cliente_id:
            query = query.filter_by(cliente_id=cliente_id)

        if data_inicial:
            try:
                dt_inicial = datetime.strptime(data_inicial, '%Y-%m-%d')
                query = query.filter(OrdemServico.data_criacao >= dt_inicial)
            except ValueError:
                flash('Data inicial inválida.')
        if data_final:
            try:
                dt_final = datetime.strptime(data_final, '%Y-%m-%d')
                query = query.filter(OrdemServico.data_criacao <= dt_final)
            except ValueError:
                flash('Data final inválida.')

        ordens = query.order_by(OrdemServico.data_criacao.desc()).all()
        clientes = Cliente.query.order_by(Cliente.nome).all()
        
        return render_template(
            'ordens/listar.html',
            ordens=ordens,
            clientes=clientes,
            filtro_status=status,
            filtro_cliente_id=cliente_id
        )

    @app.route('/ordens/nova', methods=['GET', 'POST'])
    @login_required
    def nova_ordem():
        form = OrdemServicoForm()
        form.cliente_id.choices = [(c.id, c.nome) for c in Cliente.query.order_by(Cliente.nome).all()]

        if form.validate_on_submit():
            ordem = OrdemServico(
                titulo=form.titulo.data,
                descricao=form.descricao.data,
                status=form.status.data,
                data_conclusao=form.data_conclusao.data,
                valor=form.valor.data,
                observacoes=form.observacoes.data,
                cliente_id=form.cliente_id.data
            )
            db.session.add(ordem)
            db.session.commit()
            flash('Ordem de serviço criada com sucesso!')
            return redirect(url_for('listar_ordens'))
        return render_template('ordens/novo.html', form=form)

    @app.route('/ordens/<int:id>/editar', methods=['GET', 'POST'])
    @login_required
    def editar_ordem(id):
        ordem = OrdemServico.query.get_or_404(id)
        form = OrdemServicoForm(obj=ordem)
        form.cliente_id.choices = [(c.id, c.nome) for c in Cliente.query.order_by(Cliente.nome).all()]

        if form.validate_on_submit():
            form.populate_obj(ordem)
            db.session.commit()
            flash('Ordem de serviço atualizada com sucesso!')
            return redirect(url_for('listar_ordens'))
        return render_template('ordens/editar.html', form=form, ordem=ordem)

    @app.route('/ordens/<int:id>/excluir', methods=['POST'])
    @login_required
    def excluir_ordem(id):
        ordem = OrdemServico.query.get_or_404(id)
        db.session.delete(ordem)
        db.session.commit()
        flash('Ordem de serviço excluída com sucesso!')
        return redirect(url_for('listar_ordens'))

    @app.route('/ordens/pdf')
    @login_required
    def exportar_pdf():
        status = request.args.get('status')
        cliente_id = request.args.get('cliente_id', type=int)

        query = OrdemServico.query
        if status:
            query = query.filter_by(status=status)
        if cliente_id:
            query = query.filter_by(cliente_id=cliente_id)

        ordens = query.order_by(OrdemServico.data_criacao.desc()).all()

        html = render_template('ordens/pdf.html', ordens=ordens)

        pdf_io = BytesIO()
        HTML(string=html).write_pdf(pdf_io)
        pdf_io.seek(0)

        response = make_response(pdf_io.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=ordens_servico.pdf'
        return response

    @app.route('/ordens/<int:id>/pdf')
    @login_required
    def exportar_ordem_pdf(id):
        ordem = OrdemServico.query.get_or_404(id)
        html = render_template('ordens/ordem_pdf.html', ordem=ordem)
    
        pdf_io = BytesIO()
        HTML(string=html).write_pdf(pdf_io)
        pdf_io.seek(0)
    
        response = make_response(pdf_io.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=ordem_{ordem.id}.pdf'
        return response
    
    @app.route('/estoque')
    @login_required
    def listar_produtos():
        produtos = Produto.query.order_by(Produto.nome).all()
        return render_template('estoque/listar.html', produtos=produtos)

    @app.route('/estoque/novo', methods=['GET', 'POST'])
    @login_required
    def novo_produto():
        form = ProdutoForm()
        if form.validate_on_submit():
            produto = Produto(
                nome=form.nome.data,
                descricao=form.descricao.data,
                quantidade=form.quantidade.data,
                unidade=form.unidade.data,
                categoria=form.categoria.data,
                preco=form.preco.data
            )
            db.session.add(produto)
            db.session.commit()
            flash('Produto cadastrado com sucesso!')
            return redirect(url_for('listar_produtos'))
        return render_template('estoque/form.html', form=form, produto=None)

    @app.route('/estoque/<int:id>/editar', methods=['GET', 'POST'])
    @login_required
    def editar_produto(id):
        produto = Produto.query.get_or_404(id)
        form = ProdutoForm(obj=produto)
        if form.validate_on_submit():
            form.populate_obj(produto)
            db.session.commit()
            flash('Produto atualizado com sucesso!')
            return redirect(url_for('listar_produtos'))
        return render_template('estoque/form.html', form=form, produto=produto)

    @app.route('/estoque/<int:id>/excluir', methods=['POST'])
    @login_required
    def excluir_produto(id):
        produto = Produto.query.get_or_404(id)
        db.session.delete(produto)
        db.session.commit()
        flash('Produto excluído com sucesso!')
        return redirect(url_for('listar_produtos'))

    @app.route('/estoque/<int:id>/movimentar', methods=['GET', 'POST'])
    @login_required
    def movimentar_produto(id):
        produto = Produto.query.get_or_404(id)
        form = MovimentacaoForm()

        if form.validate_on_submit():
            qtd = form.quantidade.data
            tipo = form.tipo.data

            if tipo == 'Entrada':
                produto.quantidade += qtd
            elif tipo == 'Saída':
                if produto.quantidade < qtd:
                    flash('Quantidade insuficiente no estoque.')
                    return redirect(url_for('movimentar_produto', id=id))
                produto.quantidade -= qtd
            elif tipo == 'Ajuste':
                produto.quantidade = qtd  # ajuste direto (opcional: pode ser interpretado de outras formas)

            movimentacao = MovimentacaoEstoque(
                tipo=tipo,
                quantidade=qtd,
                observacao=form.observacao.data,
                produto=produto,
                usuario=current_user
            )

            db.session.add(movimentacao)
            db.session.commit()
            flash('Movimentação registrada com sucesso!')
            return redirect(url_for('listar_produtos'))

        return render_template('estoque/movimentar.html', form=form, produto=produto)

    @app.route('/estoque/<int:id>/historico')
    @login_required
    def ver_historico_produto(id):
        produto = Produto.query.get_or_404(id)
        movimentacoes = MovimentacaoEstoque.query.filter_by(produto_id=id).order_by(MovimentacaoEstoque.data.desc()).all()
        return render_template('estoque/historico.html', produto=produto, movimentacoes=movimentacoes)

    @app.route('/estoque/<int:id>/historico/pdf')
    @login_required
    def exportar_historico_pdf(id):
        produto = Produto.query.get_or_404(id)
        movimentacoes = MovimentacaoEstoque.query.filter_by(produto_id=id).order_by(MovimentacaoEstoque.data.desc()).all()
        html = render_template('estoque/historico_pdf.html', produto=produto, movimentacoes=movimentacoes)

        pdf_io = BytesIO()
        HTML(string=html).write_pdf(pdf_io)
        pdf_io.seek(0)

        response = make_response(pdf_io.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=historico_{produto.nome}.pdf'
        return response

    @app.route('/estoque/historico/pdf')
    @login_required
    def exportar_historico_geral_pdf():
        from datetime import datetime

        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        produto_id = request.args.get('produto_id', type=int)

        query = MovimentacaoEstoque.query

        if produto_id:
            query = query.filter_by(produto_id=produto_id)

        if data_inicial:
            try:
                dt_ini = datetime.strptime(data_inicial, '%Y-%m-%d')
                query = query.filter(MovimentacaoEstoque.data >= dt_ini)
            except ValueError:
                flash('Data inicial inválida.')

        if data_final:
            try:
                dt_fim = datetime.strptime(data_final, '%Y-%m-%d')
                query = query.filter(MovimentacaoEstoque.data <= dt_fim)
            except ValueError:
                flash('Data final inválida.')

        movimentacoes = query.order_by(MovimentacaoEstoque.data.desc()).all()

        html = render_template('estoque/historico_geral_pdf.html', movimentacoes=movimentacoes)
        pdf_io = BytesIO()
        HTML(string=html).write_pdf(pdf_io)
        pdf_io.seek(0)

        response = make_response(pdf_io.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=historico_filtrado.pdf'
        return response

    @app.route('/estoque/pdf')
    @login_required
    def exportar_produtos_pdf():
        produtos = Produto.query.order_by(Produto.nome).all()
        html = render_template('estoque/produtos_pdf.html', produtos=produtos)

        pdf_io = BytesIO()
        HTML(string=html).write_pdf(pdf_io)
        pdf_io.seek(0)

        response = make_response(pdf_io.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=produtos_estoque.pdf'
        return response
    
    @app.route('/relatorios')
    @login_required
    def relatorios():
        produtos = Produto.query.order_by(Produto.nome).all()
        return render_template('relatorios/index.html', produtos=produtos)

    @app.route('/usuarios')
    @login_required
    def listar_usuarios():
        usuarios = Usuario.query.order_by(Usuario.nome).all()
        return render_template('usuarios/listar.html', usuarios=usuarios)

    @app.route('/usuarios/novo', methods=['GET', 'POST'])
    @login_required
    def novo_usuario():
        form = UsuarioForm()
        if form.validate_on_submit():
            usuario = Usuario(
                nome=form.nome.data,
                email=form.email.data,
                senha_hash=generate_password_hash(form.senha.data)
            )
            db.session.add(usuario)
            db.session.commit()
            flash('Usuário cadastrado com sucesso!')
            return redirect(url_for('listar_usuarios'))
        return render_template('usuarios/form.html', form=form, usuario=None)

    @app.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
    @login_required
    def editar_usuario(id):
        usuario = Usuario.query.get_or_404(id)
        form = UsuarioForm(obj=usuario)
        form.id = usuario.id  # necessário para validar email apenas se for diferente

        if form.validate_on_submit():
            usuario.nome = form.nome.data
            usuario.email = form.email.data
            if form.senha.data:
                usuario.senha_hash = generate_password_hash(form.senha.data)
            db.session.commit()
            flash('Usuário atualizado com sucesso!')
            return redirect(url_for('listar_usuarios'))

        return render_template('usuarios/form.html', form=form, usuario=usuario)

    @app.route('/usuarios/<int:id>/excluir', methods=['POST'])
    @login_required
    def excluir_usuario(id):
        usuario = Usuario.query.get_or_404(id)
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuário excluído com sucesso!')
        return redirect(url_for('listar_usuarios'))
    
    @app.route('/auditoria')
    @login_required
    def auditoria():
        movimentacoes = MovimentacaoEstoque.query.order_by(MovimentacaoEstoque.data.desc()).all()
        return render_template('auditoria.html', movimentacoes=movimentacoes)
