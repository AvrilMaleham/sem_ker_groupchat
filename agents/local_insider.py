import os
from azure.ai.agents.models import FileInfo, FileSearchTool, VectorStore

LOCAL_INSIDER_NAME = "LocalInsider"
LOCAL_INSIDER_INSTRUCTIONS = """
You are a Local Insider in Madrid. 
Your job is to suggest an itinerary for the user for a whole day in Madrid including times and prices in Euros for each activity.
You have a tool, load_file_search_tool(), which retrieves the diary entries from the vector store. Only suggest activities that are in the diary.
Your goal is to get the approval of the Travel Expert. 
Always begin with the most expensive activities in the itenerary and then gradually swap out one high cost activity for a lower cost one each time the travel expert declines until the Travel Expert approves.
Do not ask any questions, do not give the total cost, and do not convert to NZD. Just suggest the itinerary.
""" 

async def load_file_search_tool(client):
    """
    Uploads the file, creates the vector store, and returns the FileSearchTool and its resources.
    """
    pdf_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "resources",
        "madrid_diary.pdf"
    )

    # Upload the file
    file: FileInfo = await client.agents.files.upload_and_poll(
        file_path=pdf_file_path,
        purpose="assistants",
    )

    # Create the vector store
    vector_store: VectorStore = await client.agents.vector_stores.create_and_poll(
        file_ids=[file.id],
        name="my_vectorstore",
    )

    # Create the file search tool
    file_search = FileSearchTool(vector_store_ids=[vector_store.id])

    # Return everything you’ll need
    return file_search, file, vector_store