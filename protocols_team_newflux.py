import sys
import requests
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QTableWidget, QTableWidgetItem,
    QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QDialog, QTextEdit,
    QMessageBox
)
from PySide6.QtCore import Qt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# --- Janela Modal de Login ---
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login SynSuite")
        self.setModal(True)
        self.resize(300, 150)

        self.user_label = QLabel("Usuário:")
        self.user_input = QLineEdit()
        self.pass_label = QLabel("Senha:")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.user_label)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_label)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.login_btn)
        self.setLayout(layout)

        # --- Dados de login salvos para testes (REMOVA para produção) ---
        self.user_input.setText("SEU_USUARIO_AQUI")
        self.pass_input.setText("SUA_SENHA_AQUI")
        # -------------------------------------------------------------------

    def get_credentials(self):
        return self.user_input.text(), self.pass_input.text()

# --- Janela principal ---
class MainWindow(QMainWindow):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Extrator SynSuite - Protocolos com DESCONTO")
        self.resize(900, 600)

        # Layout principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Tabela para exibir dados
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Protocolo", "Título", "Solicitante", "Progresso", "Prazo", "Histórico Conexão"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table)

        # Botões de exportação
        btn_layout = QHBoxLayout()
        self.export_xlsx_btn = QPushButton("Exportar XLSX")
        self.export_csv_btn = QPushButton("Exportar CSV")
        self.export_pdf_btn = QPushButton("Exportar PDF")
        btn_layout.addWidget(self.export_xlsx_btn)
        btn_layout.addWidget(self.export_csv_btn)
        btn_layout.addWidget(self.export_pdf_btn)
        main_layout.addLayout(btn_layout)

        # Área de logs simples
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)

        # Conectar botões a funções
        self.export_xlsx_btn.clicked.connect(self.export_xlsx)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_pdf_btn.clicked.connect(self.export_pdf)

        # Variável para guardar os dados coletados
        self.df = pd.DataFrame()

        # Rodar a coleta logo após abrir
        self.collect_data()

    def log(self, msg):
        self.log_text.append(msg)
        print(msg)  # Também printa no terminal para debug

    def collect_data(self):
        self.log("Iniciando coleta de protocolos com 'DESCONTO' no título...")

        # Aqui você adapta a URL e os headers para a API ou site do SynSuite.
        # Exemplo fictício:
        url_protocolos = "https://synsuite.teninternet.com.br/api/protocols"  # troque pela real
        headers = {
            # Coloque headers e cookies necessários aqui, se precisar:
            "User-Agent": "Mozilla/5.0",
            # "Authorization": "Bearer TOKEN_AQUI"  # se usar token
        }

        try:
            response = self.session.get(url_protocolos, headers=headers)
            response.raise_for_status()
            protocolos = response.json()

            # Filtrar só os que têm 'DESCONTO' no título
            protocolos_desconto = [
                p for p in protocolos if 'DESCONTO' in p.get('titulo', '').upper()
            ]
            self.log(f"Protocolos encontrados: {len(protocolos)}")
            self.log(f"Protocolos com 'DESCONTO': {len(protocolos_desconto)}")

            # Agora, coletar histórico de conexão de cada protocolo
            dados = []
            for p in protocolos_desconto:
                protocolo_id = p.get('id')
                titulo = p.get('titulo')
                solicitante = p.get('solicitante', 'N/A')
                progresso = p.get('progresso', 'N/A')
                prazo = p.get('prazo', 'N/A')

                # Exemplo de url para histórico do protocolo
                url_hist = f"https://synsuite.teninternet.com.br/api/protocols/{protocolo_id}/history"

                hist_response = self.session.get(url_hist, headers=headers)
                hist_response.raise_for_status()
                history = hist_response.json()

                # Extrair resumo do histórico, por exemplo, concatenar eventos
                hist_text = "; ".join([f"{h['data']} - {h['descricao']}" for h in history])

                dados.append({
                    "Protocolo": protocolo_id,
                    "Título": titulo,
                    "Solicitante": solicitante,
                    "Progresso": progresso,
                    "Prazo": prazo,
                    "Histórico Conexão": hist_text
                })
                self.log(f"Coletado histórico para protocolo {protocolo_id}")

            self.df = pd.DataFrame(dados)

            # Preencher tabela
            self.populate_table()

        except Exception as e:
            self.log(f"Erro na coleta: {e}")
            QMessageBox.critical(self, "Erro", f"Erro na coleta: {e}")

    def populate_table(self):
        self.table.setRowCount(len(self.df))
        for i, row in self.df.iterrows():
            for j, col in enumerate(self.df.columns):
                item = QTableWidgetItem(str(row[col]))
                if j == 0:  # Protocolo
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # Não editável
                self.table.setItem(i, j, item)
        self.log("Tabela atualizada com os dados coletados.")

    def export_xlsx(self):
        try:
            self.df.to_excel("protocolos_desconto.xlsx", index=False)
            self.log("Exportado arquivo protocolos_desconto.xlsx com sucesso.")
            QMessageBox.information(self, "Exportação XLSX", "Arquivo XLSX exportado com sucesso!")
        except Exception as e:
            self.log(f"Erro ao exportar XLSX: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar XLSX: {e}")

    def export_csv(self):
        try:
            self.df.to_csv("protocolos_desconto.csv", index=False)
            self.log("Exportado arquivo protocolos_desconto.csv com sucesso.")
            QMessageBox.information(self, "Exportação CSV", "Arquivo CSV exportado com sucesso!")
        except Exception as e:
            self.log(f"Erro ao exportar CSV: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {e}")

    def export_pdf(self):
        try:
            c = canvas.Canvas("protocolos_desconto.pdf", pagesize=letter)
            width, height = letter
            text = c.beginText(40, height - 40)
            text.setFont("Helvetica", 10)
            for i, row in self.df.iterrows():
                line = f"Protocolo: {row['Protocolo']} | Título: {row['Título']} | Solicitante: {row['Solicitante']} | Progresso: {row['Progresso']} | Prazo: {row['Prazo']}"
                text.textLine(line)
                # Histórico pode ser grande, então quebra por 90 chars
                hist = row['Histórico Conexão']
                for k in range(0, len(hist), 90):
                    text.textLine("   " + hist[k:k+90])
                text.textLine("-" * 100)
                if text.getY() < 60:
                    c.drawText(text)
                    c.showPage()
                    text = c.beginText(40, height - 40)
                    text.setFont("Helvetica", 10)
            c.drawText(text)
            c.save()

            self.log("Exportado arquivo protocolos_desconto.pdf com sucesso.")
            QMessageBox.information(self, "Exportação PDF", "Arquivo PDF exportado com sucesso!")
        except Exception as e:
            self.log(f"Erro ao exportar PDF: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {e}")

def main():
    app = QApplication(sys.argv)

    # --- Janela de Login ---
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.Accepted:
        user, password = login_dialog.get_credentials()
        if not user or not password:
            QMessageBox.critical(None, "Erro", "Usuário e senha são obrigatórios.")
            sys.exit(1)

        # Criar sessão para manter cookies, etc
        session = requests.Session()

        # Aqui você adapta o login à API ou sistema real SynSuite
        login_url = "https://synsuite.teninternet.com.br/api/login"
        try:
            resp = session.post(login_url, json={"username": user, "password": password})
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success", False):
                QMessageBox.critical(None, "Erro", "Login falhou. Verifique credenciais.")
                sys.exit(1)
        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Erro no login: {e}")
            sys.exit(1)

        # Abrir janela principal com sessão autenticada
        main_win = MainWindow(session)
        main_win.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
