import sys
import csv
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QRadioButton, QCheckBox, 
                             QPushButton, QTextEdit, QScrollArea, QComboBox, 
                             QButtonGroup, QFrame, QSplitter, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class Rule:
    def __init__(self, rule_id, conditions, conclusion, precautions):
        self.rule_id = rule_id
        self.conditions = conditions # List of strings
        self.conclusion = conclusion # String
        self.precautions = precautions # String

    def __repr__(self):
        return f"Rule({self.rule_id}: {self.conditions} -> {self.conclusion})"

class ExpertSystem:
    def __init__(self, csv_path):
        self.rules = []
        try:
            self.load_rules(csv_path)
        except Exception as e:
            print(f"Error loading rules: {e}")

    def load_rules(self, csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle potential whitespace in CSV keys/values
                row = {k.strip(): v.strip() for k, v in row.items()}
                
                if not row['conditions']:
                    continue
                    
                conditions = [c.strip() for c in row['conditions'].split(';')]
                self.rules.append(Rule(
                    row['rule_id'],
                    conditions,
                    row['conclusion'],
                    row['precautions']
                ))

    def get_observable_symptoms(self):
        """
        Returns a list of symptoms that are not conclusions of other rules.
        These are the 'leaf' inputs the user should provide.
        """
        all_conclusions = set(r.conclusion for r in self.rules)
        all_conditions = set()
        for rule in self.rules:
            for c in rule.conditions:
                all_conditions.add(c)
        
        # Base symptoms are conditions that are never conclusions
        observable = all_conditions - all_conclusions
        return sorted(list(observable))

    def get_all_diseases(self):
        """Returns all possible conclusions."""
        return sorted(list(set(r.conclusion for r in self.rules)))

    def forward_chaining(self, selected_symptoms):
        """
        Data-driven: Starts with known facts (symptoms) and infers conclusions.
        """
        known_facts = set(selected_symptoms)
        fired_rules = []
        
        # We loop until no new rules fire
        while True:
            new_rule_fired = False
            for rule in self.rules:
                # If we haven't already fired this rule (or established its conclusion)
                # Note: A conclusion might be established by multiple rules, 
                # but here we track specific rule firings.
                if rule in fired_rules:
                    continue
                
                # If the conclusion is already known (maybe from another rule), 
                # we technically don't need to fire, but for expert systems 
                # we often want to know ALL paths. 
                # Simple version: if we know the conclusion, skip? 
                # No, let's see if this specific rule applies.
                
                # Check conditions
                if all(c in known_facts for c in rule.conditions):
                    if rule.conclusion not in known_facts:
                        known_facts.add(rule.conclusion)
                        new_rule_fired = True
                    fired_rules.append(rule)
                    
            if not new_rule_fired and len(fired_rules) == len([r for r in fired_rules]):
                # Break if no *new* facts were derived? 
                # Actually loop should break if state didn't change.
                # Simplest check: did we add to known_facts?
                if not new_rule_fired:
                    break
                    
        return fired_rules, known_facts

    def backward_chaining(self, target_disease):
        """
        Goal-driven: Starts with a hypothesis (disease) and works back to symptoms.
        Returns a structured trace of the logic.
        """
        trace = []
        
        def solve_goal(goal, depth=0):
            indent = "    " * depth
            # Find rules that conclude this goal
            candidate_rules = [r for r in self.rules if r.conclusion == goal]
            
            if not candidate_rules:
                # No rules conclude this. It must be a base symptom.
                # In a real rigorous system we'd check if user has it.
                # Here we just list it as a requirement.
                return False, [f"{indent}- Basic Symptom needed: '{goal}'"]
            
            success_paths = []
            
            for rule in candidate_rules:
                rule_desc = f"{indent}* Checking Rule {rule.rule_id} (Conclusion: {goal})"
                rule_path = [rule_desc]
                
                conditions_list = f"{indent}  Requires: {', '.join(rule.conditions)}"
                rule_path.append(conditions_list)
                
                # Recursively check conditions
                for condition in rule.conditions:
                    is_derived, sub_trace = solve_goal(condition, depth + 1)
                    rule_path.extend(sub_trace)
                    
                success_paths.extend(rule_path)

            return True, success_paths

        _, trace = solve_goal(target_disease)
        return trace

class MedicalExpertApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Medical Expert System")
        self.setGeometry(100, 100, 1000, 700)
        
        # Load System
        self.expert_system = ExpertSystem('knowledge_base_15_rules_forward_chaining_15.csv')
        
        # Main Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget)
        
        # Header
        header = QLabel("Medical Symptom Checker Expert System")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.layout.addWidget(header)
        
        # Mode Selection
        mode_group = QGroupBox("Select Chaining Mode")
        mode_layout = QHBoxLayout()
        
        self.rb_forward = QRadioButton("Forward Chaining (Symptom to Disease)")
        self.rb_backward = QRadioButton("Backward Chaining (Disease Logic Analysis)")
        self.rb_forward.setChecked(True)
        
        self.rb_forward.toggled.connect(self.switch_mode)
        self.rb_backward.toggled.connect(self.switch_mode)
        
        mode_layout.addWidget(self.rb_forward)
        mode_layout.addWidget(self.rb_backward)
        mode_group.setLayout(mode_layout)
        self.layout.addWidget(mode_group)
        
        # Content Stack (Since we want to swap UIs)
        # Instead of QStackedWidget, simply rebuilding/showing hiding frames is easier for this simpler script
        
        self.forward_frame = QFrame()
        self.setup_forward_ui()
        self.layout.addWidget(self.forward_frame)
        
        self.backward_frame = QFrame()
        self.setup_backward_ui()
        self.layout.addWidget(self.backward_frame)
        
        self.switch_mode() # Set initial state

    def switch_mode(self):
        if self.rb_forward.isChecked():
            self.forward_frame.show()
            self.backward_frame.hide()
        else:
            self.forward_frame.hide()
            self.backward_frame.show()

    def setup_forward_ui(self):
        layout = QVBoxLayout(self.forward_frame)
        
        # Instructions
        lbl = QLabel("Select all symptoms you are experiencing:")
        lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(lbl)
        
        # Scroll area for symptoms
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.symptom_grid = QGridLayout(scroll_content)
        
        symptoms = self.expert_system.get_observable_symptoms()
        self.symptom_checkboxes = {}
        
        # Create a grid of checkboxes
        row, col = 0, 0
        max_cols = 3
        for sym in symptoms:
            cb = QCheckBox(sym)
            self.symptom_checkboxes[sym] = cb
            self.symptom_grid.addWidget(cb, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Action Button
        btn_diagnose = QPushButton("Diagnose")
        btn_diagnose.clicked.connect(self.run_forward_chaining)
        btn_diagnose.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        layout.addWidget(btn_diagnose)
        
        # Result Area
        lbl_res = QLabel("Diagnosis Results:")
        lbl_res.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(lbl_res)
        
        self.forward_results = QTextEdit()
        self.forward_results.setReadOnly(True)
        layout.addWidget(self.forward_results)

    def setup_backward_ui(self):
        layout = QVBoxLayout(self.backward_frame)
        
        lbl = QLabel("Select a disease to verify/analyze:")
        lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(lbl)
        
        self.disease_combo = QComboBox()
        self.disease_combo.addItems(self.expert_system.get_all_diseases())
        layout.addWidget(self.disease_combo)
        
        btn_analyze = QPushButton("Analyze Logic (Backward Chain)")
        btn_analyze.clicked.connect(self.run_backward_chaining)
        btn_analyze.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        layout.addWidget(btn_analyze)
        
        lbl_res = QLabel("Backward Chaining Trace:")
        lbl_res.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(lbl_res)
        
        self.backward_results = QTextEdit()
        self.backward_results.setReadOnly(True)
        layout.addWidget(self.backward_results)

    def run_forward_chaining(self):
        selected = []
        for sym, cb in self.symptom_checkboxes.items():
            if cb.isChecked():
                selected.append(sym)
        
        if not selected:
            self.forward_results.setText("Please select at least one symptom.")
            return

        self.forward_results.clear()
        self.forward_results.append(f"<b>Selected Symptoms:</b> {', '.join(selected)}<br>")
        self.forward_results.append("<hr>")
        
        fired_rules, final_facts = self.expert_system.forward_chaining(selected)
        
        if not fired_rules:
            self.forward_results.append("No specific disease matched your symptoms based on the rule base.")
        else:
            self.forward_results.append(f"<b>Inference Chain:</b><br>")
            for rule in fired_rules:
                self.forward_results.append(f"Rule <b>{rule.rule_id}</b> fired.<br>"
                                          f"&nbsp;&nbsp;Facts detected: {', '.join(rule.conditions)}<br>"
                                          f"&nbsp;&nbsp;Conclusion: <span style='color:red'><b>{rule.conclusion}</b></span><br>")
            
            self.forward_results.append("<hr>")
            self.forward_results.append("<b>FINAL CONCLUSIONS & ADVICE:</b><br>")
            
            # Show precautions for the final conclusions (leaves of the inference)
            # Or just show all? Usually the 'most inferred' ones. 
            # Let's show all implied conclusions that are diseases (or final states)
            
            for rule in fired_rules:
                self.forward_results.append(f"<h3>{rule.conclusion}</h3>")
                self.forward_results.append(f"<b>Precautions:</b> {rule.precautions}<br>")

    def run_backward_chaining(self):
        disease = self.disease_combo.currentText()
        if not disease:
            return
            
        trace = self.expert_system.backward_chaining(disease)
        
        self.backward_results.clear()
        self.backward_results.append(f"<h2>Analysis for: {disease}</h2>")
        self.backward_results.append("The system checks for the following symptoms/conditions recursively:<br><br>")
        
        raw_text = "\n".join(trace)
        self.backward_results.append(f"<pre>{raw_text}</pre>")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MedicalExpertApp()
    window.show()
    sys.exit(app.exec())
