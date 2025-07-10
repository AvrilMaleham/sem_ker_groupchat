# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentGroupChat, AzureAIAgent
from semantic_kernel.contents import AuthorRole

from agents.local_insider import LOCAL_INSIDER_NAME, LOCAL_INSIDER_INSTRUCTIONS, load_file_search_tool
from agents.travel_expert import TRAVEL_EXPERT_NAME, TRAVEL_EXPERT_INSTRUCTIONS, load_openapi_tools
from agents.termination_strategy import ItineraryApprovalTerminationStrategy

"""
This sample demonstrates two LLM agents:
Local Insider: Suggests a madrid itinerary from their diaries in a vector store with prices in Euros
Travel Expert: Adds the total cost of the itinerary and converts to NZD using an API

The user inputs their budget in NZD and the Local Insider suggests an itinerary.
The agents 'chat' in a loop until the Travel says the itinerary is within budget.
"""


async def main():
    model_deployment_name = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-4o")

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
    
        file_search, file, vector_store = await load_file_search_tool(client)
        
        



        local_insider_definition = await client.agents.create_agent(
            model=model_deployment_name,
            name=LOCAL_INSIDER_NAME,
            instructions=LOCAL_INSIDER_INSTRUCTIONS,
            tools=file_search.definitions,
            tool_resources=file_search.resources,
        )

        local_insider_agent = AzureAIAgent(
            client=client,
            definition=local_insider_definition,
        )


        openapi_tools = load_openapi_tools()

        travel_expert_definition = await client.agents.create_agent(
            model=model_deployment_name,
            name=TRAVEL_EXPERT_NAME,
            instructions=TRAVEL_EXPERT_INSTRUCTIONS,
            tools=openapi_tools.definitions,
        )

        travel_expert_agent = AzureAIAgent(
            client=client,
            definition=travel_expert_definition,
        )

   
        chat = AgentGroupChat(
            agents=[local_insider_agent, travel_expert_agent],
            termination_strategy=ItineraryApprovalTerminationStrategy(
                agents=[travel_expert_agent], maximum_iterations=10
            ),
        )

        try:
            print("Welcome to the Bespoke Travel Agency!")
            print("Type 'exit' or 'quit' to end the chat.\n")
            user_input = input("Where would you like to go? ").strip()

            while user_input.lower() not in ("exit", "quit"):
                await chat.add_chat_message(message=user_input)
                print(f"# {AuthorRole.USER}: '{user_input}'")

                async for content in chat.invoke():
                    print(f"# {content.role} - {content.name or '*'}: '{content.content}'")

                user_input = input("\nYour next request: ").strip()

        finally:
            await chat.reset()
            await client.agents.delete_agent(local_insider_definition.id)
            await client.agents.delete_agent(travel_expert_definition.id)
            await client.agents.vector_stores.delete(vector_store.id)
            await client.agents.files.delete(file.id)
            


if __name__ == "__main__":
    asyncio.run(main())
