import json
import csv
import os

class Rule:
    def __init__(self, rule_id, conditions, conclusion, precautions):
        self.rule_id = rule_id
        self.conditions = conditions  # List of strings
        self.conclusion = conclusion  # String
        self.precautions = precautions  # String

    def __repr__(self):
        return f"Rule({self.rule_id}: {self.conditions} -> {self.conclusion})"

class ExpertSystem:
    def __init__(self, file_path):
        self.rules = []
        try:
            self.load_rules(file_path)
        except Exception as e:
            print(f"Error loading rules: {e}")

    def load_rules(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            self._load_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _load_json(self, json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                self.rules.append(Rule(
                    item['rule_id'],
                    item['conditions'],
                    item['conclusion'],
                    item.get('precautions', "Consult a doctor.")
                ))

    def _load_csv(self, csv_path):
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
        """Returns symptoms that are not conclusions of other rules (leaf inputs)."""
        all_conclusions = set(r.conclusion for r in self.rules)
        all_conditions = set()
        for rule in self.rules:
            for c in rule.conditions:
                all_conditions.add(c)
        
        observable = all_conditions - all_conclusions
        return sorted(list(observable))

    def get_all_conclusions(self):
        return sorted(list(set(r.conclusion for r in self.rules)))

    def forward_chaining(self, selected_symptoms):
        """
        Derive all possible diseases from selected symptoms.
        Returns: matching_rules (list), known_facts (set)
        """
        known_facts = set(selected_symptoms)
        fired_rules = []
        
        while True:
            new_rule_fired = False
            for rule in self.rules:
                if rule in fired_rules:
                    continue
                
                # Check if all conditions are met
                if all(c in known_facts for c in rule.conditions):
                    if rule.conclusion not in known_facts:
                        known_facts.add(rule.conclusion)
                        new_rule_fired = True
                    fired_rules.append(rule)
            
            if not new_rule_fired:
                break
                
        return fired_rules, known_facts

    def backward_verification(self, target_disease, user_symptoms):
        """
        Verify if target_disease is supported by user_symptoms.
        Returns: (is_confirmed, trace_log)
        """
        known_facts = set(user_symptoms)
        trace_log = []
        
        def check_goal(goal, depth=0):
            indent = "&nbsp;" * (depth * 4)
            
            if goal in known_facts:
                trace_log.append(f"{indent}<span style='color:green'>[OK] Fact '{goal}' detected.</span>")
                return True

            candidate_rules = [r for r in self.rules if r.conclusion == goal]
            
            if not candidate_rules:
                trace_log.append(f"{indent}<span style='color:red'>[MISSING] '{goal}' not found in symptoms.</span>")
                return False
            
            for rule in candidate_rules:
                trace_log.append(f"{indent}Checking Rule {rule.rule_id} for '{goal}'...")
                
                all_conditions_met = True
                for condition in rule.conditions:
                    if not check_goal(condition, depth + 1):
                        all_conditions_met = False
                        break
                
                if all_conditions_met:
                    trace_log.append(f"{indent}<span style='color:blue'>[SUCCESS] Rule {rule.rule_id} fired. '{goal}' confirmed.</span>")
                    known_facts.add(goal) 
                    return True
            
            trace_log.append(f"{indent}<span style='color:orange'>[FAIL] Could not establish '{goal}'.</span>")
            return False

        result = check_goal(target_disease)
        return result, trace_log