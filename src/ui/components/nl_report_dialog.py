from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QHBoxLayout, QSizePolicy, QFileDialog, QMessageBox
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtCore import Qt, QDate
from ...core.utils import parse_transaction, get_mistral_api_key
import requests, re, calendar, dateutil.parser, csv

class NaturalLanguageReportDialog(QDialog):
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI-Powered Report Generator")
        self.setMinimumSize(720, 600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(18)
        header = QLabel("Generate Report with AI")
        header.setStyleSheet("color: #569CD6; font-size: 20px; font-weight: bold;")
        layout.addWidget(header, alignment=Qt.AlignHCenter)
        self.prompt_edit = QLineEdit()
        self.prompt_edit.setPlaceholderText("e.g. generate income statement for May 2025")
        layout.addWidget(self.prompt_edit)
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.result_box, stretch=1)
        btn_row = QHBoxLayout()
        self.generate_btn = QPushButton("Generate")
        self.generate_btn.clicked.connect(self.generate_report)
        btn_row.addWidget(self.generate_btn)
        self.export_btn = QPushButton("Export CSV")
        self.export_btn.clicked.connect(self.export_csv)
        btn_row.addWidget(self.export_btn)
        self.print_btn = QPushButton("Print")
        self.print_btn.clicked.connect(self.print_report)
        btn_row.addWidget(self.print_btn)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)
        self.system = system
        self.last_report_text = ""

    def generate_report(self):
        prompt = self.prompt_edit.text().strip()
        if not prompt:
            self.result_box.setPlainText("Please enter a prompt.")
            return
        self.result_box.setPlainText("Generating report, please wait...")
        try:
            prompt_lc = prompt.lower()
            report_type = None
            from_date = to_date = as_of_date = None
            # Simple patterns for report type
            if "income statement" in prompt_lc:
                report_type = "income_statement"
            elif "balance sheet" in prompt_lc:
                report_type = "balance_sheet"
            elif "cash flow" in prompt_lc:
                report_type = "cash_flow"
            # Date extraction (month/year or as of date)
            month_year = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})', prompt_lc)
            year = re.search(r'\b(20\d{2})\b', prompt_lc)
            as_of = re.search(r'as of (\w+ \d{1,2},? \d{4})', prompt_lc)
            today = QDate.currentDate().toString("yyyy-MM-dd")
            # Default: current month
            if month_year:
                month = list(calendar.month_name).index(month_year.group(1).capitalize())
                year_val = int(month_year.group(2))
                from_date = f"{year_val}-{month:02d}-01"
                to_date = f"{year_val}-{month:02d}-{calendar.monthrange(year_val, month)[1]:02d}"
            elif as_of:
                as_of_date = dateutil.parser.parse(as_of.group(1)).strftime("%Y-%m-%d")
            elif year:
                from_date = f"{year.group(1)}-01-01"
                to_date = f"{year.group(1)}-12-31"
            else:
                from_date = QDate.currentDate().addMonths(-1).toString("yyyy-MM-01")
                to_date = today
            # --- Step 2: Get real data from backend ---
            data_summary = ""
            if report_type == "income_statement":
                breakdown = self.system.generate_income_statement_breakdown(from_date, to_date)
                data_summary = f"INCOME STATEMENT DATA ({from_date} to {to_date}):\n" + str(breakdown)
            elif report_type == "balance_sheet":
                as_of = as_of_date or today
                breakdown = self.system.generate_balance_sheet_breakdown(as_of)
                data_summary = f"BALANCE SHEET DATA (as of {as_of}):\n" + str(breakdown)
            elif report_type == "cash_flow":
                breakdown = self.system.generate_cash_flow_breakdown(from_date, to_date)
                data_summary = f"CASH FLOW DATA ({from_date} to {to_date}):\n" + str(breakdown)
            else:
                data_summary = "SYSTEM DATA: (No recognized report type, showing all available)\n"
                data_summary += str(self.system.get_trial_balance(from_date, to_date))
            # --- Step 3: LLM playbook ---
            playbook = '''
You are an expert accountant and reporting assistant. Given the user's request and the real accounting data below, you must:
- Strictly follow double-entry accounting rules and classic report formats (Income Statement, Balance Sheet, Cash Flow, etc).
- Use only the data provided below. Never invent or estimate numbers.
- If a date or period is specified, use it. If not, use the most recent data.
- Format the report in clear, professional markdown or plain text.
- Respond with only the report itself, and no extra explanation, commentary, or preamble. The popup should show only the report.
- If the request is ambiguous, ask for clarification.
'''
            api_key = get_mistral_api_key()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            data = {
                "model": "mistral-tiny",
                "messages": [
                    {"role": "user", "content": playbook + f"\n\nUSER REQUEST: {prompt}\n\nREAL DATA:\n{data_summary}"}
                ]
            }
            response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            self.result_box.setMarkdown(content)
            self.last_report_text = content
        except Exception as e:
            self.result_box.setPlainText(f"Error: {e}")
            self.last_report_text = ""

    def export_csv(self):
        if not self.last_report_text.strip():
            QMessageBox.warning(self, "Export", "No report to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Report", "report.csv", "CSV Files (*.csv)")
        if not path:
            return
        # Try to extract table from markdown/plain text and save as CSV
        lines = self.last_report_text.splitlines()
        table_lines = [l for l in lines if ("," in l or "|" in l)]
        if not table_lines:
            QMessageBox.warning(self, "Export", "No tabular data found in report.")
            return
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for l in table_lines:
                if "|" in l:
                    row = [cell.strip() for cell in l.strip("|").split("|")]
                else:
                    row = [cell.strip() for cell in l.split(",")]
                writer.writerow(row)
        QMessageBox.information(self, "Export", f"Report exported to {path}")

    def print_report(self):
        if not self.last_report_text.strip():
            QMessageBox.warning(self, "Print", "No report to print.")
            return
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.Accepted:
            self.result_box.print(printer)
