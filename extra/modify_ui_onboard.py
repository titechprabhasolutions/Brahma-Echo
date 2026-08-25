import sys
from pathlib import Path

ui_path = Path("ui.py")
content = ui_path.read_text(encoding="utf-8")

if "from core.identity import identity" not in content:
    content = content.replace("from workspace_store import store as workspace_store\n", "from workspace_store import store as workspace_store\nfrom core.identity import identity\n")

if "_build_stage_identity" not in content:
    content = content.replace(
        "        self._build_stage1()\n        self._build_stage2()",
        "        self._build_stage1()\n        self._build_stage_identity()\n        self._build_stage_owner()\n        self._build_stage_behavior()\n        self._build_stage_shared()\n        self._build_stage2()"
    )

    stage_code = """
    # ── STAGE 1.1: Assistant Identity ────────────────────────────────
    def _build_stage_identity(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addStretch(2)

        title = QLabel("DEFINE YOUR ASSISTANT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: rgba(255,255,255,0.7); background: transparent; letter-spacing: 2px;")
        lay.addWidget(title)
        
        sub = QLabel("Every assistant needs an identity.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: rgba(255,255,255,0.4); background: transparent;")
        lay.addWidget(sub)
        lay.addSpacing(20)

        form_lay = QGridLayout()
        form_lay.setSpacing(16)
        
        lbl_ast = QLabel("Assistant Name")
        lbl_ast.setStyleSheet("color: #ffaa30;")
        self._inp_ast = QLineEdit(identity.get_assistant_name())
        self._inp_ast.setStyleSheet("background: rgba(255,255,255,0.1); color: #fff; padding: 6px; border-radius: 4px;")
        form_lay.addWidget(lbl_ast, 0, 0)
        form_lay.addWidget(self._inp_ast, 0, 1)

        lbl_app = QLabel("Application Name")
        lbl_app.setStyleSheet("color: #ffaa30;")
        self._inp_app = QLineEdit(identity.get_application_name())
        self._inp_app.setStyleSheet("background: rgba(255,255,255,0.1); color: #fff; padding: 6px; border-radius: 4px;")
        form_lay.addWidget(lbl_app, 1, 0)
        form_lay.addWidget(self._inp_app, 1, 1)

        container = QWidget()
        container.setFixedWidth(400)
        container.setLayout(form_lay)
        lay.addWidget(container, 0, Qt.AlignmentFlag.AlignCenter)

        btn = QPushButton("CONTINUE →")
        btn.setFixedSize(160, 40)
        btn.setStyleSheet("background: rgba(255, 170, 48, 0.2); color: #ffaa30; border: 1px solid #ffaa30; border-radius: 20px;")
        btn.clicked.connect(self._save_identity_and_next)
        lay.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        lay.addStretch(2)
        self._stack.addWidget(page)

    def _save_identity_and_next(self):
        identity.set_assistant_name(self._inp_ast.text().strip() or "Brahma")
        identity.set_application_name(self._inp_app.text().strip() or "Brahma Echo")
        self._stack.setCurrentIndex(2)

    # ── STAGE 1.2: Owner Profile ────────────────────────────────
    def _build_stage_owner(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addStretch(2)

        title = QLabel("WHO AM I ASSISTING?")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: rgba(255,255,255,0.7); background: transparent; letter-spacing: 2px;")
        lay.addWidget(title)
        
        sub = QLabel("Tell me a little about yourself so I can work better with you.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: rgba(255,255,255,0.4); background: transparent;")
        lay.addWidget(sub)
        lay.addSpacing(20)

        form_lay = QGridLayout()
        form_lay.setSpacing(16)
        
        lbl_own = QLabel("Your Name")
        lbl_own.setStyleSheet("color: #ffaa30;")
        self._inp_own = QLineEdit(identity.get_owner_name())
        self._inp_own.setStyleSheet("background: rgba(255,255,255,0.1); color: #fff; padding: 6px; border-radius: 4px;")
        form_lay.addWidget(lbl_own, 0, 0)
        form_lay.addWidget(self._inp_own, 0, 1)

        lbl_role = QLabel("Your Role")
        lbl_role.setStyleSheet("color: #ffaa30;")
        self._inp_role = QLineEdit(identity.get_owner_role())
        self._inp_role.setPlaceholderText("e.g. Student, Developer")
        self._inp_role.setStyleSheet("background: rgba(255,255,255,0.1); color: #fff; padding: 6px; border-radius: 4px;")
        form_lay.addWidget(lbl_role, 1, 0)
        form_lay.addWidget(self._inp_role, 1, 1)

        container = QWidget()
        container.setFixedWidth(400)
        container.setLayout(form_lay)
        lay.addWidget(container, 0, Qt.AlignmentFlag.AlignCenter)

        btn = QPushButton("CONTINUE →")
        btn.setFixedSize(160, 40)
        btn.setStyleSheet("background: rgba(255, 170, 48, 0.2); color: #ffaa30; border: 1px solid #ffaa30; border-radius: 20px;")
        btn.clicked.connect(self._save_owner_and_next)
        lay.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        lay.addStretch(2)
        self._stack.addWidget(page)

    def _save_owner_and_next(self):
        identity.set_owner_name(self._inp_own.text().strip())
        identity.set_owner_role(self._inp_role.text().strip())
        self._stack.setCurrentIndex(3)

    # ── STAGE 1.3: Behavior ────────────────────────────────
    def _build_stage_behavior(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addStretch(2)

        title = QLabel("HOW SHOULD I ASSIST YOU?")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: rgba(255,255,255,0.7); background: transparent; letter-spacing: 2px;")
        lay.addWidget(title)
        lay.addSpacing(20)

        self._combo_mode = QComboBox()
        self._combo_mode.addItems(["professional", "casual", "technical", "minimal", "proactive"])
        self._combo_mode.setCurrentText(identity.get_behavior_mode())
        self._combo_mode.setStyleSheet("background: rgba(255,255,255,0.1); color: #fff; padding: 6px; border-radius: 4px;")
        self._combo_mode.setFixedWidth(300)
        lay.addWidget(self._combo_mode, 0, Qt.AlignmentFlag.AlignCenter)
        
        sub = QLabel("Custom Instructions (Optional)")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #ffaa30; margin-top: 10px;")
        lay.addWidget(sub)
        
        self._inp_custom = QTextEdit(identity.get_custom_instructions())
        self._inp_custom.setFixedSize(400, 80)
        self._inp_custom.setStyleSheet("background: rgba(255,255,255,0.1); color: #fff; padding: 6px; border-radius: 4px;")
        lay.addWidget(self._inp_custom, 0, Qt.AlignmentFlag.AlignCenter)

        lay.addSpacing(20)
        btn = QPushButton("CONTINUE →")
        btn.setFixedSize(160, 40)
        btn.setStyleSheet("background: rgba(255, 170, 48, 0.2); color: #ffaa30; border: 1px solid #ffaa30; border-radius: 20px;")
        btn.clicked.connect(self._save_behavior_and_next)
        lay.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        lay.addStretch(2)
        self._stack.addWidget(page)

    def _save_behavior_and_next(self):
        identity.set_behavior_mode(self._combo_mode.currentText())
        identity.set_custom_instructions(self._inp_custom.toPlainText().strip())
        self._stack.setCurrentIndex(4)

    # ── STAGE 1.4: Shared Computer ────────────────────────────────
    def _build_stage_shared(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addStretch(2)

        title = QLabel("WHO USES THIS COMPUTER?")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: rgba(255,255,255,0.7); background: transparent; letter-spacing: 2px;")
        lay.addWidget(title)
        lay.addSpacing(20)
        
        btn_personal = QPushButton("THIS IS MY PERSONAL COMPUTER")
        btn_personal.setFixedSize(300, 50)
        btn_personal.setStyleSheet("background: rgba(255, 170, 48, 0.1); color: #ffaa30; border: 1px solid #ffaa30; border-radius: 8px;")
        btn_personal.clicked.connect(lambda: self._save_shared_and_next(False))
        lay.addWidget(btn_personal, 0, Qt.AlignmentFlag.AlignCenter)
        
        lay.addSpacing(10)
        
        btn_shared = QPushButton("THIS IS A SHARED COMPUTER")
        btn_shared.setFixedSize(300, 50)
        btn_shared.setStyleSheet("background: rgba(255,255,255, 0.05); color: #fff; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px;")
        btn_shared.clicked.connect(lambda: self._save_shared_and_next(True))
        lay.addWidget(btn_shared, 0, Qt.AlignmentFlag.AlignCenter)
        
        lay.addStretch(2)
        self._stack.addWidget(page)
        
    def _save_shared_and_next(self, shared: bool):
        identity.set_shared_computer(shared)
        self._stack.setCurrentIndex(5)
"""
    
    content = content.replace("    def _build_stage2(self):", stage_code + "\n    def _build_stage2(self):")

    content = content.replace(
        "QTimer.singleShot(2500, lambda: self._stack.setCurrentIndex(1))",
        "QTimer.singleShot(2500, self._finish_stage1)"
    )
    
    finish_stage1_code = """
    def _finish_stage1(self):
        if not identity.is_setup_complete():
            self._stack.setCurrentIndex(1)
        else:
            self._stack.setCurrentIndex(5)
"""
    content = content.replace("    def _build_stage2(self):", finish_stage1_code + "\n    def _build_stage2(self):")

ui_path.write_text(content, encoding="utf-8")
print("ui.py modified")
