import sys
import json
import requests
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout,
    QWidget, QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QFileDialog, QProgressDialog,
    QHBoxLayout, QScrollArea, QSizePolicy, QCheckBox, QDateEdit
)
from PySide6.QtCore import Qt, QTimer, QDate

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
    def __init__(self, session, tag_ids, parent=None):
        super().__init__(parent)
        self.session = session
        self.tag_ids = tag_ids
        self.setWindowTitle("Histórico de Conexão")
        self.resize(800, 500)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.date_from = QDateEdit(calendarPopup=True)
        self.date_to = QDateEdit(calendarPopup=True)
        today = QDate.currentDate()
        self.date_to.setDate(today)
        self.date_from.setDate(today.addDays(-7))
        form.addRow("Data Início:", self.date_from)
        form.addRow("Data Fim:", self.date_to)
        layout.addLayout(form)
        btn_load = QPushButton("Carregar Histórico")
        btn_load.clicked.connect(self.load_history)
        layout.addWidget(btn_load)
        self.table = QTableWidget()
        self.table.setShowGrid(True)
        layout.addWidget(self.table)
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def load_history(self):
        start = self.date_from.date().toString('yyyy-MM-dd')
        end = self.date_to.date().toString('yyyy-MM-dd')
        combined = []
        for tag_id in self.tag_ids:
            hist_url = (
                f"https://synsuite.teninternet.com.br:45701/api/v1/Projects/Attendance/"
                f"Connections/GetConsumptionHistory?contractServiceTagId={tag_id}&startDate={start}&endDate={end}"
            )
            resp = self.session.get(hist_url)
            try:
                hist_json = resp.json()
                records = hist_json.get('historyData', [])
            except Exception:
                records = []
            combined.extend(records)
        if not combined:
            QMessageBox.information(self, "Histórico de Conexão", "Nenhum dado disponível para o período informado.")
            return
        headers = list(combined[0].keys())
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(combined))
        for i, rec in enumerate(combined):
            for j, key in enumerate(headers):
                val = rec.get(key, '')
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table.setItem(i, j, item)
        self.table.resizeColumnsToContents()

class MainWindow(QMainWindow):
    def __init__(self, usuario, senha):
        super().__init__()
        self.setWindowTitle("Solicitações de Desconto - SynSuite")
        self.usuario = usuario
        self.senha = senha
        self.protocol_data = []
        self.session = None
        # Table screen
        self.table = QTableWidget()
        btn_export = QPushButton("Exportar para Excel")
        btn_analyze = QPushButton("Analisar protocolo")
        btn_export.clicked.connect(self.export_to_excel)
        btn_analyze.clicked.connect(self.show_analysis_screen)
        lt = QVBoxLayout()
        lt.addWidget(QLabel("Protocolos da equipe:"))
        lt.addWidget(self.table)
        hb = QHBoxLayout()
        hb.addWidget(btn_export)
        hb.addWidget(btn_analyze)
        lt.addLayout(hb)
        self.table_container = QWidget()
        self.table_container.setLayout(lt)
        # Analysis screen
        self.analysis_container = QWidget()
        self.analysis_container.setVisible(False)
        self.init_analysis_ui()
        ml = QVBoxLayout()
        ml.addWidget(self.table_container)
        ml.addWidget(self.analysis_container)
        ce = QWidget()
        ce.setLayout(ml)
        self.setCentralWidget(ce)
        self.showMaximized()
        QTimer.singleShot(100, self.extract_protocols)

    def extract_protocols(self):
        LOGIN_URL = "https://synsuite.teninternet.com.br/users/login"
        DATA_URL = "https://synsuite.teninternet.com.br/assignments/getDataTable"
        self.session = requests.Session()
        payload = {"data[User][login]": self.usuario, "data[User][password2]": self.senha}
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Referer": LOGIN_URL}
        r = self.session.post(LOGIN_URL, data=payload, headers=headers)
        if "Assignments" not in r.text:
            QMessageBox.critical(self, "Erro", "Login falhou. Verifique as credenciais.")
            self.close(); return
        headers_d = {"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest", "Referer": "https://synsuite.teninternet.com.br/assignments"}
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
        base = {"Assignment.task":1, "Assignment.deleted":False, "Assignment.assignment_origin":5, "Assignment.progress <":100, "filter_team":1}
        base_payload = {"sEcho":1, "iColumns":7, "sColumns":"", "iDisplayStart":0, "iDisplayLength":1, "mDataProp_0":"Assignment.id","mDataProp_1":"Assignment.title","mDataProp_2":"Responsible.name","mDataProp_3":"Assignment.progress","mDataProp_4":"Assignment.final_date","mDataProp_5":"Assignment.assignment_origin","mDataProp_6":"AssignmentIncident.protocol","datatable": json.dumps({"fields":fields,"searchFields":search_fields,"conditions":base})}
        total = self.session.post(DATA_URL, headers=headers_d, data=base_payload).json().get("iTotalDisplayRecords",0)
        passo=25; steps=(total+passo-1)//passo
        dlg = QProgressDialog("Carregando protocolos da equipe...","Cancelar",0,steps,self)
        dlg.setWindowTitle("Aguarde...")
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.show()
        for i,start in enumerate(range(0,total,passo)):
            pl = base_payload.copy(); pl["iDisplayStart"]=start; pl["iDisplayLength"]=passo
            data = self.session.post(DATA_URL,headers=headers_d,data=pl).json().get("aaData",[])
            for it in data:
                title=it["Assignment"].get("title","")
                if "DESCONTO" not in title.upper(): continue
                aid=it["Assignment"].get("id","")
                protocol=it["AssignmentIncident"].get("protocol",
"")
                requester=it["Requestor"].get("name","")
                final_date=it["Assignment"].get("final_date","")
                desc=it["Assignment"].get("description","")
                self.protocol_data.append([aid,protocol,title,requester,final_date,desc])
            dlg.setValue(i+1); QApplication.processEvents()
        if not self.protocol_data:
            QMessageBox.information(self,"Resultado","Nenhum protocolo encontrado.")
        else:
            self.protocol_data.sort(key=lambda x: x[0])
            self.populate_table()

    def populate_table(self):
        hdrs = ["ID", "Protocolo", "Título", "Solicitante", "Data Final", "Descrição"]
        self.table.setColumnCount(len(hdrs))
        self.table.setHorizontalHeaderLabels(hdrs)
        self.table.setRowCount(len(self.protocol_data))
        for i, row in enumerate(self.protocol_data):
            for j, val in enumerate(row):
                if j == 5:
                    lbl = QLabel()
                    lbl.setTextFormat(Qt.RichText)
                    lbl.setWordWrap(True)
                    lbl.setText(val.replace("\n", "<br>"))
                    self.table.setCellWidget(i, j, lbl)
                    height = lbl.sizeHint().height()
                    self.table.setRowHeight(i, max(height, 30))
                else:
                    it = QTableWidgetItem(str(val))
                    it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                    it.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                    self.table.setItem(i, j, it)
        self.table.resizeColumnsToContents()

    def init_analysis_ui(self):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        cont = QWidget()
        self.scroll_layout = QVBoxLayout(cont)
        self.scroll.setWidget(cont)
        btn_layout = QHBoxLayout()
        for name in [
            "Exportar para PDF", "Exportar para Excel (XLSX)",
            "Analisar histórico de conexão", "Calcular desconto"
        ]:
            b = QPushButton(name)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            if name == "Analisar histórico de conexão":
                b.clicked.connect(self.show_connection_history)
            btn_layout.addWidget(b)
        back = QPushButton("Voltar")
        back.clicked.connect(self.show_table_screen)
        btn_layout.addWidget(back)
        lay = QVBoxLayout(self.analysis_container)
        lay.addWidget(self.scroll)
        lay.addLayout(btn_layout)

    def show_analysis_screen(self):
        # Limpa itens anteriores
        for i in reversed(range(self.scroll_layout.count())):
            w = self.scroll_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self.checkboxes = []
        # Adiciona cada protocolo com descrição e estilo de grade
        for row in self.protocol_data:
            box = QWidget()
            # borda e espaçamento inicial
            default_style = "border:1px solid #ccc; border-radius:5px; padding:5px; margin-bottom:10px;"
            selected_style = "background-color:#474747; color:white; border:1px solid #ccc; border-radius:5px; padding:5px; margin-bottom:10px;"
            box.setStyleSheet(default_style)
            bl = QVBoxLayout(box)
            cb = QCheckBox("Selecionar")
            self.checkboxes.append((cb, row[0]))
            # atualiza estilo ao selecionar/desselecionar
            def on_state_change(state, b=box):
                b.setStyleSheet(selected_style if state == Qt.Checked else default_style)
            cb.stateChanged.connect(on_state_change)
            bl.addWidget(cb)
            for lab, val in zip(
                ["Protocolo", "Título", "Solicitante", "Data Final", "Descrição"],
                row[1:]
            ):
                lbl = QLabel(f"<b>{lab}:</b> {val}")
                lbl.setWordWrap(True)
                bl.addWidget(lbl)
            self.scroll_layout.addWidget(box)
        self.table_container.setVisible(False)
        self.analysis_container.setVisible(True)

    def show_connection_history(self):
        # obtém contractServiceTagId antes de abrir diálogo
        tag_ids = []
        for cb, pid in self.checkboxes:
            if cb.isChecked():
                info_url = (
                    f"https://synsuite.teninternet.com.br:45701/api/v1/Projects/Attendance/"
                    f"GetSolicitationInformations?assignmentId={pid}"
                )
                resp = self.session.get(info_url)
                try:
                    info_json = resp.json()
                    tag_id = info_json.get('contractServiceTagId')
                except Exception:
                    tag_id = None
                if tag_id:
                    tag_ids.append(tag_id)
        if not tag_ids:
            QMessageBox.information(self, "Histórico de Conexão", "Selecione ao menos um protocolo.")
            return
        dlg = ConnectionHistoryDialog(self.session, tag_ids, self)
        dlg.exec()

    def show_table_screen(self):
        self.analysis_container.setVisible(False)
        self.table_container.setVisible(True)

    def export_to_excel(self):
        df = pd.DataFrame(self.protocol_data, columns=["ID","Protocolo","Título","Solicitante","Data Final","Descrição"])
        fn, _ = QFileDialog.getSaveFileName(self, "Salvar Excel", "protocolos.xlsx", "Excel Files (*.xlsx)")
        if fn:
            df.to_excel(fn, index=False)
            QMessageBox.information(self, "Sucesso", f"Salvo em: {fn}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginDialog()
    if login.exec() == QDialog.Accepted:
        u, p = login.get_credentials()
        w = MainWindow(u, p)
        w.show()
        sys.exit(app.exec())
    else:
        sys.exit()
