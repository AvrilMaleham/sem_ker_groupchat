import json
import os

from dotenv import load_dotenv
from azure.ai.agents.models import OpenApiAnonymousAuthDetails, OpenApiTool

load_dotenv()

TRAVEL_EXPERT_NAME = "TravelExpert"
TRAVEL_EXPERT_INSTRUCTIONS = """
You are a travel expert. 
You receive the itinerary from the local insider and calculate how much it will cost in total in Euros. You will then convert the total cost to NZD using the currency conversion tool.

IMPORTANT: You MUST use the get_convert tool to get the current exchange rates from EUR. The tool requires:
- base: "EUR" (the base currency)

The API will return exchange rates for EUR to all currencies. Look for the "NZD" rate in the response and multiply the total Euro cost by that rate to get the NZD equivalent.

The budget is 100 NZD per day.
If the converted amount is under 50 NZD, say exactly the words "itinerary approved".
If the converted amount is over 50 NZD, say "it's not approved" and ask the local insider to suggest a cheaper itinerary.

Do not ask any questions. And do not mention what the budget is.
Always use the currency conversion tool when you receive an itinerary with costs in Euros.
""" 

def load_openapi_tools():
    openapi_spec_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "resources",
    )

    with open(os.path.join(openapi_spec_file_path, "convert.json")) as convert_file:
        convert_openapi_spec = json.loads(convert_file.read())

    auth = OpenApiAnonymousAuthDetails()

    openapi_convert = OpenApiTool(
        name="get_convert",
        spec=convert_openapi_spec,
        description="Get current exchange rates for a base currency. Use this tool to get EUR exchange rates, then find the NZD rate to convert Euro amounts to NZD. Required parameter: base (currency code like 'EUR').",
        auth=auth,
        
    )

    return openapi_convert
