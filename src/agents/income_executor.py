from src.core.capabilities import get_high_priority_tools

class IncomeExecutor:
    def execute(self, action: str, params: dict = None):
        if params is None: params = {}
        
        tools = get_high_priority_tools()
        
        if action == "generate_course":
            topic = params.get("topic", "Agentes IA")
            return {"status": "success", "type": "course", "title": f"Masterclass: {topic}", "price": 97, "message": f"Curso '{topic}' generado"}
        
        if action == "generate_ebook":
            topic = params.get("topic", "Sistemas Autónomos")
            return {"status": "success", "type": "ebook", "title": f"{topic} - Guía", "price": 47, "message": f"Ebook '{topic}' generado"}
        
        if action == "create_bundle":
            return {"status": "success", "type": "bundle", "price": 127, "message": "Bundle creado exitosamente"}
        
        return {"status": "error", "message": f"Acción desconocida: {action}"}

income_executor = IncomeExecutor()