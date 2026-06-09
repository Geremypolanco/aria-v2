from src.agents.income_executor import income_executor

class Orchestrator:
    def execute(self, user_input: str):
        text = user_input.lower()
        if any(kw in text for kw in ['curso', 'ebook', 'bundle', 'genera', 'ingreso']):
            return income_executor.execute('generate_course' if 'curso' in text else 'generate_ebook')
        return {'action': 'respond', 'result': {'message': f'Procesado: {user_input}'}}

orchestrator = Orchestrator()