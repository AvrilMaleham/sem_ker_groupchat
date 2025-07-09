# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentGroupChat, AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.contents import AuthorRole

"""
This sample demonstrates two LLM agents:
Chef Bot: Imagines recipes
Nutrition Coach: Checks meal plans and gives health advice

They 'chat' in a loop until the Nutrition Coach says it's approved.
"""

class MealApprovalTerminationStrategy(TerminationStrategy):
    """Ends the chat when the Nutrition Coach approves the meal."""

    async def should_agent_terminate(self, agent, history):
        return "meal approved" in history[-1].content.lower()


CHEF_NAME = "ChefBot"
CHEF_INSTRUCTIONS = """
You are a chef. 
Your job is to suggest a meal recipe with a short ingredient list based on the user input, each ingredient should include the quantity. 
Your goal is to get the approval of the Nutrition Coach. 
Always begin with a high calorie meal suggestion and then gradually suggest lower calorie meals each time the nutrition coach declines until the Nutrition Coach approves.
Do not ask any questions, just suggest a meal.
"""

COACH_NAME = "NutritionCoach"
COACH_INSTRUCTIONS = """
You are a nutrition coach. 
You recieve the recipe from the chef and calculate how many calories it will contain based on each ingredient and the quantity. 
The calorie limit is 400 calories.
If the meal is under 400 calories, say meal approved. 
If the meal is over 400 calories, say it's not approved and ask the chef to suggest a different recipe.
"""


async def main():
    model_deployment_name = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-4o")

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create the Chef agent
        chef_definition = await client.agents.create_agent(
            model=model_deployment_name,
            name=CHEF_NAME,
            instructions=CHEF_INSTRUCTIONS,
        )

        chef_agent = AzureAIAgent(
            client=client,
            definition=chef_definition,
        )

        # 2. Create the Nutrition Coach agent
        coach_definition = await client.agents.create_agent(
            model=model_deployment_name,
            name=COACH_NAME,
            instructions=COACH_INSTRUCTIONS,
        )

        coach_agent = AzureAIAgent(
            client=client,
            definition=coach_definition,
        )

        # 3. Put them in a group chat with custom termination
        chat = AgentGroupChat(
            agents=[chef_agent, coach_agent],
            termination_strategy=MealApprovalTerminationStrategy(
                agents=[coach_agent], maximum_iterations=10
            ),
        )

        try:
            print("Welcome to the Chef + Nutrition Coach Group Chat!")
            print("Type 'exit' or 'quit' to end the chat.\n")
            user_input = input("What meal do you want? ").strip()

            while user_input.lower() not in ("exit", "quit"):
                await chat.add_chat_message(message=user_input)
                print(f"# {AuthorRole.USER}: '{user_input}'")

                async for content in chat.invoke():
                    print(f"# {content.role} - {content.name or '*'}: '{content.content}'")

                user_input = input("\nYour next request: ").strip()

        finally:
            await chat.reset()
            await client.agents.delete_agent(chef_definition.id)
            await client.agents.delete_agent(coach_definition.id)


if __name__ == "__main__":
    asyncio.run(main())
