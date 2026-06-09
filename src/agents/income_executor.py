class IncomeExecutor:
    def execute(self, action):
        return {'status': 'success', 'message': f'Acción {action} ejecutada', 'price': 97}

income_executor = IncomeExecutor()