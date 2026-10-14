import sqlite3
import calendar
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox


ARQUIVO_BANCO = "finance.db"

SUBCATEGORIAS = [
    "Moradia",
    "Alimentação",
    "Transporte",
    "Trabalho",
    "Saúde",
    "Lazer",
    "Educação",
    "Contas",
    "Compras",
    "Outros"
]


# =========================================================
# BANCO DE DADOS
# =========================================================

def conectar_banco():
    return sqlite3.connect(ARQUIVO_BANCO)


def criar_tabelas():

    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Tabela original.
    # Não apagamos nem alteramos as movimentações existentes.

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            subcategoria TEXT NOT NULL,
            descricao TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)

    # Nova tabela da Missão 26.

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            valor REAL NOT NULL,
            subcategoria TEXT NOT NULL,
            descricao TEXT NOT NULL,
            dia_vencimento INTEGER NOT NULL,
            ativa INTEGER NOT NULL DEFAULT 1
        )
    """)

    # Esta tabela registra quais recorrências já foram
    # geradas em cada mês.
    #
    # UNIQUE(recorrencia_id, mes_referencia)
    # impede que a mesma recorrência seja gerada duas vezes
    # para o mesmo mês.

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recorrencias_geradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recorrencia_id INTEGER NOT NULL,
            mes_referencia TEXT NOT NULL,
            transacao_id INTEGER NOT NULL,
            UNIQUE(recorrencia_id, mes_referencia)
        )
    """)

    conexao.commit()
    conexao.close()


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def formatar_moeda(valor):

    texto = f"{valor:,.2f}"

    texto = (
        texto
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"R$ {texto}"


def converter_valor(texto):

    texto = (
        texto
        .strip()
        .replace("R$", "")
        .replace(" ", "")
    )

    if "," in texto:

        texto = (
            texto
            .replace(".", "")
            .replace(",", ".")
        )

    try:
        valor = float(texto)

    except ValueError:
        return None

    if valor <= 0:
        return None

    return valor


def converter_data_para_banco(data):

    try:

        return datetime.strptime(
            data,
            "%d/%m/%Y"
        ).strftime("%Y-%m-%d")

    except ValueError:

        return None


def converter_data_para_tela(data):

    try:

        return datetime.strptime(
            data,
            "%Y-%m-%d"
        ).strftime("%d/%m/%Y")

    except ValueError:

        return data


def intervalo_mes(mes_ano):

    try:

        inicio = datetime.strptime(
            "01/" + mes_ano,
            "%d/%m/%Y"
        )

    except ValueError:

        return None, None

    if inicio.month == 12:

        fim = datetime(
            inicio.year + 1,
            1,
            1
        )

    else:

        fim = datetime(
            inicio.year,
            inicio.month + 1,
            1
        )

    return (
        inicio.strftime("%Y-%m-%d"),
        fim.strftime("%Y-%m-%d")
    )


def data_recorrencia(mes_ano, dia):

    try:

        mes, ano = mes_ano.split("/")

        mes = int(mes)
        ano = int(ano)

        ultimo_dia = calendar.monthrange(
            ano,
            mes
        )[1]

        # Exemplo:
        # vencimento dia 31 em fevereiro.
        # Nesse caso usamos o último dia de fevereiro.

        dia_real = min(
            dia,
            ultimo_dia
        )

        return datetime(
            ano,
            mes,
            dia_real
        ).strftime("%Y-%m-%d")

    except (ValueError, IndexError):

        return None


# =========================================================
# APLICAÇÃO
# =========================================================

class FinanceApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Assistente Financeiro"
        )

        self.root.geometry(
            "1200x780"
        )

        self.root.minsize(
            1000,
            680
        )

        self.id_em_edicao = None

        self.id_recorrencia_em_edicao = None

        criar_tabelas()

        self.configurar_estilo()

        self.criar_interface()

        self.atualizar_tudo()


    # =====================================================
    # ESTILO
    # =====================================================

    def configurar_estilo(self):

        estilo = ttk.Style()

        try:

            estilo.theme_use(
                "clam"
            )

        except tk.TclError:

            pass

        estilo.configure(
            "Titulo.TLabel",
            font=(
                "Segoe UI",
                22,
                "bold"
            )
        )

        estilo.configure(
            "Subtitulo.TLabel",
            font=(
                "Segoe UI",
                11
            )
        )

        estilo.configure(
            "CardTitulo.TLabel",
            font=(
                "Segoe UI",
                10
            )
        )

        estilo.configure(
            "CardValor.TLabel",
            font=(
                "Segoe UI",
                17,
                "bold"
            )
        )

        estilo.configure(
            "Treeview",
            rowheight=30,
            font=(
                "Segoe UI",
                10
            )
        )

        estilo.configure(
            "Treeview.Heading",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        estilo.configure(
            "TNotebook.Tab",
            padding=(
                12,
                7
            )
        )

        estilo.configure(
            "TButton",
            padding=6
        )


    # =====================================================
    # INTERFACE
    # =====================================================

    def criar_interface(self):

        cabecalho = ttk.Frame(
            self.root
        )

        cabecalho.pack(
            fill="x",
            padx=20,
            pady=(18, 5)
        )

        ttk.Label(
            cabecalho,
            text="Assistente Financeiro",
            style="Titulo.TLabel"
        ).pack(
            anchor="w"
        )

        ttk.Label(
            cabecalho,
            text=(
                "Controle de ganhos, gastos "
                "e movimentações financeiras"
            ),
            style="Subtitulo.TLabel"
        ).pack(
            anchor="w"
        )

        self.abas = ttk.Notebook(
            self.root
        )

        self.abas.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=15
        )

        self.aba_movimentacoes = ttk.Frame(
            self.abas
        )

        self.aba_fixos = ttk.Frame(
            self.abas
        )

        self.aba_variaveis = ttk.Frame(
            self.abas
        )

        self.aba_ganhos = ttk.Frame(
            self.abas
        )

        self.aba_recorrencias = ttk.Frame(
            self.abas
        )

        self.aba_resumo = ttk.Frame(
            self.abas
        )

        self.aba_anual = ttk.Frame(
            self.abas
        )

        self.abas.add(
            self.aba_movimentacoes,
            text="Movimentações"
        )

        self.abas.add(
            self.aba_fixos,
            text="Gastos Fixos"
        )

        self.abas.add(
            self.aba_variaveis,
            text="Gastos Variáveis"
        )

        self.abas.add(
            self.aba_ganhos,
            text="Ganhos"
        )

        self.abas.add(
            self.aba_recorrencias,
            text="Recorrências"
        )

        self.abas.add(
            self.aba_resumo,
            text="Resumo mensal"
        )

        self.abas.add(
            self.aba_anual,
            text="Controle do ano"
        )

        self.criar_aba_movimentacoes()

        self.criar_aba_tipo(
            self.aba_fixos,
            "Gasto Fixo"
        )

        self.criar_aba_tipo(
            self.aba_variaveis,
            "Gasto Variável"
        )

        self.criar_aba_tipo(
            self.aba_ganhos,
            "Ganho"
        )

        self.criar_aba_recorrencias()

        self.criar_aba_resumo()

        self.criar_aba_anual()


    # =====================================================
    # ABA MOVIMENTAÇÕES
    # =====================================================

    def criar_aba_movimentacoes(self):

        formulario = ttk.LabelFrame(
            self.aba_movimentacoes,
            text="Cadastrar movimentação"
        )

        formulario.pack(
            fill="x",
            padx=15,
            pady=15
        )

        ttk.Label(
            formulario,
            text="Tipo"
        ).grid(
            row=0,
            column=0,
            padx=8,
            pady=(10, 4),
            sticky="w"
        )

        self.tipo_var = tk.StringVar()

        self.tipo_combo = ttk.Combobox(
            formulario,
            textvariable=self.tipo_var,
            values=[
                "Gasto Fixo",
                "Gasto Variável",
                "Ganho"
            ],
            state="readonly",
            width=18
        )

        self.tipo_combo.grid(
            row=1,
            column=0,
            padx=8,
            pady=(0, 12)
        )

        ttk.Label(
            formulario,
            text="Valor"
        ).grid(
            row=0,
            column=1,
            padx=8,
            pady=(10, 4),
            sticky="w"
        )

        self.valor_var = tk.StringVar()

        ttk.Entry(
            formulario,
            textvariable=self.valor_var,
            width=16
        ).grid(
            row=1,
            column=1,
            padx=8,
            pady=(0, 12)
        )

        ttk.Label(
            formulario,
            text="Subcategoria"
        ).grid(
            row=0,
            column=2,
            padx=8,
            pady=(10, 4),
            sticky="w"
        )

        self.subcategoria_var = tk.StringVar()

        self.subcategoria_combo = ttk.Combobox(
            formulario,
            textvariable=self.subcategoria_var,
            values=SUBCATEGORIAS,
            width=18
        )

        self.subcategoria_combo.grid(
            row=1,
            column=2,
            padx=8,
            pady=(0, 12)
        )

        ttk.Label(
            formulario,
            text="Descrição"
        ).grid(
            row=0,
            column=3,
            padx=8,
            pady=(10, 4),
            sticky="w"
        )

        self.descricao_var = tk.StringVar()

        ttk.Entry(
            formulario,
            textvariable=self.descricao_var,
            width=30
        ).grid(
            row=1,
            column=3,
            padx=8,
            pady=(0, 12)
        )

        ttk.Label(
            formulario,
            text="Data"
        ).grid(
            row=0,
            column=4,
            padx=8,
            pady=(10, 4),
            sticky="w"
        )

        self.data_var = tk.StringVar(
            value=datetime.now().strftime(
                "%d/%m/%Y"
            )
        )

        ttk.Entry(
            formulario,
            textvariable=self.data_var,
            width=14
        ).grid(
            row=1,
            column=4,
            padx=8,
            pady=(0, 12)
        )

        frame_botoes = ttk.Frame(
            formulario
        )

        frame_botoes.grid(
            row=1,
            column=5,
            padx=8,
            pady=(0, 12)
        )

        self.botao_salvar = ttk.Button(
            frame_botoes,
            text="Salvar",
            command=self.salvar_movimentacao
        )

        self.botao_salvar.pack(
            side="left",
            padx=3
        )

        self.botao_cancelar = ttk.Button(
            frame_botoes,
            text="Limpar",
            command=self.limpar_formulario
        )

        self.botao_cancelar.pack(
            side="left",
            padx=3
        )

        frame_filtro = ttk.Frame(
            self.aba_movimentacoes
        )

        frame_filtro.pack(
            fill="x",
            padx=15,
            pady=(0, 10)
        )

        ttk.Label(
            frame_filtro,
            text="Movimentações do mês:"
        ).pack(
            side="left"
        )

        self.mes_movimentacoes_var = tk.StringVar(
            value=datetime.now().strftime(
                "%m/%Y"
            )
        )

        ttk.Entry(
            frame_filtro,
            textvariable=self.mes_movimentacoes_var,
            width=10
        ).pack(
            side="left",
            padx=8
        )

        ttk.Button(
            frame_filtro,
            text="Buscar",
            command=self.carregar_movimentacoes
        ).pack(
            side="left"
        )

        ttk.Button(
            frame_filtro,
            text="Excluir selecionada",
            command=self.excluir_movimentacao
        ).pack(
            side="right",
            padx=5
        )

        ttk.Button(
            frame_filtro,
            text="Editar selecionada",
            command=self.editar_movimentacao
        ).pack(
            side="right",
            padx=5
        )

        frame_tabela = ttk.Frame(
            self.aba_movimentacoes
        )

        frame_tabela.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15)
        )

        self.tabela_movimentacoes = (
            self.criar_tabela_movimentacoes(
                frame_tabela,
                mostrar_tipo=True
            )
        )

        self.tabela_movimentacoes.bind(
            "<Double-1>",
            lambda event:
            self.editar_movimentacao()
        )


    # =====================================================
    # TABELA DE MOVIMENTAÇÕES
    # =====================================================

    def criar_tabela_movimentacoes(
        self,
        container,
        mostrar_tipo=True
    ):

        area_tabela = ttk.Frame(
            container
        )

        area_tabela.pack(
            fill="both",
            expand=True
        )

        if mostrar_tipo:

            colunas = (
                "id",
                "tipo",
                "valor",
                "subcategoria",
                "descricao",
                "data"
            )

        else:

            colunas = (
                "id",
                "valor",
                "subcategoria",
                "descricao",
                "data"
            )

        tabela = ttk.Treeview(
            area_tabela,
            columns=colunas,
            show="headings"
        )

        tabela.heading(
            "id",
            text="ID",
            anchor="center"
        )

        tabela.column(
            "id",
            width=65,
            minwidth=65,
            anchor="center",
            stretch=False
        )

        if mostrar_tipo:

            tabela.heading(
                "tipo",
                text="Tipo",
                anchor="center"
            )

            tabela.column(
                "tipo",
                width=190,
                minwidth=190,
                anchor="center",
                stretch=False
            )

        tabela.heading(
            "valor",
            text="Valor",
            anchor="center"
        )

        tabela.column(
            "valor",
            width=210,
            minwidth=210,
            anchor="center",
            stretch=False
        )

        tabela.heading(
            "subcategoria",
            text="Subcategoria",
            anchor="center"
        )

        tabela.column(
            "subcategoria",
            width=250,
            minwidth=250,
            anchor="center",
            stretch=False
        )

        tabela.heading(
            "descricao",
            text="Descrição",
            anchor="center"
        )

        tabela.column(
            "descricao",
            width=430,
            minwidth=430,
            anchor="center",
            stretch=False
        )

        tabela.heading(
            "data",
            text="Data",
            anchor="center"
        )

        tabela.column(
            "data",
            width=150,
            minwidth=150,
            anchor="center",
            stretch=False
        )

        scrollbar_vertical = ttk.Scrollbar(
            area_tabela,
            orient="vertical",
            command=tabela.yview
        )

        scrollbar_horizontal = ttk.Scrollbar(
            area_tabela,
            orient="horizontal",
            command=tabela.xview
        )

        tabela.configure(
            yscrollcommand=scrollbar_vertical.set,
            xscrollcommand=scrollbar_horizontal.set
        )

        tabela.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar_vertical.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        scrollbar_horizontal.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        area_tabela.rowconfigure(
            0,
            weight=1
        )

        area_tabela.columnconfigure(
            0,
            weight=1
        )

        return tabela


    # =====================================================
    # ABAS POR TIPO
    # =====================================================

    def criar_aba_tipo(
        self,
        aba,
        tipo
    ):

        topo = ttk.Frame(
            aba
        )

        topo.pack(
            fill="x",
            padx=20,
            pady=20
        )

        ttk.Label(
            topo,
            text="Mês:"
        ).pack(
            side="left"
        )

        mes_var = tk.StringVar(
            value=datetime.now().strftime(
                "%m/%Y"
            )
        )

        ttk.Entry(
            topo,
            textvariable=mes_var,
            width=10
        ).pack(
            side="left",
            padx=8
        )

        ttk.Button(
            topo,
            text="Atualizar",
            command=lambda:
            self.atualizar_aba_tipo(
                tipo
            )
        ).pack(
            side="left"
        )

        card = ttk.LabelFrame(
            aba
        )

        card.pack(
            fill="x",
            padx=20,
            pady=(0, 15)
        )

        ttk.Label(
            card,
            text="Total do mês",
            style="CardTitulo.TLabel"
        ).pack(
            anchor="w",
            padx=15,
            pady=(12, 2)
        )

        label_total = ttk.Label(
            card,
            text="R$ 0,00",
            style="CardValor.TLabel"
        )

        label_total.pack(
            anchor="w",
            padx=15,
            pady=(0, 15)
        )

        frame_tabela = ttk.Frame(
            aba
        )

        frame_tabela.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        tabela = (
            self.criar_tabela_movimentacoes(
                frame_tabela,
                mostrar_tipo=False
            )
        )

        if tipo == "Gasto Fixo":

            self.mes_fixos_var = mes_var
            self.total_fixos_label = label_total
            self.tabela_fixos = tabela

        elif tipo == "Gasto Variável":

            self.mes_variaveis_var = mes_var
            self.total_variaveis_label = label_total
            self.tabela_variaveis = tabela

        else:

            self.mes_ganhos_var = mes_var
            self.total_ganhos_label = label_total
            self.tabela_ganhos = tabela


    # =====================================================
    # SALVAR MOVIMENTAÇÃO
    # =====================================================

    def salvar_movimentacao(self):

        tipo = (
            self.tipo_var
            .get()
            .strip()
        )

        valor = converter_valor(
            self.valor_var.get()
        )

        subcategoria = (
            self.subcategoria_var
            .get()
            .strip()
        )

        descricao = (
            self.descricao_var
            .get()
            .strip()
        )

        data = (
            self.data_var
            .get()
            .strip()
        )

        if not tipo:

            messagebox.showerror(
                "Erro",
                "Escolha o tipo da movimentação."
            )

            return

        if valor is None:

            messagebox.showerror(
                "Erro",
                "Digite um valor válido maior que zero."
            )

            return

        if not subcategoria:

            messagebox.showerror(
                "Erro",
                "Informe a subcategoria."
            )

            return

        if not descricao:

            messagebox.showerror(
                "Erro",
                "Informe uma descrição."
            )

            return

        data_banco = converter_data_para_banco(
            data
        )

        if data_banco is None:

            messagebox.showerror(
                "Erro",
                "Use a data no formato DD/MM/AAAA."
            )

            return

        conexao = conectar_banco()
        cursor = conexao.cursor()

        if self.id_em_edicao is None:

            cursor.execute("""
                INSERT INTO transacoes (
                    tipo,
                    valor,
                    subcategoria,
                    descricao,
                    data
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                tipo,
                valor,
                subcategoria,
                descricao,
                data_banco
            ))

            mensagem = (
                "Movimentação salva com sucesso!"
            )

        else:

            cursor.execute("""
                UPDATE transacoes
                SET
                    tipo = ?,
                    valor = ?,
                    subcategoria = ?,
                    descricao = ?,
                    data = ?
                WHERE id = ?
            """, (
                tipo,
                valor,
                subcategoria,
                descricao,
                data_banco,
                self.id_em_edicao
            ))

            mensagem = (
                "Movimentação atualizada com sucesso!"
            )

        conexao.commit()
        conexao.close()

        self.limpar_formulario()

        self.atualizar_tudo()

        messagebox.showinfo(
            "Sucesso",
            mensagem
        )


    # =====================================================
    # EDITAR MOVIMENTAÇÃO
    # =====================================================

    def editar_movimentacao(self):

        selecionado = (
            self.tabela_movimentacoes
            .selection()
        )

        if not selecionado:

            messagebox.showwarning(
                "Atenção",
                "Selecione uma movimentação."
            )

            return

        item = self.tabela_movimentacoes.item(
            selecionado[0]
        )

        id_transacao = (
            item["values"][0]
        )

        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                tipo,
                valor,
                subcategoria,
                descricao,
                data
            FROM transacoes
            WHERE id = ?
        """, (
            id_transacao,
        ))

        transacao = cursor.fetchone()

        conexao.close()

        if transacao is None:

            messagebox.showerror(
                "Erro",
                "Movimentação não encontrada."
            )

            return

        (
            tipo,
            valor,
            subcategoria,
            descricao,
            data
        ) = transacao

        self.id_em_edicao = (
            id_transacao
        )

        self.tipo_var.set(
            tipo
        )

        self.valor_var.set(
            f"{valor:.2f}".replace(
                ".",
                ","
            )
        )

        self.subcategoria_var.set(
            subcategoria
        )

        self.descricao_var.set(
            descricao
        )

        self.data_var.set(
            converter_data_para_tela(
                data
            )
        )

        self.botao_salvar.config(
            text="Salvar alterações"
        )

        self.botao_cancelar.config(
            text="Cancelar edição"
        )


    # =====================================================
    # EXCLUIR MOVIMENTAÇÃO
    # =====================================================

    def excluir_movimentacao(self):

        selecionado = (
            self.tabela_movimentacoes
            .selection()
        )

        if not selecionado:

            messagebox.showwarning(
                "Atenção",
                "Selecione uma movimentação."
            )

            return

        item = self.tabela_movimentacoes.item(
            selecionado[0]
        )

        valores = item["values"]

        id_transacao = valores[0]
        valor = valores[2]
        descricao = valores[4]

        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            (
                "Deseja realmente excluir "
                "esta movimentação?\n\n"
                f"{descricao}\n"
                f"{valor}"
            )
        )

        if not confirmar:

            return

        conexao = conectar_banco()
        cursor = conexao.cursor()

        # Caso seja uma movimentação criada por uma
        # recorrência, removemos também o registro de geração.
        # Assim ela poderá ser gerada novamente se necessário.

        cursor.execute("""
            DELETE FROM recorrencias_geradas
            WHERE transacao_id = ?
        """, (
            id_transacao,
        ))

        cursor.execute("""
            DELETE FROM transacoes
            WHERE id = ?
        """, (
            id_transacao,
        ))

        conexao.commit()
        conexao.close()

        self.atualizar_tudo()

        messagebox.showinfo(
            "Sucesso",
            "Movimentação excluída."
        )


    # =====================================================
    # LIMPAR FORMULÁRIO
    # =====================================================

    def limpar_formulario(self):

        self.id_em_edicao = None

        self.tipo_var.set("")
        self.valor_var.set("")
        self.subcategoria_var.set("")
        self.descricao_var.set("")

        self.data_var.set(
            datetime.now().strftime(
                "%d/%m/%Y"
            )
        )

        self.botao_salvar.config(
            text="Salvar"
        )

        self.botao_cancelar.config(
            text="Limpar"
        )


    # =====================================================
    # CARREGAR MOVIMENTAÇÕES
    # =====================================================

    def carregar_movimentacoes(self):

        mes = (
            self.mes_movimentacoes_var
            .get()
            .strip()
        )

        inicio, fim = intervalo_mes(
            mes
        )

        if inicio is None:

            messagebox.showerror(
                "Erro",
                "Use o mês no formato MM/AAAA."
            )

            return

        for item in (
            self.tabela_movimentacoes
            .get_children()
        ):

            self.tabela_movimentacoes.delete(
                item
            )

        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                id,
                tipo,
                valor,
                subcategoria,
                descricao,
                data
            FROM transacoes
            WHERE data >= ?
            AND data < ?
            ORDER BY data DESC, id DESC
        """, (
            inicio,
            fim
        ))

        resultados = (
            cursor.fetchall()
        )

        conexao.close()

        for (
            id_transacao,
            tipo,
            valor,
            subcategoria,
            descricao,
            data
        ) in resultados:

            self.tabela_movimentacoes.insert(
                "",
                "end",
                values=(
                    id_transacao,
                    tipo,
                    formatar_moeda(
                        valor
                    ),
                    subcategoria,
                    descricao,
                    converter_data_para_tela(
                        data
                    )
                )
            )


    # =====================================================
    # ATUALIZAR ABAS POR TIPO
    # =====================================================

    def atualizar_aba_tipo(
        self,
        tipo
    ):

        if tipo == "Gasto Fixo":

            mes = (
                self.mes_fixos_var
                .get()
                .strip()
            )

            tabela = (
                self.tabela_fixos
            )

            label_total = (
                self.total_fixos_label
            )

        elif tipo == "Gasto Variável":

            mes = (
                self.mes_variaveis_var
                .get()
                .strip()
            )

            tabela = (
                self.tabela_variaveis
            )

            label_total = (
                self.total_variaveis_label
            )

        else:

            mes = (
                self.mes_ganhos_var
                .get()
                .strip()
            )

            tabela = (
                self.tabela_ganhos
            )

            label_total = (
                self.total_ganhos_label
            )

        inicio, fim = intervalo_mes(
            mes
        )

        if inicio is None:

            return

        for item in tabela.get_children():

            tabela.delete(
                item
            )

        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                id,
                valor,
                subcategoria,
                descricao,
                data
            FROM transacoes
            WHERE tipo = ?
            AND data >= ?
            AND data < ?
            ORDER BY data DESC, id DESC
        """, (
            tipo,
            inicio,
            fim
        ))

        resultados = (
            cursor.fetchall()
        )

        total = 0

        for (
            id_transacao,
            valor,
            subcategoria,
            descricao,
            data
        ) in resultados:

            total += valor

            tabela.insert(
                "",
                "end",
                values=(
                    id_transacao,
                    formatar_moeda(
                        valor
                    ),
                    subcategoria,
                    descricao,
                    converter_data_para_tela(
                        data
                    )
                )
            )

        conexao.close()

        # Linha final com o total do mês na própria tabela.
        # As colunas destas abas são:
        # ID | Valor | Subcategoria | Descrição | Data
        tabela.insert(
            "",
            "end",
            values=(
                "TOTAL",
                formatar_moeda(total),
                "",
                "",
                ""
            ),
            tags=("linha_total",)
        )

        tabela.tag_configure(
            "linha_total",
            font=("Segoe UI", 10, "bold")
        )

        label_total.config(
            text=formatar_moeda(
                total
            )
        )


    # =====================================================
    # MISSÃO 26
    # ABA RECORRÊNCIAS
    # =====================================================

    def criar_aba_recorrencias(self):

        formulario = ttk.LabelFrame(
            self.aba_recorrencias,
            text="Cadastrar gasto fixo recorrente"
        )

        formulario.pack(
            fill="x",
            padx=20,
            pady=20
        )

        # VALOR

        ttk.Label(
            formulario,
            text="Valor"
        ).grid(
            row=0,
            column=0,
            padx=8,
            pady=(10, 4),
            sticky="w"
        )

        self.rec_valor_var = (
            tk.StringVar()
        )

        ttk.Entry(
            formulario,
            textvariable=self.rec_valor_var,
            width=18
        ).grid(
            row=1,
            column=0,
            padx=8,
            pady=(0, 12)
        )

        # SUBCATEGORIA

        ttk.Label(
            formulario,
            text="Subcategoria"
        ).grid(
            row=0,
            column=1,
            padx=8,
            pady=(10, 4),
            sticky="w"
        )

        self.rec_subcategoria_var = (
            tk.StringVar()
        )

        ttk.Combobox(
            formulario,
            textvariable=self.rec_subcategoria_var,
            values=SUBCATEGORIAS,
            width=18
        ).grid(
            row=1,
            column=1,
            padx=8,
            pady=(0, 12)
        )

        # DESCRIÇÃO

        ttk.Label(
            formulario,
            text="Descrição"
        ).grid(
            row=0,
            column=2,
            padx=8,
            pady=(10, 4),
            sticky="w"
        )

        self.rec_descricao_var = (
            tk.StringVar()
        )

        ttk.Entry(
            formulario,
            textvariable=self.rec_descricao_var,
            width=32
        ).grid(
            row=1,
            column=2,
            padx=8,
            pady=(0, 12)
        )

        # DIA

        ttk.Label(
            formulario,
            text="Dia do mês"
        ).grid(
            row=0,
            column=3,
            padx=8,
            pady=(10, 4),
            sticky="w"
        )

        self.rec_dia_var = (
            tk.StringVar()
        )

        ttk.Spinbox(
            formulario,
            from_=1,
            to=31,
            textvariable=self.rec_dia_var,
            width=8
        ).grid(
            row=1,
            column=3,
            padx=8,
            pady=(0, 12)
        )

        # BOTÕES

        frame_botoes = ttk.Frame(
            formulario
        )

        frame_botoes.grid(
            row=1,
            column=4,
            padx=8,
            pady=(0, 12)
        )

        self.botao_salvar_recorrencia = (
            ttk.Button(
                frame_botoes,
                text="Salvar recorrência",
                command=self.salvar_recorrencia
            )
        )

        self.botao_salvar_recorrencia.pack(
            side="left",
            padx=3
        )

        ttk.Button(
            frame_botoes,
            text="Limpar",
            command=self.limpar_recorrencia
        ).pack(
            side="left",
            padx=3
        )

        # GERAÇÃO MENSAL

        frame_geracao = ttk.LabelFrame(
            self.aba_recorrencias,
            text="Gerar gastos do mês"
        )

        frame_geracao.pack(
            fill="x",
            padx=20,
            pady=(0, 15)
        )

        ttk.Label(
            frame_geracao,
            text="Mês:"
        ).pack(
            side="left",
            padx=(12, 5),
            pady=12
        )

        self.rec_mes_var = tk.StringVar(
            value=datetime.now().strftime(
                "%m/%Y"
            )
        )

        ttk.Entry(
            frame_geracao,
            textvariable=self.rec_mes_var,
            width=10
        ).pack(
            side="left",
            padx=5,
            pady=12
        )

        ttk.Button(
            frame_geracao,
            text="Gerar gastos fixos do mês",
            command=self.gerar_recorrencias_mes
        ).pack(
            side="left",
            padx=8,
            pady=12
        )

        # BOTÕES DE GERENCIAMENTO

        frame_acoes = ttk.Frame(
            self.aba_recorrencias
        )

        frame_acoes.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        ttk.Button(
            frame_acoes,
            text="Editar selecionada",
            command=self.editar_recorrencia
        ).pack(
            side="left",
            padx=(0, 5)
        )

        ttk.Button(
            frame_acoes,
            text="Ativar / Desativar",
            command=self.alternar_recorrencia
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            frame_acoes,
            text="Excluir recorrência",
            command=self.excluir_recorrencia
        ).pack(
            side="left",
            padx=5
        )

        # TABELA

        frame_tabela = ttk.Frame(
            self.aba_recorrencias
        )

        frame_tabela.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        colunas = (
            "id",
            "valor",
            "subcategoria",
            "descricao",
            "dia",
            "status"
        )

        self.tabela_recorrencias = (
            ttk.Treeview(
                frame_tabela,
                columns=colunas,
                show="headings"
            )
        )

        titulos = {
            "id": "ID",
            "valor": "Valor",
            "subcategoria": "Subcategoria",
            "descricao": "Descrição",
            "dia": "Dia",
            "status": "Status"
        }

        larguras = {
            "id": 70,
            "valor": 160,
            "subcategoria": 220,
            "descricao": 400,
            "dia": 100,
            "status": 120
        }

        for coluna in colunas:

            self.tabela_recorrencias.heading(
                coluna,
                text=titulos[coluna],
                anchor="center"
            )

            self.tabela_recorrencias.column(
                coluna,
                width=larguras[coluna],
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            frame_tabela,
            orient="vertical",
            command=(
                self.tabela_recorrencias.yview
            )
        )

        self.tabela_recorrencias.configure(
            yscrollcommand=scrollbar.set
        )

        self.tabela_recorrencias.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tabela_recorrencias.bind(
            "<Double-1>",
            lambda event:
            self.editar_recorrencia()
        )


    # =====================================================
    # SALVAR RECORRÊNCIA
    # =====================================================

    def salvar_recorrencia(self):

        valor = converter_valor(
            self.rec_valor_var.get()
        )

        subcategoria = (
            self.rec_subcategoria_var
            .get()
            .strip()
        )

        descricao = (
            self.rec_descricao_var
            .get()
            .strip()
        )

        try:

            dia = int(
                self.rec_dia_var
                .get()
                .strip()
            )

        except ValueError:

            dia = 0

        if valor is None:

            messagebox.showerror(
                "Erro",
                "Digite um valor válido maior que zero."
            )

            return

        if not subcategoria:

            messagebox.showerror(
                "Erro",
                "Informe a subcategoria."
            )

            return

        if not descricao:

            messagebox.showerror(
                "Erro",
                "Informe uma descrição."
            )

            return

        if dia < 1 or dia > 31:

            messagebox.showerror(
                "Erro",
                "O dia deve estar entre 1 e 31."
            )

            return

        conexao = conectar_banco()
        cursor = conexao.cursor()

        if (
            self.id_recorrencia_em_edicao
            is None
        ):

            cursor.execute("""
                INSERT INTO recorrencias (
                    valor,
                    subcategoria,
                    descricao,
                    dia_vencimento,
                    ativa
                )
                VALUES (?, ?, ?, ?, 1)
            """, (
                valor,
                subcategoria,
                descricao,
                dia
            ))

            mensagem = (
                "Recorrência cadastrada com sucesso!"
            )

        else:

            cursor.execute("""
                UPDATE recorrencias
                SET
                    valor = ?,
                    subcategoria = ?,
                    descricao = ?,
                    dia_vencimento = ?
                WHERE id = ?
            """, (
                valor,
                subcategoria,
                descricao,
                dia,
                self.id_recorrencia_em_edicao
            ))

            mensagem = (
                "Recorrência atualizada com sucesso!"
            )

        conexao.commit()
        conexao.close()

        self.limpar_recorrencia()

        self.carregar_recorrencias()

        messagebox.showinfo(
            "Sucesso",
            mensagem
        )


    # =====================================================
    # LIMPAR RECORRÊNCIA
    # =====================================================

    def limpar_recorrencia(self):

        self.id_recorrencia_em_edicao = (
            None
        )

        self.rec_valor_var.set("")
        self.rec_subcategoria_var.set("")
        self.rec_descricao_var.set("")
        self.rec_dia_var.set("")

        self.botao_salvar_recorrencia.config(
            text="Salvar recorrência"
        )


    # =====================================================
    # CARREGAR RECORRÊNCIAS
    # =====================================================

    def carregar_recorrencias(self):

        for item in (
            self.tabela_recorrencias
            .get_children()
        ):

            self.tabela_recorrencias.delete(
                item
            )

        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                id,
                valor,
                subcategoria,
                descricao,
                dia_vencimento,
                ativa
            FROM recorrencias
            ORDER BY ativa DESC,
                     dia_vencimento,
                     descricao
        """)

        resultados = (
            cursor.fetchall()
        )

        conexao.close()

        for (
            id_recorrencia,
            valor,
            subcategoria,
            descricao,
            dia,
            ativa
        ) in resultados:

            status = (
                "Ativa"
                if ativa
                else "Inativa"
            )

            self.tabela_recorrencias.insert(
                "",
                "end",
                values=(
                    id_recorrencia,
                    formatar_moeda(
                        valor
                    ),
                    subcategoria,
                    descricao,
                    dia,
                    status
                )
            )


    # =====================================================
    # EDITAR RECORRÊNCIA
    # =====================================================

    def editar_recorrencia(self):

        selecionado = (
            self.tabela_recorrencias
            .selection()
        )

        if not selecionado:

            messagebox.showwarning(
                "Atenção",
                "Selecione uma recorrência."
            )

            return

        item = self.tabela_recorrencias.item(
            selecionado[0]
        )

        id_recorrencia = (
            item["values"][0]
        )

        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                valor,
                subcategoria,
                descricao,
                dia_vencimento
            FROM recorrencias
            WHERE id = ?
        """, (
            id_recorrencia,
        ))

        recorrencia = (
            cursor.fetchone()
        )

        conexao.close()

        if recorrencia is None:

            return

        (
            valor,
            subcategoria,
            descricao,
            dia
        ) = recorrencia

        self.id_recorrencia_em_edicao = (
            id_recorrencia
        )

        self.rec_valor_var.set(
            f"{valor:.2f}".replace(
                ".",
                ","
            )
        )

        self.rec_subcategoria_var.set(
            subcategoria
        )

        self.rec_descricao_var.set(
            descricao
        )

        self.rec_dia_var.set(
            str(dia)
        )

        self.botao_salvar_recorrencia.config(
            text="Salvar alterações"
        )


    # =====================================================
    # ATIVAR / DESATIVAR
    # =====================================================

    def alternar_recorrencia(self):

        selecionado = (
            self.tabela_recorrencias
            .selection()
        )

        if not selecionado:

            messagebox.showwarning(
                "Atenção",
                "Selecione uma recorrência."
            )

            return

        item = self.tabela_recorrencias.item(
            selecionado[0]
        )

        id_recorrencia = (
            item["values"][0]
        )

        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT ativa
            FROM recorrencias
            WHERE id = ?
        """, (
            id_recorrencia,
        ))

        resultado = (
            cursor.fetchone()
        )

        if resultado is None:

            conexao.close()
            return

        novo_status = (
            0
            if resultado[0]
            else 1
        )

        cursor.execute("""
            UPDATE recorrencias
            SET ativa = ?
            WHERE id = ?
        """, (
            novo_status,
            id_recorrencia
        ))

        conexao.commit()
        conexao.close()

        self.carregar_recorrencias()


    # =====================================================
    # EXCLUIR RECORRÊNCIA
    # =====================================================

    def excluir_recorrencia(self):

        selecionado = (
            self.tabela_recorrencias
            .selection()
        )

        if not selecionado:

            messagebox.showwarning(
                "Atenção",
                "Selecione uma recorrência."
            )

            return

        item = self.tabela_recorrencias.item(
            selecionado[0]
        )

        valores = item["values"]

        id_recorrencia = valores[0]
        descricao = valores[3]

        confirmar = messagebox.askyesno(
            "Excluir recorrência",
            (
                "Deseja excluir esta recorrência?\n\n"
                f"{descricao}\n\n"
                "As movimentações que já foram "
                "geradas continuarão no histórico."
            )
        )

        if not confirmar:

            return

        conexao = conectar_banco()
        cursor = conexao.cursor()

        # Apagamos primeiro os vínculos de controle.
        # As transações financeiras já geradas NÃO são apagadas.

        cursor.execute("""
            DELETE FROM recorrencias_geradas
            WHERE recorrencia_id = ?
        """, (
            id_recorrencia,
        ))

        cursor.execute("""
            DELETE FROM recorrencias
            WHERE id = ?
        """, (
            id_recorrencia,
        ))

        conexao.commit()
        conexao.close()

        self.limpar_recorrencia()

        self.carregar_recorrencias()

        messagebox.showinfo(
            "Sucesso",
            "Recorrência excluída."
        )


    # =====================================================
    # GERAR RECORRÊNCIAS DO MÊS
    # =====================================================

    def gerar_recorrencias_mes(self):

        mes = (
            self.rec_mes_var
            .get()
            .strip()
        )

        inicio, fim = intervalo_mes(
            mes
        )

        if inicio is None:

            messagebox.showerror(
                "Erro",
                "Use o mês no formato MM/AAAA."
            )

            return

        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                id,
                valor,
                subcategoria,
                descricao,
                dia_vencimento
            FROM recorrencias
            WHERE ativa = 1
            ORDER BY dia_vencimento
        """)

        recorrencias = (
            cursor.fetchall()
        )

        if not recorrencias:

            conexao.close()

            messagebox.showinfo(
                "Recorrências",
                "Não existem recorrências ativas."
            )

            return

        geradas = 0
        ignoradas = 0

        for (
            id_recorrencia,
            valor,
            subcategoria,
            descricao,
            dia
        ) in recorrencias:

            cursor.execute("""
                SELECT id
                FROM recorrencias_geradas
                WHERE recorrencia_id = ?
                AND mes_referencia = ?
            """, (
                id_recorrencia,
                mes
            ))

            ja_existe = (
                cursor.fetchone()
            )

            if ja_existe:

                ignoradas += 1
                continue

            data = data_recorrencia(
                mes,
                dia
            )

            if data is None:

                continue

            cursor.execute("""
                INSERT INTO transacoes (
                    tipo,
                    valor,
                    subcategoria,
                    descricao,
                    data
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                "Gasto Fixo",
                valor,
                subcategoria,
                descricao,
                data
            ))

            transacao_id = (
                cursor.lastrowid
            )

            cursor.execute("""
                INSERT INTO recorrencias_geradas (
                    recorrencia_id,
                    mes_referencia,
                    transacao_id
                )
                VALUES (?, ?, ?)
            """, (
                id_recorrencia,
                mes,
                transacao_id
            ))

            geradas += 1

        conexao.commit()
        conexao.close()

        self.atualizar_tudo()

        messagebox.showinfo(
            "Recorrências",
            (
                f"Movimentações geradas: {geradas}\n"
                f"Já existentes: {ignoradas}"
            )
        )


    # =====================================================
    # RESUMO MENSAL
    # =====================================================

    def criar_aba_resumo(self):

        topo = ttk.Frame(
            self.aba_resumo
        )

        topo.pack(
            fill="x",
            padx=20,
            pady=20
        )

        ttk.Label(
            topo,
            text="Mês:"
        ).pack(
            side="left"
        )

        self.mes_resumo_var = tk.StringVar(
            value=datetime.now().strftime(
                "%m/%Y"
            )
        )

        ttk.Entry(
            topo,
            textvariable=self.mes_resumo_var,
            width=10
        ).pack(
            side="left",
            padx=10
        )

        ttk.Button(
            topo,
            text="Atualizar resumo",
            command=self.atualizar_resumo
        ).pack(
            side="left"
        )

        frame_cards = ttk.Frame(
            self.aba_resumo
        )

        frame_cards.pack(
            fill="x",
            padx=20,
            pady=(0, 15)
        )

        for coluna in range(5):

            frame_cards.columnconfigure(
                coluna,
                weight=1
            )

        self.card_ganhos = (
            self.criar_card(
                frame_cards,
                "Ganhos",
                0
            )
        )

        self.card_fixos = (
            self.criar_card(
                frame_cards,
                "Gastos Fixos",
                1
            )
        )

        self.card_variaveis = (
            self.criar_card(
                frame_cards,
                "Gastos Variáveis",
                2
            )
        )

        self.card_gastos = (
            self.criar_card(
                frame_cards,
                "Total de Gastos",
                3
            )
        )

        self.card_balanco = (
            self.criar_card(
                frame_cards,
                "Balanço",
                4
            )
        )

        frame_subcategorias = (
            ttk.LabelFrame(
                self.aba_resumo,
                text="Gastos por subcategoria"
            )
        )

        frame_subcategorias.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        self.tabela_subcategorias = (
            ttk.Treeview(
                frame_subcategorias,
                columns=(
                    "subcategoria",
                    "total"
                ),
                show="headings"
            )
        )

        self.tabela_subcategorias.heading(
            "subcategoria",
            text="Subcategoria"
        )

        self.tabela_subcategorias.heading(
            "total",
            text="Total gasto"
        )

        self.tabela_subcategorias.column(
            "subcategoria",
            width=350
        )

        self.tabela_subcategorias.column(
            "total",
            width=180,
            anchor="e"
        )

        self.tabela_subcategorias.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )


    def criar_card(
        self,
        container,
        titulo,
        coluna
    ):

        card = ttk.LabelFrame(
            container
        )

        card.grid(
            row=0,
            column=coluna,
            sticky="nsew",
            padx=5,
            pady=5
        )

        ttk.Label(
            card,
            text=titulo,
            style="CardTitulo.TLabel"
        ).pack(
            anchor="w",
            padx=12,
            pady=(12, 2)
        )

        valor = ttk.Label(
            card,
            text="R$ 0,00",
            style="CardValor.TLabel"
        )

        valor.pack(
            anchor="w",
            padx=12,
            pady=(0, 15)
        )

        return valor


    def atualizar_resumo(self):

        mes = (
            self.mes_resumo_var
            .get()
            .strip()
        )

        inicio, fim = intervalo_mes(
            mes
        )

        if inicio is None:

            return

        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                tipo,
                SUM(valor)
            FROM transacoes
            WHERE data >= ?
            AND data < ?
            GROUP BY tipo
        """, (
            inicio,
            fim
        ))

        ganhos = 0
        fixos = 0
        variaveis = 0

        for (
            tipo,
            total
        ) in cursor.fetchall():

            total = total or 0

            if tipo == "Ganho":

                ganhos = total

            elif tipo == "Gasto Fixo":

                fixos = total

            elif tipo == "Gasto Variável":

                variaveis = total

        gastos = (
            fixos + variaveis
        )

        balanco = (
            ganhos - gastos
        )

        self.card_ganhos.config(
            text=formatar_moeda(
                ganhos
            )
        )

        self.card_fixos.config(
            text=formatar_moeda(
                fixos
            )
        )

        self.card_variaveis.config(
            text=formatar_moeda(
                variaveis
            )
        )

        self.card_gastos.config(
            text=formatar_moeda(
                gastos
            )
        )

        self.card_balanco.config(
            text=formatar_moeda(
                balanco
            )
        )

        for item in (
            self.tabela_subcategorias
            .get_children()
        ):

            self.tabela_subcategorias.delete(
                item
            )

        cursor.execute("""
            SELECT
                subcategoria,
                SUM(valor)
            FROM transacoes
            WHERE data >= ?
            AND data < ?
            AND tipo != 'Ganho'
            GROUP BY subcategoria
            ORDER BY SUM(valor) DESC
        """, (
            inicio,
            fim
        ))

        for (
            subcategoria,
            total
        ) in cursor.fetchall():

            self.tabela_subcategorias.insert(
                "",
                "end",
                values=(
                    subcategoria,
                    formatar_moeda(
                        total
                    )
                )
            )

        conexao.close()


    # =====================================================
    # CONTROLE ANUAL
    # =====================================================

    def criar_aba_anual(self):

        topo = ttk.Frame(
            self.aba_anual
        )

        topo.pack(
            fill="x",
            padx=20,
            pady=20
        )

        ttk.Label(
            topo,
            text="Ano:"
        ).pack(
            side="left"
        )

        self.ano_var = tk.StringVar(
            value=str(
                datetime.now().year
            )
        )

        ttk.Entry(
            topo,
            textvariable=self.ano_var,
            width=8
        ).pack(
            side="left",
            padx=10
        )

        ttk.Button(
            topo,
            text="Atualizar",
            command=self.atualizar_controle_anual
        ).pack(
            side="left"
        )

        colunas = (
            "mes",
            "ganhos",
            "fixos",
            "variaveis",
            "gastos",
            "balanco"
        )

        self.tabela_anual = (
            ttk.Treeview(
                self.aba_anual,
                columns=colunas,
                show="headings"
            )
        )

        titulos = {
            "mes": "Mês",
            "ganhos": "Ganhos",
            "fixos": "Gastos Fixos",
            "variaveis": "Gastos Variáveis",
            "gastos": "Total de Gastos",
            "balanco": "Balanço"
        }

        for coluna in colunas:

            self.tabela_anual.heading(
                coluna,
                text=titulos[coluna]
            )

        self.tabela_anual.column(
            "mes",
            width=130
        )

        for coluna in (
            "ganhos",
            "fixos",
            "variaveis",
            "gastos",
            "balanco"
        ):

            self.tabela_anual.column(
                coluna,
                width=155,
                anchor="e"
            )

        self.tabela_anual.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )


    def atualizar_controle_anual(self):

        try:

            ano = int(
                self.ano_var
                .get()
                .strip()
            )

        except ValueError:

            return

        nomes_meses = [
            "Janeiro",
            "Fevereiro",
            "Março",
            "Abril",
            "Maio",
            "Junho",
            "Julho",
            "Agosto",
            "Setembro",
            "Outubro",
            "Novembro",
            "Dezembro"
        ]

        for item in (
            self.tabela_anual
            .get_children()
        ):

            self.tabela_anual.delete(
                item
            )

        conexao = conectar_banco()
        cursor = conexao.cursor()

        for numero_mes in range(
            1,
            13
        ):

            inicio = datetime(
                ano,
                numero_mes,
                1
            )

            if numero_mes == 12:

                fim = datetime(
                    ano + 1,
                    1,
                    1
                )

            else:

                fim = datetime(
                    ano,
                    numero_mes + 1,
                    1
                )

            cursor.execute("""
                SELECT
                    tipo,
                    SUM(valor)
                FROM transacoes
                WHERE data >= ?
                AND data < ?
                GROUP BY tipo
            """, (
                inicio.strftime(
                    "%Y-%m-%d"
                ),
                fim.strftime(
                    "%Y-%m-%d"
                )
            ))

            ganhos = 0
            fixos = 0
            variaveis = 0

            for (
                tipo,
                total
            ) in cursor.fetchall():

                total = total or 0

                if tipo == "Ganho":

                    ganhos = total

                elif tipo == "Gasto Fixo":

                    fixos = total

                elif tipo == "Gasto Variável":

                    variaveis = total

            gastos = (
                fixos + variaveis
            )

            balanco = (
                ganhos - gastos
            )

            self.tabela_anual.insert(
                "",
                "end",
                values=(
                    nomes_meses[
                        numero_mes - 1
                    ],
                    formatar_moeda(
                        ganhos
                    ),
                    formatar_moeda(
                        fixos
                    ),
                    formatar_moeda(
                        variaveis
                    ),
                    formatar_moeda(
                        gastos
                    ),
                    formatar_moeda(
                        balanco
                    )
                )
            )

        conexao.close()


    # =====================================================
    # ATUALIZAR TUDO
    # =====================================================

    def atualizar_tudo(self):

        self.carregar_movimentacoes()

        self.atualizar_aba_tipo(
            "Gasto Fixo"
        )

        self.atualizar_aba_tipo(
            "Gasto Variável"
        )

        self.atualizar_aba_tipo(
            "Ganho"
        )

        self.carregar_recorrencias()

        self.atualizar_resumo()

        self.atualizar_controle_anual()


# =========================================================
# INICIAR APLICAÇÃO
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = FinanceApp(
        root
    )

    root.mainloop()