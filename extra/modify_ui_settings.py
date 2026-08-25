import sys
from pathlib import Path

ui_path = Path("ui.py")
content = ui_path.read_text(encoding="utf-8")

if "identity_card = self._card(\"Identity & Profile\"," not in content:
    identity_card_code = """
        # Identity & Profile
        identity_card = self._card("Identity & Profile", "Configure assistant identity, user profile, and behavior.")
        ilay = identity_card.layout()
        
        # Assistant Settings
        ast_row = QHBoxLayout()
        ast_row.addWidget(QLabel("Assistant Name"))
        self._set_ast_name = QLineEdit(identity.get_assistant_name())
        self._set_ast_name.textChanged.connect(lambda t: identity.set_assistant_name(t.strip() or "Brahma"))
        ast_row.addWidget(self._set_ast_name)
        ilay.addLayout(ast_row)
        
        app_row = QHBoxLayout()
        app_row.addWidget(QLabel("Application Name"))
        self._set_app_name = QLineEdit(identity.get_application_name())
        self._set_app_name.textChanged.connect(lambda t: identity.set_application_name(t.strip() or "Brahma Echo"))
        app_row.addWidget(self._set_app_name)
        ilay.addLayout(app_row)

        # Owner Profile
        own_row = QHBoxLayout()
        own_row.addWidget(QLabel("Your Name"))
        self._set_own_name = QLineEdit(identity.get_owner_name())
        self._set_own_name.textChanged.connect(lambda t: identity.set_owner_name(t.strip()))
        own_row.addWidget(self._set_own_name)
        ilay.addLayout(own_row)

        role_row = QHBoxLayout()
        role_row.addWidget(QLabel("Your Role"))
        self._set_own_role = QLineEdit(identity.get_owner_role())
        self._set_own_role.textChanged.connect(lambda t: identity.set_owner_role(t.strip()))
        role_row.addWidget(self._set_own_role)
        ilay.addLayout(role_row)

        # Behavior
        beh_row = QHBoxLayout()
        beh_row.addWidget(QLabel("Behavior Mode"))
        self._set_beh_mode = QComboBox()
        self._set_beh_mode.addItems(["professional", "casual", "technical", "minimal", "proactive"])
        self._set_beh_mode.setCurrentText(identity.get_behavior_mode())
        self._set_beh_mode.currentTextChanged.connect(lambda t: identity.set_behavior_mode(t))
        beh_row.addWidget(self._set_beh_mode)
        ilay.addLayout(beh_row)

        lay.addWidget(identity_card)
"""
    content = content.replace("        # AI Providers", identity_card_code + "\n        # AI Providers")
    ui_path.write_text(content, encoding="utf-8")
    print("ui.py settings modified")
