import sys
import json
import requests
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout,
    QWidget, QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QFileDialog, QProgressDialog,
    QTextEdit, QHBoxLayout, QScrollArea, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextDocument

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login SynSuite")
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        layout = QFormLayout()
        layout.addRow("Usuário:", self.user_input)
        layout.addRow("Senha:", self.pass_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_credentials(self):
        return self.user_input.text(), self.pass_input.text()


class ConnectionHistoryDialog(QDialog):
    def __init__(self, history_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Histórico de Conexão")
        layout = QVBoxLayout(self)

        # Create table
        table = QTableWidget()
        headers = ["Protocolo", "Título", "Solicitante", "Data Final"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(history_data))

        for row_idx, record in enumerate(history_data):
            for col_idx, value in enumerate(record[:4]):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.resizeColumnsToContents()
        layout.addWidget(table)

        # Add close button
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class MainWindow(QMainWindow):
    def __init__(self, usuario, senha):
        super().__init__()
        self.setWindowTitle("Solicitações de Desconto - SynSuite")
        self.usuario = usuario
        self.senha = senha
        self.protocol_data = []

        # --- Tela da tabela ---
        self.label = QLabel("Protocolos da equipe:")
        self.table = QTableWidget()
        self.button_export = QPushButton("Exportar para Excel")
        self.button_analyze = QPushButton("Analisar protocolo")

        self.button_export.clicked.connect(self.export_to_excel)
        self.button_analyze.clicked.connect(self.show_analysis_screen)

        layout_table = QVBoxLayout()
        layout_table.addWidget(self.label)
        layout_table.addWidget(self.table)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.button_export)
        button_layout.addWidget(self.button_analyze)
        layout_table.addLayout(button_layout)

        self.table_container = QWidget()
        self.table_container.setLayout(layout_table)

        # --- Tela de análise ---
        self.analysis_container = QWidget()
        self.analysis_container.setVisible(False)
        self.init_analysis_ui()

        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.table_container)
        main_layout.addWidget(self.analysis_container)

        central = QWidget()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        self.showMaximized()
        QTimer.singleShot(100, self.extract_protocols)

    def extract_protocols(self):
        LOGIN_URL = "https://synsuite.teninternet.com.br/users/login"
        DATA_URL = "https://synsuite.teninternet.com.br/assignments/getDataTable"

        session = requests.Session()
        login_payload = {
            "data[User][login]": self.usuario,
            "data[User][password2]": self.senha
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_URL
        }

        login_response = session.post(LOGIN_URL, data=login_payload, headers=headers)
        if "Assignments" not in login_response.text:
            QMessageBox.critical(self, "Erro", "Login falhou. Verifique as credenciais.")
            self.close()
            return

        headers_data = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://synsuite.teninternet.com.br/assignments"
        }

        fields = [
            "Assignment.id", "Assignment.title", "Responsible.name", "Assignment.progress",
            "Assignment.final_date", "Assignment.assignment_origin",
            "Requestor.name_2", "Assignment.description", "Assignment.assignment_type",
            "Assignment.date_situation", "Assignment.has_children",
            "Assignment.has_product_acquisition_requests", "Assignment.blockTask",
            "Assignment.responsible_id", "Assignment.client_projects", "Assignment.lawsuit_id",
            "Assignment.time_remaining", "Assignment.days_remaining", "Assignment.weight",
            "Assignment.in_execution", "Requestor.name", "AssignmentIncident.team_manager_id",
            "AssignmentIncident.incident_status_id", "AssignmentIncident.protocol",
            "AssignmentIncident.client_id", "Responsible.name_2", "Team.title",
            "Assignment.is_omnichannel", "IncidentType.solicitation_type"
        ]

        search_fields = [
            "Assignment.description", "Team.title", "Requestor.name_2", "Responsible.name_2",
            "Responsible.name", "Client.name_2", "Client.name", "Person.name_2", "Person.name"
        ]

        base_conditions = {
            "Assignment.task": 1,
            "Assignment.deleted": False,
            "Assignment.assignment_origin": 5,
            "Assignment.progress <": 100,
            "filter_team": 1
        }

        payload_teste = {
            "sEcho": 1,
            "iColumns": 7,
            "sColumns": "",
            "iDisplayStart": 0,
            "iDisplayLength": 1,
            "mDataProp_0": "Assignment.id",
            "mDataProp_1": "Assignment.title",
            "mDataProp_2": "Responsible.name",
            "mDataProp_3": "Assignment.progress",
            "mDataProp_4": "Assignment.final_date",
            "mDataProp_5": "Assignment.assignment_origin",
            "mDataProp_6": "AssignmentIncident.protocol",
            "datatable": json.dumps({
                "fields": fields,
                "searchFields": search_fields,
                "conditions": base_conditions
            })
        }

        res_teste = session.post(DATA_URL, headers=headers_data, data=payload_teste)
        res_json = res_teste.json()
        total_registros = int(res_json.get("iTotalDisplayRecords", 0))

        passo = 25
        total_passos = (total_registros + passo - 1) // passo

        progress_dialog = QProgressDialog("Carregando protocolos da equipe...", "Cancelar", 0, total_passos, self)
        progress_dialog.setWindowTitle("Aguarde")
        progress_dialog.setWindowModality(Qt.ApplicationModal)
        progress_dialog.setAutoClose(True)
        progress_dialog.show()

        for i, start in enumerate(range(0, total_registros, passo)):
            payload_data = payload_teste.copy()
            payload_data["iDisplayStart"] = start
            payload_data["iDisplayLength"] = passo

            response = session.post(DATA_URL, headers=headers_data, data=payload_data)
            data = response.json()

            if not data.get("aaData"):
                break

            for item in data.get("aaData", []):
                try:
                    title = item["Assignment"].get("title", "")
                    parts = title.split(" - ", 2)
                    if len(parts) < 2 or "DESCONTO" not in parts[1].upper():
                        continue

                    protocol = item["AssignmentIncident"].get("protocol", "")
                    requester = item["Requestor"].get("name", "")
                    final_date = item["Assignment"].get("final_date", "")
                    description = item["Assignment"].get("description", "")
                    self.protocol_data.append([protocol, title, requester, final_date, description])
                except KeyError as e:
                    print(f"[!] Campo ausente: {e}")
                    continue

            progress_dialog.setValue(i + 1)
            QApplication.processEvents()

        if not self.protocol_data:
            QMessageBox.information(self, "Resultado", "Nenhum protocolo encontrado com critério 'DESCONTO'.")
            return

        self.protocol_data.sort(key=lambda x: x[0])
        self.populate_table()

    def populate_table(self):
        headers = ["Protocolo", "Título", "Solicitante", "Data Final", "Descrição"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.table.setRowCount(len(self.protocol_data))

        for row_idx, row_data in enumerate(self.protocol_data):
            for col_idx, value in enumerate(row_data):
                if col_idx == 4:  # coluna "Descrição"
                    label = QLabel()
                    label.setTextFormat(Qt.RichText)
                    label.setWordWrap(True)
                    label.setText(value.replace('\n', '<br>'))
                    label.adjustSize()  # força ajustar tamanho interno

                    self.table.setCellWidget(row_idx, col_idx, label)

                    # Ajusta a altura da linha para mostrar todo conteúdo do QLabel
                    height = label.sizeHint().height()
                    self.table.setRowHeight(row_idx, max(height, 30))  # mínimo 30 px
                else:
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    self.table.setItem(row_idx, col_idx, item)

        self.table.resizeColumnsToContents()


    def export_to_excel(self):
        df = pd.DataFrame(self.protocol_data, columns=["Protocolo", "Título", "Solicitante", "Data Final", "Descrição"])
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", "protocolos_synsuite.xlsx", "Excel Files (*.xlsx)")
        if filename:
            df.to_excel(filename, index=False)
            QMessageBox.information(self, "Sucesso", f"Arquivo salvo como: {filename}")

    def init_analysis_ui(self):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)

        self.scroll.setWidget(self.scroll_content)

        # Buttons layout
        button_layout = QHBoxLayout()
        buttons = [
            "Exportar para PDF",
            "Exportar para Excel (XLSX)",
            "Analisar histórico de conexão",
            "Calcular desconto",
        ]
        for name in buttons:
            btn = QPushButton(name)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            if name == "Analisar histórico de conexão":
                btn.clicked.connect(self.show_connection_history)
            button_layout.addWidget(btn)

        self.button_back = QPushButton("Voltar")
        self.button_back.clicked.connect(self.show_table_screen)
        button_layout.addWidget(self.button_back)

        layout = QVBoxLayout()
        layout.addWidget(self.scroll)
        layout.addLayout(button_layout)

        self.analysis_container.setLayout(layout)

    def show_analysis_screen(self):
        # Clean previous
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Store checkboxes with protocol data
        self.checkboxes = []
        for protocol in self.protocol_data:
            box = QWidget()
            box_layout = QVBoxLayout(box)
            box.setStyleSheet("border: 1px solid gray; padding: 10px; margin: 5px; border-radius: 5px;")

            checkbox = QCheckBox(f"Selecionar protocolo {protocol[0]}")
            self.checkboxes.append((checkbox, box, protocol))
            checkbox.stateChanged.connect(self.toggle_selection_effect)
            box_layout.addWidget(checkbox)

            for label, content in zip(["Protocolo", "Título", "Solicitante", "Data Final"], protocol[:4]):
                box_layout.addWidget(QLabel(f"<b>{label}:</b> {content}"))

            descricao = QLabel()
            descricao.setTextFormat(Qt.RichText)
            descricao.setWordWrap(True)
            descricao.setText(protocol[4].replace('\n', '<br>'))
            box_layout.addWidget(QLabel("<b>Descrição:</b>"))
            box_layout.addWidget(descricao)

            self.scroll_layout.addWidget(box)

        self.table_container.setVisible(False)
        self.analysis_container.setVisible(True)

    def show_connection_history(self):
        # Gather selected protocols
        selected = [protocol for (cb, widget, protocol) in self.checkboxes if cb.isChecked()]
        if not selected:
            QMessageBox.information(self, "Histórico de Conexão", "Nenhum protocolo selecionado.")
            return

        dialog = ConnectionHistoryDialog(selected, self)
        dialog.exec()

    def show_table_screen(self):
        self.analysis_container.setVisible(False)
        self.table_container.setVisible(True)

    def toggle_selection_effect(self, state):
        checkbox = self.sender()
        for cb, widget, _ in self.checkboxes:
            if cb is checkbox:
                if state == Qt.Checked:
                    widget.setStyleSheet("background-color: #d0f0c0; border: 1px solid gray; padding: 10px; margin: 5px; border-radius: 5px;")
                else:
                    widget.setStyleSheet("border: 1px solid gray; padding: 10px; margin: 5px; border-radius: 5px;")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    login = LoginDialog()
    if login.exec() == QDialog.Accepted:
        usuario, senha = login.get_credentials()
        window = MainWindow(usuario, senha)
        window.show()
        sys.exit(app.exec())
    else:
        print("Login cancelado pelo usuário.")
        sys.exit()
