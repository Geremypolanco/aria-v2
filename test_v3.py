import asyncio
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.orchestrator.v3 import orchestrator_v3

async def test_run():
    print("--- Testing ARIA ENGINE v3.0 Orchestrator ---")
    async for chunk in orchestrator_v3.run("Crear una imagen de un gato astronauta"):
        print(chunk, end="")
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_run())
