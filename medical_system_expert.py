import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QGroupBox, QCheckBox, QPushButton, QTextEdit,
                               QComboBox,
                             QScrollArea, QFrame, QSplitter, QMessageBox, QGridLayout, 
                             QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPalette, QColor
from engine import ExpertSystem

class ModernButton(QPushButton):
    def __init__(self, text, color="#00bcd4", parent=None):
        super().__init__(text, parent)
        self.set_color(color)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_color(self, color):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
                margin-top: -2px;
            }}
            QPushButton:pressed {{
                background-color: {color}aa;
                margin-top: 1px;
            }}
        """)

class AppStyle:
    STYLESHEET = """
        QMainWindow {
            background-color: #f0f4f8;
        }
        QLabel {
            color: #2c3e50;
            font-family: 'Segoe UI', sans-serif;
        }
        QGroupBox {
            border: 1px solid #dcdde1;
            border-radius: 10px;
            background-color: white;
            margin-top: 20px;
            font-weight: bold;
            color: #34495e;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QCheckBox {
            font-size: 13px;
            padding: 5px;
            color: #57606f;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid #bdc3c7;
        }
        QCheckBox::indicator:checked {
            background-color: #00bcd4;
            border-color: #00bcd4;
        }
        QTextEdit {
            background-color: #ffffff;
            border: 1px solid #e1e1e1;
            border-radius: 8px;
            padding: 10px;
            font-family: 'Consolas', monospace;
            font-size: 14px;
            color: #2f3640;
        }
        QComboBox {
            border: 1px solid #ced6e0;
            border-radius: 6px;
            padding: 8px;
            min-width: 200px;
            background-color: white;
            color: #2c3e50;
        }
        QComboBox QAbstractItemView {
            background-color: white;
            color: #2c3e50;
            selection-background-color: #00bcd4;
            selection-color: white;
            border: 1px solid #ced6e0;
        }
        QScrollBar:vertical {
            background: #e0e0e0; /* Light grey track */
            width: 14px;
            margin: 0px;
            border-radius: 7px;
        }
        QScrollBar::handle:vertical {
            background: white;   /* White handle */
            min-height: 20px;
            border-radius: 7px;
            border: 1px solid #c0c0c0; /* Subtle border for visibility */
        }
        QScrollBar::add-line:vertical { height: 0px; }
        QScrollBar::sub-line:vertical { height: 0px; }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
    """

class ArtificialDoctorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Expert system 2 (CSV Base)")
        self.resize(1200, 800)
        self.setStyleSheet(AppStyle.STYLESHEET)
        
        # CHANGED: Load from CSV instead of JSON
        self.system = ExpertSystem('knowledge_base_15_rules_forward_chaining_15.csv')
        
        self.init_ui()
        
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        #Header
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #2c3e50; border-radius: 10px;")
        header_frame.setFixedHeight(80)
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("Artificial Doctor (Expert 2)")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        subtitle_label = QLabel("Advanced Symptom Analysis System (CSV Powered)")
        subtitle_label.setStyleSheet("color: #ecf0f1; font-size: 14px; font-style: italic;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(subtitle_label)
        main_layout.addWidget(header_frame)

        #Splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel
        symptoms_group = QGroupBox("Select Your Symptoms")
        symptoms_layout = QVBoxLayout(symptoms_group)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        self.symptoms_grid = QGridLayout(scroll_content)
        self.symptom_checkboxes = {}

        symptoms = self.system.get_observable_symptoms()
        
        row, col = 0, 0

        for sym in symptoms:
            cb = QCheckBox(sym.replace("_", " ").title())
            cb.setProperty("symptom_id", sym)
            cb.stateChanged.connect(self.update_reset_button_state)
            self.symptom_checkboxes[sym] = cb
            self.symptoms_grid.addWidget(cb, row, col)
            row += 1
            
        scroll.setWidget(scroll_content)
        symptoms_layout.addWidget(scroll)
        
        self.btn_reset = ModernButton("Reset Choices", "#bdc3c7")
        self.btn_reset.clicked.connect(self.reset_choices)
        symptoms_layout.addWidget(self.btn_reset)
        
        # Right Panel
        logic_group = QGroupBox("Diagnosis & Verification")
        logic_layout = QVBoxLayout(logic_group)
        
        # Forward
        forward_frame = QFrame()
        forward_frame.setStyleSheet("background-color: #e8f6f3; border-radius: 8px; padding: 10px;")
        fwd_layout = QVBoxLayout(forward_frame)
        fwd_label = QLabel("Diagnosis (Forward Chaining)")
        fwd_label.setStyleSheet("font-weight: bold; color: #16a085; font-size: 16px;")
        btn_diagnose = ModernButton("Diagnose All Possibilities", "#1abc9c")
        btn_diagnose.clicked.connect(self.run_diagnosis)
        
        fwd_layout.addWidget(fwd_label)
        fwd_layout.addWidget(btn_diagnose)
        logic_layout.addWidget(forward_frame)
        
        logic_layout.addSpacing(10)
        
        # Backward
        backward_frame = QFrame()
        backward_frame.setStyleSheet("background-color: #ebf5fb; border-radius: 8px; padding: 10px;")
        bwd_layout = QVBoxLayout(backward_frame)
        bwd_label = QLabel("Verification (Backward Chaining)")
        bwd_label.setStyleSheet("font-weight: bold; color: #2980b9; font-size: 16px;")
        
        input_container = QHBoxLayout()
        self.disease_combo = QComboBox()
        self.disease_combo.addItems(self.system.get_all_conclusions())
        
        btn_verify = ModernButton("Verify Hypothesis", "#3498db")
        btn_verify.clicked.connect(self.run_verification)
        
        input_container.addWidget(self.disease_combo)
        
        bwd_layout.addWidget(bwd_label)
        bwd_layout.addLayout(input_container)
        bwd_layout.addWidget(btn_verify)
        logic_layout.addWidget(backward_frame)

        # Results
        res_label = QLabel("Analysis Results")
        res_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        logic_layout.addWidget(res_label)
        
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        logic_layout.addWidget(self.result_area)

        # Finalize Splitter
        content_splitter.addWidget(symptoms_group)
        content_splitter.addWidget(logic_group)
        content_splitter.setSizes([400, 800])
        content_splitter.setCollapsible(0, False)
        
        main_layout.addWidget(content_splitter)

    def update_reset_button_state(self):
        any_checked = any(cb.isChecked() for cb in self.symptom_checkboxes.values())
        if any_checked:
            self.btn_reset.set_color("#3498db")
        else:
            self.btn_reset.set_color("#bdc3c7")

    def reset_choices(self):
        for cb in self.symptom_checkboxes.values():
            cb.setChecked(False)
        self.result_area.clear()
        self.animate_reset()

    def get_selected_symptoms(self):
        return [sym for sym, cb in self.symptom_checkboxes.items() if cb.isChecked()]

    def run_diagnosis(self):
        selected = self.get_selected_symptoms()
        if not selected:
            self.show_error("Please select at least one symptom from the list.")
            return
            
        self.result_area.clear()
        self.result_area.append("=== RUNNING FORWARD CHAINING DIAGNOSIS ===\n")
        self.result_area.append(f"Observed Facts: {', '.join(selected).replace('_', ' ')}\n")
        
        fired_rules, known_facts = self.system.forward_chaining(selected)
        
        if not fired_rules:
            self.result_area.append("Result: No specific disease identified based on current rules.")
            self.result_area.append("\nNote: Please consult a real doctor. This is an AI simulation.")
            return

        for rule in fired_rules:
            html = f"""
            <div style="background-color: #e8f8f5; padding: 10px; margin: 5px; border-radius: 5px; border-left: 5px solid #1abc9c;">
                <h3 style="color: #16a085;">Start Rule {rule.rule_id} -> {rule.conclusion}</h3>
                <p><b>Conditions Met:</b> {', '.join(rule.conditions)}</p>
                <p><b>Recommendation:</b> {rule.precautions}</p>
            </div>
            """
            self.result_area.insertHtml(html)
            self.result_area.append("") 

        final_conclusions = [r.conclusion for r in fired_rules]
        self.result_area.append(f"\nFinal Inferred States: {', '.join(final_conclusions)}")

    def run_verification(self):
        selected = self.get_selected_symptoms()
        target = self.disease_combo.currentText()
        
        if not selected:
             self.show_error("Please select symptoms first to verify them against the disease.")
             return
             
        self.result_area.clear()
        self.result_area.append(f"=== VERIFYING HYPOTHESIS: {target.upper()} ===\n")
        
        success, trace = self.system.backward_verification(target, selected)
        
        color = "#27ae60" if success else "#c0392b"
        status = "CONFIRMED" if success else "NOT CONFIRMED"
        
        header_html = f"""
        <div style="background-color: {color}20; padding: 10px; border-bottom: 2px solid {color};">
            <h2 style="color: {color}; margin: 0;">Status: {status}</h2>
        </div>
        <br>
        """
        self.result_area.insertHtml(header_html)
        
        self.result_area.append("<b>Logic Trace:</b>")
        for line in trace:
            self.result_area.insertHtml(line + "<br>")

    def show_error(self, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Input Required")
        msg.setText(message)
        msg.setStyleSheet("background-color: white;")
        msg.exec()

    def animate_reset(self):
        self.effect = QGraphicsOpacityEffect(self.centralWidget())
        self.centralWidget().setGraphicsEffect(self.effect)
        
        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0.5)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # Cleanup effect after animation to prevent rendering artifacts
        self.anim.finished.connect(lambda: self.centralWidget().setGraphicsEffect(None))
        
        self.anim.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 244, 248))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(44, 62, 80))
    app.setPalette(palette)
    
    window = ArtificialDoctorApp()
    window.show()
    sys.exit(app.exec())