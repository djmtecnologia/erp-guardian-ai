import re
import os

class ImpactAnalyzer:
    def __init__(self, workspace_path):
        self.workspace_path = workspace_path
        self.dependency_graph = {}

    def parse_delphi_uses(self, content):
        """Extract units from uses clauses"""
        # Simple regex for uses clauses (interface and implementation)
        matches = re.findall(r'uses\s+([\s\S]*?);', content, re.IGNORECASE)
        units = []
        for match in matches:
            # Clean and split by comma
            cleaned = match.replace('\n', '').replace(' ', '')
            units.extend(cleaned.split(','))
        return [u.strip() for u in units if u.strip()]

    def parse_sql_references(self, content):
        """Extract table and package names from SQL"""
        # Rough extraction of table names after FROM or JOIN
        tables = re.findall(r'FROM\s+([a-zA-Z0-9_.]+)', content, re.IGNORECASE)
        tables += re.findall(r'JOIN\s+([a-zA-Z0-9_.]+)', content, re.IGNORECASE)
        # Extraction of package calls PKG_NAME.PROCEDURE
        packages = re.findall(r'([a-zA-Z0-9_]+)\.[a-zA-Z0-9_]+', content)
        return list(set(tables + packages))

    def analyze_file(self, filepath):
        with open(filepath, 'r', encoding='latin-1', errors='ignore') as f:
            content = f.read()
            
        if filepath.endswith('.pas'):
            return {"type": "Delphi", "dependencies": self.parse_delphi_uses(content)}
        elif filepath.endswith(('.sql', '.pks', '.pkb')):
            return {"type": "Oracle", "dependencies": self.parse_sql_references(content)}
        return {"type": "Unknown", "dependencies": []}

    def generate_impact_report(self, changed_files):
        """Generate a list of impacted modules based on changes"""
        report = {
            "impacted_modules": [],
            "risk_score": 0,
            "details": []
        }
        
        for file in changed_files:
            analysis = self.analyze_file(file)
            report["details"].append({
                "file": os.path.basename(file),
                "dependencies": analysis["dependencies"]
            })
            # Business logic mapping (Stub)
            # In a real system, we'd map 'UFinancial' unit to 'Financial' module
            if any('Financial' in d or 'Fin' in d for d in analysis["dependencies"]):
                report["impacted_modules"].append("Financial")
            if any('Stock' in d or 'Estoque' in d for d in analysis["dependencies"]):
                report["impacted_modules"].append("Stock")
                
        report["impacted_modules"] = list(set(report["impacted_modules"]))
        report["risk_score"] = len(report["impacted_modules"]) * 20 # Simple heuristic
        
        return report
