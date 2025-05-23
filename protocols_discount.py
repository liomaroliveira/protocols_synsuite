import sys
import json
import requests
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout,
    QWidget, QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QFileDialog
)
from PySide6.QtCore import Qt, QTimer


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


class MainWindow(QMainWindow):
    def __init__(self, usuario, senha):
        super().__init__()
        self.setWindowTitle("Extrator de Protocolos SynSuite")
        self.usuario = usuario
        self.senha = senha
        self.protocol_titles = []

        self.label = QLabel("Protocolos extraídos:")
        self.table = QTableWidget()
        self.button_export = QPushButton("Exportar para Excel")
        self.button_export.clicked.connect(self.export_to_excel)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.table)
        layout.addWidget(self.button_export)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

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

        for start in range(0, 10000, 25):
            payload_data = {
                "sEcho": 1,
                "iColumns": 7,
                "sColumns": "",
                "iDisplayStart": start,
                "iDisplayLength": 25,
                "mDataProp_0": "Assignment.id",
                "mDataProp_1": "Assignment.title",
                "mDataProp_2": "Requestor.name",
                "mDataProp_3": "Assignment.progress",
                "mDataProp_4": "Assignment.final_date",
                "mDataProp_5": "Assignment.assignment_origin",
                "mDataProp_6": "AssignmentIncident.protocol",
                "datatable": json.dumps({
                    "fields": [
                        "Assignment.id", "Assignment.title", "Requestor.name",
                        "Assignment.progress", "Assignment.final_date",
                        "Assignment.priority", "Assignment.assignment_origin",
                        "Requestor.name_2", "Assignment.description",
                        "Assignment.assignment_type", "Assignment.date_situation",
                        "Assignment.has_children", "Assignment.has_product_acquisition_requests",
                        "Assignment.blockTask", "Assignment.responsible_id",
                        "Assignment.type_progress", "Assignment.client_projects",
                        "Assignment.corresponding_parent_id", "Assignment.time_remaining",
                        "Assignment.days_remaining", "Assignment.weight",
                        "AssignmentIncident.team_manager_id", "AssignmentIncident.incident_status_id",
                        "AssignmentIncident.protocol", "AssignmentIncident.client_id",
                        "AssignmentIncidentPerson.name", "AssignmentIncidentPerson.name_2",
                        "Assignment.info_path", "Assignment.lawsuit_id", "Instance.title",
                        "Assignment.instance_root_title", "Assignment.parentOriginatesFromCrm",
                        "Assignment.is_omnichannel", "IncidentType.solicitation_type"
                    ],
                    "searchFields": [
                        "Assignment.description", "Assignment.info_path", "Requestor.name_2",
                        "Responsible.name_2", "Responsible.name", "Client.name_2", "Client.name",
                        "Person.name_2", "Person.name", "Instance.title", "Assignment.instance_root_title"
                    ],
                    "conditions": {
                        "Assignment.progress <": 100,
                        "Assignment.task": 1,
                        "Assignment.deleted": False,
                        "Assignment.in_execution": None,
                        "Assignment.assignment_origin NOT": [96, 95, 30, 502],
                        "Assignment.assignment_origin": 5
                    }
                })
            }

            response = session.post(DATA_URL, headers=headers_data, data=payload_data)
            data = response.json()

            if not data.get("aaData"):
                break

            for item in data.get("aaData", []):
                try:
                    title = item["Assignment"]["title"]
                    protocol = item["AssignmentIncident"].get("protocol", "")
                    requester = item["Requestor"].get("name", "")
                    final_date = item["Assignment"].get("final_date", "")
                    self.protocol_titles.append([
                        protocol, title, requester, final_date
                    ])
                except KeyError as e:
                    print(f"[!] Campo ausente: {e}")
                    continue

        if not self.protocol_titles:
            QMessageBox.information(self, "Resultado", "Nenhum protocolo encontrado.")
            return

        self.populate_table()

    def populate_table(self):
        headers = ["Protocolo", "Título", "Solicitante", "Data Final"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(self.protocol_titles))

        for row_idx, row_data in enumerate(self.protocol_titles):
            for col_idx, value in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        self.table.resizeColumnsToContents()

    def export_to_excel(self):
        df = pd.DataFrame(self.protocol_titles, columns=["Protocolo", "Título", "Solicitante", "Data Final"])
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", "protocolos_synsuite.xlsx", "Excel Files (*.xlsx)")
        if filename:
            df.to_excel(filename, index=False)
            QMessageBox.information(self, "Sucesso", f"Arquivo salvo como: {filename}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_dialog = LoginDialog()
    if login_dialog.exec():
        usuario, senha = login_dialog.get_credentials()
        window = MainWindow(usuario, senha)
        window.show()
        sys.exit(app.exec())
