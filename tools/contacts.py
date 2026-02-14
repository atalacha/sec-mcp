from typing import Any, Dict
from .base import BaseTool

class GetListContacts(BaseTool):
    name = "get_list_contacts"
    description = "Retrieves a list of contacts from your Google Account."
    
    input_schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "description": "Max number of contacts to return (default 10)"}
        }
    }

    def __init__(self, people_service):
        self.service = people_service  # Store the authenticated service

    async def run(self, arguments: Dict[str, Any]) -> str:
        limit = arguments.get("limit", 10)
        
        # Call Google People API
        results = self.service.people().connections().list(
            resourceName='people/me',
            pageSize=limit,
            personFields='names,emailAddresses'
        ).execute()
        
        connections = results.get('connections', [])
        
        # Simplify output for the LLM
        simple_list = []
        for person in connections:
            names = person.get('names', [])
            emails = person.get('emailAddresses', [])
            if names:
                simple_list.append(f"{names[0].get('displayName')} ({emails[0].get('value') if emails else 'No Email'})")
                
        return "\n".join(simple_list) if simple_list else "No contacts found."


class CreateContacts(BaseTool):
    name = "create_contacts"
    description = "Creates a new contact in your Google Account."
    
    input_schema = {
        "type": "object",
        "properties": {
            "givenName": {"type": "string", "description": "First name"},
            "familyName": {"type": "string", "description": "Last name"},
            "email": {"type": "string", "description": "Email address"}
        },
        "required": ["givenName"]
    }

    def __init__(self, people_service):
        self.service = people_service

    async def run(self, arguments: Dict[str, Any]) -> str:
        contact_body = {
            "names": [{
                "givenName": arguments["givenName"],
                "familyName": arguments.get("familyName", "")
            }],
            "emailAddresses": [{
                "value": arguments.get("email", "")
            }]
        }
        
        self.service.people().createContact(body=contact_body).execute()
        return f"Successfully created contact for {arguments['givenName']}."
