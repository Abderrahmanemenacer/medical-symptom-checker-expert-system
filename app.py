import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


CSV_PATH = "knowledge_base_15_rules_forward_chaining_15.csv"
SPECIAL_CONCLUSIONS = {"emergency", "seek_emergency_care"}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    conditions: Tuple[str, ...]
    conclusion: str
    precautions: Tuple[str, ...]


def load_rules(csv_path: str) -> List[Rule]:
    rules: List[Rule] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conditions = tuple(s.strip() for s in row["conditions"].split(";") if s.strip())
            precautions = tuple(s.strip() for s in row["precautions"].split(";") if s.strip())
            rules.append(
                Rule(
                    rule_id=row["rule_id"].strip(),
                    conditions=conditions,
                    conclusion=row["conclusion"].strip(),
                    precautions=precautions,
                )
            )
    return rules


def build_indexes(rules: List[Rule]) -> Tuple[Set[str], Set[str], Dict[str, List[Rule]]]:
    conclusions = {r.conclusion for r in rules}
    conditions = {c for r in rules for c in r.conditions}
    base_symptoms = {c for c in conditions if c not in conclusions and c not in SPECIAL_CONCLUSIONS}
    by_conclusion: Dict[str, List[Rule]] = {}
    for r in rules:
        by_conclusion.setdefault(r.conclusion, []).append(r)
    return base_symptoms, conclusions, by_conclusion


def forward_chain(rules: List[Rule], initial_facts: Set[str]) -> Tuple[Set[str], List[Rule]]:
    facts = set(initial_facts)
    fired: List[Rule] = []
    changed = True
    while changed:
        changed = False
        for rule in rules:
            if rule in fired:
                continue
            if all(cond in facts for cond in rule.conditions):
                fired.append(rule)
                facts.add(rule.conclusion)
                changed = True
    return facts, fired


def explain_backward(
    goal: str,
    by_conclusion: Dict[str, List[Rule]],
    base_symptoms: Set[str],
    conclusions: Set[str],
    depth: int = 0,
    visited: Set[str] | None = None,
) -> List[str]:
    if visited is None:
        visited = set()
    lines: List[str] = []
    indent = "  " * depth
    if goal in visited:
        lines.append(f"{indent}- {goal} (already expanded)")
        return lines
    visited.add(goal)

    rules = by_conclusion.get(goal, [])
    if not rules:
        if goal in base_symptoms:
            lines.append(f"{indent}- {goal} (symptom)")
        else:
            lines.append(f"{indent}- {goal} (no rule found)")
        return lines

    lines.append(f"{indent}- Goal: {goal}")
    for rule in rules:
        conds = ", ".join(rule.conditions)
        lines.append(f"{indent}  Rule {rule.rule_id}: requires {conds}")
        for cond in rule.conditions:
            if cond in base_symptoms:
                lines.append(f"{indent}    - {cond} (symptom)")
            elif cond in conclusions:
                lines.extend(explain_backward(cond, by_conclusion, base_symptoms, conclusions, depth + 2, visited))
            else:
                lines.append(f"{indent}    - {cond} (unknown)")
    return lines


class MainWindow(QMainWindow):
    def __init__(self, rules: List[Rule]) -> None:
        super().__init__()
        self.rules = rules
        self.base_symptoms, self.conclusions, self.by_conclusion = build_indexes(rules)
        self.diseases = sorted(c for c in self.conclusions if c not in SPECIAL_CONCLUSIONS)

        self.setWindowTitle("Medical Symptom Checker Expert System")
        self.resize(900, 600)

        root = QWidget()
        layout = QHBoxLayout()
        root.setLayout(layout)
        self.setCentralWidget(root)

        controls = QVBoxLayout()
        layout.addLayout(controls, 1)

        mode_group = QGroupBox("Reasoning Mode")
        mode_layout = QVBoxLayout()
        mode_group.setLayout(mode_layout)
        self.forward_radio = QRadioButton("Forward Chaining")
        self.backward_radio = QRadioButton("Backward Chaining")
        self.forward_radio.setChecked(True)
        mode_layout.addWidget(self.forward_radio)
        mode_layout.addWidget(self.backward_radio)
        controls.addWidget(mode_group)

        self.mode_buttons = QButtonGroup()
        self.mode_buttons.addButton(self.forward_radio)
        self.mode_buttons.addButton(self.backward_radio)
        self.mode_buttons.buttonToggled.connect(self.refresh_mode)

        self.forward_box = QGroupBox("Select Symptoms")
        forward_layout = QVBoxLayout()
        self.forward_box.setLayout(forward_layout)
        self.symptom_list = QListWidget()
        for symptom in sorted(self.base_symptoms):
            item = QListWidgetItem(symptom)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.symptom_list.addItem(item)
        forward_layout.addWidget(self.symptom_list)
        controls.addWidget(self.forward_box)

        self.backward_box = QGroupBox("Select Disease")
        backward_layout = QVBoxLayout()
        self.backward_box.setLayout(backward_layout)
        self.disease_combo = QComboBox()
        self.disease_combo.addItems(self.diseases)
        backward_layout.addWidget(self.disease_combo)
        controls.addWidget(self.backward_box)

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_reasoning)
        controls.addWidget(self.run_button)

        self.result = QTextEdit()
        self.result.setReadOnly(True)
        layout.addWidget(self.result, 2)

        self.refresh_mode()

    def refresh_mode(self) -> None:
        is_forward = self.forward_radio.isChecked()
        self.forward_box.setVisible(is_forward)
        self.backward_box.setVisible(not is_forward)
        self.result.clear()

    def run_reasoning(self) -> None:
        if self.forward_radio.isChecked():
            self.run_forward()
        else:
            self.run_backward()

    def run_forward(self) -> None:
        selected = set()
        for i in range(self.symptom_list.count()):
            item = self.symptom_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.add(item.text())

        facts, fired = forward_chain(self.rules, selected)
        diseases = [r.conclusion for r in fired if r.conclusion in self.diseases]
        emergency = "seek_emergency_care" in facts or "emergency" in facts

        lines: List[str] = []
        lines.append("Forward chaining results")
        lines.append(f"Selected symptoms: {', '.join(sorted(selected)) if selected else 'none'}")
        lines.append(f"Fired rules: {', '.join(r.rule_id for r in fired) if fired else 'none'}")

        if diseases:
            lines.append("Diagnosed diseases:")
            for rule in fired:
                if rule.conclusion in self.diseases:
                    precautions = "; ".join(rule.precautions) if rule.precautions else "none"
                    lines.append(f"- {rule.conclusion} (Rule {rule.rule_id})")
                    lines.append(f"  Precautions: {precautions}")
        else:
            lines.append("Diagnosed diseases: none")

        if emergency:
            lines.append("Emergency detected. Seek emergency care immediately.")

        self.result.setPlainText("\n".join(lines))

    def run_backward(self) -> None:
        goal = self.disease_combo.currentText()
        lines = ["Backward chaining results", f"Goal disease: {goal}", ""]
        lines.extend(explain_backward(goal, self.by_conclusion, self.base_symptoms, self.conclusions))
        self.result.setPlainText("\n".join(lines))


def main() -> None:
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found at {CSV_PATH}")
    rules = load_rules(CSV_PATH)
    app = QApplication([])
    window = MainWindow(rules)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
