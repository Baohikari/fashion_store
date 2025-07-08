from agent.tools.customer_tools.customer import customer_tools
from agent.tools.manager_tools.manager import manager_tools
import traceback
from google.adk.agents import Agent

# Combine both tool sets
all_tools = customer_tools + manager_tools  # cả hai đều là list[function]

try:
    root_agent = Agent(
        name="fashion_store_helper",
        model="gemini-2.0-flash-exp",
        description=(
            "You are a smart fashion assistant for an online fashion store. "
            "You help customers with product discovery and style suggestions, "
            "and assist managers with product management and sales analysis."
        ),
        tools=all_tools,
    )
except Exception as e:
    print("🚨 Agent creation failed:")
    traceback.print_exc()
    raise e
# --- Custom Agent with prompt routing logic (optional) ---
class FashionStoreAgent(Agent):
    def __init__(self):
        super().__init__(
            name="fashion_store_helper",
            model="gemini-2.0-flash-exp",
            description=(
                "You are a smart fashion assistant for an online fashion store. "
                "Determine whether the user is a customer or manager and use appropriate tools."
            ),
            tools=all_tools,
        )

    def determine_user_type(self, prompt: str) -> str:
        manager_keywords = [
            "add product", "update product", "delete product",
            "remove product", "sales", "report", "top selling",
            "revenue", "analytics", "inventory", "stock", "manage"
        ]
        return "manager" if any(kw in prompt.lower() for kw in manager_keywords) else "customer"

    async def run(self, prompt: str, **kwargs):
        user_type = self.determine_user_type(prompt)
        enhanced_prompt = f"[{user_type.upper()} MODE] {prompt}"
        return await super().run(enhanced_prompt, **kwargs)


custom_fashion_agent = FashionStoreAgent()

__all__ = ["root_agent", "custom_fashion_agent"]
