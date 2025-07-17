import os
from azure.ai.agents.models import FileInfo, FileSearchTool, VectorStore

LOCAL_INSIDER_NAME = "LocalInsider"
LOCAL_INSIDER_INSTRUCTIONS = """
You are a Local Insider who can provide information about multiple destinations including Madrid, Iceland, and Santorini. 
Your job is to suggest an itinerary for the user for a whole day in their chosen destination including times and prices in Euros for each activity.

CRITICAL RULES:
1. You MUST ALWAYS use the file search tool first before suggesting any activities
2. Search for the specific destination name (Madrid, Iceland, or Santorini) in the vector store
3. ONLY suggest activities that are explicitly mentioned in the search results
4. If no relevant activities are found in the search results, say "I couldn't find specific activities for [destination] in my diary. Please try a different destination."
5. NEVER make up activities or use general knowledge - only use what's in the diary entries

Your goal is to get the approval of the Travel Expert. 
Always begin with the most expensive activities in the itinerary and then gradually swap out one high cost activity for a lower cost one each time the travel expert declines until the Travel Expert approves.
Do not ask any questions, do not give the total cost, and do not convert to NZD. Just suggest the itinerary.
""" 

async def load_file_search_tool(client):
    """
    Uploads multiple PDF files, creates the vector store, and returns the FileSearchTool and its resources.
    """
    # Define the PDF files to upload
    pdf_files = [
        "madrid_diary.pdf",
        "iceland_diary.pdf", 
        "santorini_diary.pdf"
    ]
    
    resources_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "resources"
    )
    
    file_ids = []
    
    # Upload each PDF file
    for pdf_file in pdf_files:
        pdf_file_path = os.path.join(resources_dir, pdf_file)
        
        # Check if file exists before uploading
        if os.path.exists(pdf_file_path):
            file: FileInfo = await client.agents.files.upload_and_poll(
                file_path=pdf_file_path,
                purpose="assistants",
            )
            file_ids.append(file.id)
            print(f"Uploaded {pdf_file} with ID: {file.id}")
        else:
            print(f"Warning: {pdf_file} not found at {pdf_file_path}")

    # Create the vector store with all uploaded files
    vector_store: VectorStore = await client.agents.vector_stores.create_and_poll(
        file_ids=file_ids,
        name="multi_destination_vectorstore",
    )

    # Create the file search tool
    file_search = FileSearchTool(vector_store_ids=[vector_store.id])

    # Return everything you'll need
    return file_search, file_ids, vector_store