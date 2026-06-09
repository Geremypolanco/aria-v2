from src.agents.income_executor import income_executor

class Orchestrator:
    def execute(self, user_input: str):
        text = user_input.lower()
        
        if any(kw in text for kw in ["curso", "genera curso", "crea curso"]):
            return income_executor.execute("generate_course", {"topic": user_input})
        
        if any(kw in text for kw in ["ebook", "genera ebook"]):
            return income_executor.execute("generate_ebook", {"topic": user_input})
        
        if "bundle" in text or "paquete" in text:
            return income_executor.execute("create_bundle")
        
        if any(kw in text for kw in ["mejora", "evoluciona", "optimiza"]):
            return {"action": "self_improve", "result": {"message": "Auto-mejora activada"}}
        
        return {"action": "respond", "result": {"message": f"Procesado: {user_input}"}}

orchestrator = Orchestrator()