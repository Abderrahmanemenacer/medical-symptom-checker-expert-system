import webview
import os
import sys
from engine import ExpertSystem

class Api:
    def __init__(self):
        # Initialize the expert system
        self.system = ExpertSystem('knowledge_base_15_rules_forward_chaining_15.csv')

    def get_symptoms(self):
        """Expose observable symptoms to the UI."""
        return self.system.get_observable_symptoms()

    def get_conclusions(self):
        """Expose all possible conclusions/diseases to the UI."""
        return self.system.get_all_conclusions()

    def run_diagnosis(self, selected_symptoms):
        """Execute forward chaining and return serializable results."""
        fired_rules, known_facts = self.system.forward_chaining(selected_symptoms)
        
        # Convert Rule objects to dictionaries for JSON serialization
        results = {
            'fired_rules': [
                {
                    'rule_id': r.rule_id,
                    'conditions': r.conditions,
                    'conclusion': r.conclusion,
                    'precautions': r.precautions
                } for r in fired_rules
            ],
            'known_facts': list(known_facts)
        }
        return results

    def run_verification(self, target_disease, user_symptoms):
        """Execute backward verification and return results."""
        success, trace = self.system.backward_verification(target_disease, user_symptoms)
        return {
            'success': success,
            'trace': trace
        }

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    api = Api()
    
    # Path to the web directory
    web_dir = f"{os.getcwd()}/web"#get_resource_path('web')
    index_html = os.path.join(web_dir, 'index.html')

    # Create the window
    window = webview.create_window(
        'ArtDoc AI - Medical Expert System', 
        index_html, 
        js_api=api,
        width=1200,
        height=850,
        background_color='#f8fafc'
    )

    # Start the app
    # gui='edgechromium' is preferred on Windows for modern features
    # webview.start(debug=True)
    webview.start()