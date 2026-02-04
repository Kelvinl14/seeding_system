import sys
import os
import logging
import psycopg2
import importlib
from dotenv import load_dotenv
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QComboBox, QPushButton, QTextEdit, QGroupBox, 
    QFormLayout, QSpinBox, QCheckBox, QMessageBox, QProgressBar,
    QTabWidget, QLineEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QIcon

# Adicionar o diretório atual ao sys.path
sys.path.append(str(Path(__file__).resolve().parent))

# Caminho absoluto para a raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

from seed.core.seed_runner import SeedRunner
from seed.config.seed_profiles import SeedSize, PROFILES
from seed.config.seed_settings import load_settings


# Configuração de log para capturar na GUI
class GUILogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg)

class DBWorker(QThread):
    finished = Signal(bool, str)
    log_signal = Signal(str)

    def __init__(self, action, params):
        super().__init__()
        self.action = action
        self.params = params

    def run(self):
        handler = None
        try:
            # Configurar logs
            handler = GUILogHandler(self.log_signal)
            handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            logging.getLogger().addHandler(handler)
            logging.getLogger().setLevel(logging.INFO)

            conn_params = self.params.get('conn_params')
            conn = psycopg2.connect(**conn_params)

            if self.action == 'seed':
                profile_size = self.params.get('profile_size')
                custom_counts = self.params.get('custom_counts')
                selected_seeds = self.params.get('selected_seeds')

                os.environ["SEED_SIZE"] = profile_size.name.lower()

                if profile_size == SeedSize.CUSTOM:
                    # settings.CURRENT_PROFILE.products_count = custom_counts['products']
                    # settings.CURRENT_PROFILE.clients_count = custom_counts['clients']
                    # settings.CURRENT_PROFILE.entries_count = custom_counts['entries']
                    # settings.CURRENT_PROFILE.distributions_count = custom_counts['distributions']
                    # settings.CURRENT_PROFILE.sales_count = custom_counts['sales']
                    os.environ["SEED_PRODUCTS"] = str(custom_counts['products'])
                    os.environ["SEED_CLIENTS"] = str(custom_counts['clients'])
                    os.environ["SEED_ENTRIES"] = str(custom_counts['entries'])
                    os.environ["SEED_DISTRIBUTIONS"] = str(custom_counts['distributions'])
                    os.environ["SEED_SALES"] = str(custom_counts['sales'])

                os.environ["FORCE_SEED"] = (
                    "true" if self.params.get('force_seed', False) else "false"
                )

                settings = load_settings()

                runner = SeedRunner(conn, settings=settings)

                # else:
                #     settings.CURRENT_PROFILE = PROFILES[profile_size]

                # runner = SeedRunner(conn)
                # Modificar runner para aceitar seleção de seeds se necessário
                # Por simplicidade, vamos rodar o runner padrão, mas poderíamos filtrar stages
                # runner.run_all()
                runner.run(only=selected_seeds)
                self.finished.emit(True, "Seeding concluído com sucesso!")

            elif self.action == 'clean':
                tables = self.params.get('tables')
                with conn.cursor() as cur:
                    for table in tables:
                        logging.info(f"Limpando tabela: {table}")
                        cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                conn.commit()
                self.finished.emit(True, "Limpeza concluída com sucesso!")

            conn.close()
        except Exception as e:
            self.finished.emit(False, f"Erro: {str(e)}")
        finally:
            if handler:
                logging.getLogger().removeHandler(handler)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Systock - Database Manager & Seeder")
        self.setMinimumSize(900, 700)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header
        header_label = QLabel("Database Management System")
        header_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_conn_tab(), "Conexão")
        self.tabs.addTab(self.create_seed_tab(), "Seeding")
        self.tabs.addTab(self.create_clean_tab(), "Limpeza")
        main_layout.addWidget(self.tabs)

        # Progress & Logs
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        log_group = QGroupBox("Logs de Execução")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: Consolas, monospace;")
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

    def create_conn_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox("Configurações do PostgreSQL")
        form = QFormLayout()

        env = self.load_env_settings()
        
        self.db_host = QLineEdit(env.get("DB_HOST", "localhost"))
        self.db_port = QLineEdit(env.get("DB_PORT", "5432"))
        self.db_name = QLineEdit(env.get("DB_NAME", "postgres"))
        self.db_user = QLineEdit(env.get("DB_USER", "postgres"))
        self.db_pass = QLineEdit(env.get("DB_PASSWORD", ""))
        self.db_pass.setEchoMode(QLineEdit.Password)
        
        form.addRow("Host:", self.db_host)
        form.addRow("Porta:", self.db_port)
        form.addRow("Banco de Dados:", self.db_name)
        form.addRow("Usuário:", self.db_user)
        form.addRow("Senha:", self.db_pass)
        
        group.setLayout(form)
        layout.addWidget(group)
        
        self.btn_test_conn = QPushButton("Testar Conexão")
        self.btn_test_conn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        self.btn_test_conn.clicked.connect(self.test_connection)

        self.btn_save_conn = QPushButton("Salvar Configurações")
        self.btn_save_conn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.btn_save_conn.clicked.connect(self.save_connection_settings)

        layout.addWidget(self.btn_test_conn)
        layout.addWidget(self.btn_save_conn)
        layout.addStretch()
        return tab

    # =========================
    # TAB DE SEEDING - Cofigurações
    SEED_DEPENDENCIES = {
        "entries": ["products"],
        "distributions": ["products"],
        "sales": ["products", "clients"],
    }

    SEED_MAP = {
        "Produtos": "products",
        "Clientes": "clients",
        "Entradas": "entries",
        "Distribuições": "distributions",
        "Vendas": "sales"
    }

    SEED_MAP_REVERSE = {v: k for k, v in SEED_MAP.items()}

    def create_seed_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Perfil e Volumes
        vol_group = QGroupBox("Configuração de Volume")
        vol_layout = QVBoxLayout()
        
        self.profile_combo = QComboBox()
        for size in SeedSize:
            self.profile_combo.addItem(size.name, size)
        self.profile_combo.setCurrentText("MEDIUM")
        self.profile_combo.currentIndexChanged.connect(self.on_profile_changed)
        vol_layout.addWidget(QLabel("Perfil:"))
        vol_layout.addWidget(self.profile_combo)
        
        self.custom_group = QWidget()
        custom_form = QFormLayout(self.custom_group)
        self.spin_products = QSpinBox(); self.spin_products.setRange(0, 1000000); self.spin_products.setValue(500)
        self.spin_clients = QSpinBox(); self.spin_clients.setRange(0, 1000000); self.spin_clients.setValue(100)
        self.spin_entries = QSpinBox(); self.spin_entries.setRange(0, 1000000); self.spin_entries.setValue(200)
        self.spin_dist = QSpinBox(); self.spin_dist.setRange(0, 1000000); self.spin_dist.setValue(150)
        self.spin_sales = QSpinBox(); self.spin_sales.setRange(0, 1000000); self.spin_sales.setValue(300)
        
        custom_form.addRow("Produtos:", self.spin_products)
        custom_form.addRow("Clientes:", self.spin_clients)
        custom_form.addRow("Entradas:", self.spin_entries)
        custom_form.addRow("Distribuições:", self.spin_dist)
        custom_form.addRow("Vendas:", self.spin_sales)
        
        vol_layout.addWidget(self.custom_group)
        vol_group.setLayout(vol_layout)
        layout.addWidget(vol_group)
        
        # Seleção de Seeds
        seed_sel_group = QGroupBox("Selecionar Seeds")
        seed_sel_layout = QVBoxLayout()
        self.seed_list = QListWidget()

        for s in self.SEED_MAP:
            item = QListWidgetItem(s)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.seed_list.addItem(item)

        seed_sel_layout.addWidget(self.seed_list)
        seed_sel_group.setLayout(seed_sel_layout)
        layout.addWidget(seed_sel_group)
        
        self.check_force = QCheckBox("Forçar execução (Produção)")
        layout.addWidget(self.check_force)

        
        self.btn_run_seed = QPushButton("Iniciar Seeding")
        self.btn_run_seed.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        self.btn_run_seed.clicked.connect(self.start_seeding)
        layout.addWidget(self.btn_run_seed)
        
        return tab

    def create_clean_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox("Limpeza de Dados (TRUNCATE)")
        vbox = QVBoxLayout()
        
        self.clean_list = QListWidget()
        tables = [
            "sale_items", "sales", "internal_distribution_items", 
            "internal_distributions", "product_entry_items", 
            "product_entries", "products", "clients", "suppliers", "stores"
        ]
        for t in tables:
            item = QListWidgetItem(t)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.clean_list.addItem(item)
        
        vbox.addWidget(QLabel("Selecione as tabelas para limpar (CUIDADO: Isso apagará os dados!):"))
        vbox.addWidget(self.clean_list)
        
        self.btn_clean = QPushButton("Limpar Tabelas Selecionadas")
        self.btn_clean.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        self.btn_clean.clicked.connect(self.start_cleaning)
        vbox.addWidget(self.btn_clean)
        
        group.setLayout(vbox)
        layout.addWidget(group)
        layout.addStretch()
        return tab

    def validate_seed_dependencies(self, selected_seeds: list[str]) -> tuple[bool, str]:
        missing = {}

        for seed in selected_seeds:
            deps = self.SEED_DEPENDENCIES.get(seed, [])
            for dep in deps:
                if dep not in selected_seeds:
                    missing.setdefault(seed, []).append(dep)

        if not missing:
            return True, ""

        messages = []
        for seed, deps in missing.items():
            seed_label = self.SEED_MAP_REVERSE.get(seed, seed)
            dep_labels = [self.SEED_MAP_REVERSE.get(d, d) for d in deps]
            messages.append(
                f"• {seed_label} depende de: {', '.join(dep_labels)}"
            )

        msg = (
                "Algumas seeds selecionadas possuem dependências não marcadas:\n\n"
                + "\n".join(messages)
        )

        return False, msg

    def auto_select_dependencies(self, selected_seeds: list[str]):
        required = set(selected_seeds)

        for seed in selected_seeds:
            deps = self.SEED_DEPENDENCIES.get(seed, [])
            required.update(deps)

        for i in range(self.seed_list.count()):
            label = self.seed_list.item(i).text()
            seed_id = self.SEED_MAP[label]
            if seed_id in required:
                self.seed_list.item(i).setCheckState(Qt.Checked)

    def get_conn_params(self):
        return {
            "host": self.db_host.text(),
            "port": self.db_port.text(),
            "database": self.db_name.text(),
            "user": self.db_user.text(),
            "password": self.db_pass.text(),
            "sslmode": "require" if "render" in self.db_host.text().lower() else "prefer"
        }

    def test_connection(self):
        try:
            params = self.get_conn_params()
            conn = psycopg2.connect(**params)
            conn.close()
            QMessageBox.information(self, "Sucesso", "Conexão estabelecida com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Conexão", str(e))

    def save_connection_settings(self):
        try:
            params = self.get_conn_params()
            env_file = BASE_DIR / ".env"

            with open(env_file, "w") as f:
                f.write(f"DB_HOST={params['host']}\n")
                f.write(f"DB_PORT={params['port']}\n")
                f.write(f"DB_NAME={params['database']}\n")
                f.write(f"DB_USER={params['user']}\n")
                f.write(f"DB_PASSWORD={params['password']}\n")

            # 🔥 ATUALIZA O ENV EM MEMÓRIA
            load_dotenv(env_file, override=True)

            QMessageBox.information(self, "Sucesso", "Configurações salvas em .env")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", str(e))

    def load_env_settings(self):
        env_file = BASE_DIR / ".env"
        if not env_file.exists():
            return {}

        env = {}
        with open(env_file, "r") as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    env[key] = value
        return env

    def on_profile_changed(self, index):
        size = self.profile_combo.currentData()
        is_custom = (size == SeedSize.CUSTOM)
        self.custom_group.setEnabled(is_custom)
        if not is_custom:
            p = PROFILES[size]
            self.spin_products.setValue(p.products_count)
            self.spin_clients.setValue(p.clients_count)
            self.spin_entries.setValue(p.entries_count)
            self.spin_dist.setValue(p.distributions_count)
            self.spin_sales.setValue(p.sales_count)

    def start_seeding(self):
        SEED_MAP = {
            "Produtos": "products",
            "Clientes": "clients",
            "Entradas": "entries",
            "Distribuições": "distributions",
            "Vendas": "sales",
        }

        params = {
            'conn_params': self.get_conn_params(),
            'profile_size': self.profile_combo.currentData(),
            'custom_counts': {
                'products': self.spin_products.value(),
                'clients': self.spin_clients.value(),
                'entries': self.spin_entries.value(),
                'distributions': self.spin_dist.value(),
                'sales': self.spin_sales.value()
            },
            'selected_seeds': [SEED_MAP[self.seed_list.item(i).text()] for i in range(self.seed_list.count()) if self.seed_list.item(i).checkState() == Qt.Checked]
        }
        # settings.FORCE_SEED = self.check_force.isChecked()
        os.environ["FORCE_SEED"] = "true" if self.check_force.isChecked() else "false"

        ok, error_msg = self.validate_seed_dependencies(params['selected_seeds'])

        if not ok:
            reply = QMessageBox.warning(
                self,
                "Dependências de Seeds",
                error_msg + "\n\nDeseja selecionar automaticamente as dependências?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.auto_select_dependencies(params['selected_seeds'])
            else:
                return

        self.run_worker('seed', params)

    def start_cleaning(self):
        selected_tables = [self.clean_list.item(i).text() for i in range(self.clean_list.count()) if self.clean_list.item(i).checkState() == Qt.Checked]
        if not selected_tables:
            QMessageBox.warning(self, "Aviso", "Nenhuma tabela selecionada.")
            return
        
        reply = QMessageBox.critical(
            self, "Confirmação de Exclusão", 
            f"Você tem certeza que deseja apagar TODOS os dados das tabelas: {', '.join(selected_tables)}?\nEsta ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            params = {'conn_params': self.get_conn_params(), 'tables': selected_tables}
            self.run_worker('clean', params)

    def run_worker(self, action, params):
        self.log_output.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.tabs.setEnabled(False)
        
        self.worker = DBWorker(action, params)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    @Slot(str)
    def append_log(self, message):
        self.log_output.append(message)
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    @Slot(bool, str)
    def on_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.tabs.setEnabled(True)
        if success:
            QMessageBox.information(self, "Sucesso", message)
        else:
            QMessageBox.critical(self, "Erro", message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
