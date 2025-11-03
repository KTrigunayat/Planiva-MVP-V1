"""
Vendor-related CrewAI tools for event planning agents
"""

import json
import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from crewai.tools import BaseTool
try:
    from langchain_ollama import OllamaLLM
except ImportError:
    from langchain_community.llms import Ollama as OllamaLLM
from dotenv import load_dotenv
from typing import ClassVar, Type
from pydantic import BaseModel, Field

# Load environment variables for database connection
load_dotenv()


class HybridFilterInput(BaseModel):
    """Input schema for HybridFilterTool"""
    client_data: dict = Field(..., description="Complete client data dictionary containing preferences and requirements")
    service_type: str = Field(..., description="Type of service to filter for (venue, caterer, photographer, makeup_artist)")


class HybridFilterTool(BaseTool):
    """
    Processes structured client JSON using deterministic logic for hard filters 
    and an LLM for nuanced soft preferences.
    
    This tool maintains the existing deterministic logic for hard filters while
    preserving LLM-based soft preference extraction functionality.
    """
    name: str = "Hybrid Client Form Processor"
    description: str = "Processes structured client JSON using deterministic logic for hard filters and an LLM for nuanced soft preferences."
    args_schema: Type[BaseModel] = HybridFilterInput
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = None
    
    @property
    def llm(self):
        if self._llm is None:
            self._llm = OllamaLLM(model="gemma:2b")
        return self._llm

    def _extract_hard_filters(self, client_data: dict, service_type: str) -> dict:
        """
        Extract deterministic hard filters from client data.
        Preserves existing logic for compatibility.
        """
        hard_filters = {}
        vision_text = client_data.get('clientVision', '')
        
        # Extract location from client vision text
        match = re.search(r'\b(in|near)\s([A-Z][a-z]+)\b', vision_text)
        if match:
            hard_filters['location_city'] = match.group(2)
        
        if service_type == 'venue':
            hard_filters['capacity_min'] = max(client_data.get('guestCount', {}).values() or [0])
            hard_filters['required_amenities'] = client_data.get('essentialVenueAmenities', [])
            hard_filters['venue_type'] = client_data.get('venuePreferences', [])
            hard_filters['beverages_allowed'] = client_data.get('foodAndCatering', {}).get('beverages', {}).get('allowed', False)
        
        elif service_type == 'caterer':
            hard_filters['guest_capacity'] = max(client_data.get('guestCount', {}).values() or [0])
            hard_filters['dietary_options'] = client_data.get('foodAndCatering', {}).get('dietaryOptions')
            hard_filters['beverages_allowed'] = client_data.get('foodAndCatering', {}).get('beverages', {}).get('allowed', False)
            if any('live' in c.lower() for c in client_data.get('foodAndCatering', {}).get('cuisinePreferences', [])):
                hard_filters['requires_live_counters'] = True

        elif service_type == 'photographer':
            hard_filters['must_provide_video'] = "videography" in client_data.get('additionalRequirements', {})
            video_reqs = client_data.get('additionalRequirements', {}).get('videography', '')
            required_deliverables = []
            if 'pre-wedding shoot' in video_reqs: 
                required_deliverables.append('pre-wedding shoot')
            if 'same-day edit' in video_reqs: 
                required_deliverables.append('same-day edit')
            if required_deliverables:
                hard_filters['required_deliverables'] = required_deliverables

        elif service_type == 'makeup_artist':
            hard_filters['service_for'] = 'bride'
            hard_filters['on_site_service'] = True

        return hard_filters

    def _extract_soft_preferences_with_llm(self, client_data: dict, service_type: str) -> dict:
        """
        Extract soft preferences using LLM analysis.
        Maintains existing LLM-based preference extraction functionality.
        """
        text_to_analyze = f"Client Vision: {client_data.get('clientVision', '')}\n"
        
        if service_type == 'venue':
            text_to_analyze += f"Desired Theme: {client_data.get('decorationAndAmbiance', {}).get('desiredTheme', '')}"
        elif service_type == 'caterer':
            text_to_analyze += f"Cuisine Preferences: {', '.join(client_data.get('foodAndCatering', {}).get('cuisinePreferences', []))}"
        elif service_type == 'photographer':
            text_to_analyze += f"Photography Style: {client_data.get('additionalRequirements', {}).get('photography', '')}"
        elif service_type == 'makeup_artist':
            text_to_analyze += f"Makeup Artist Requirements: {client_data.get('additionalRequirements', {}).get('makeup', '')}"

        prompt = f"""
        You are a silent, efficient JSON API. You only respond with a single, valid JSON object and nothing else.
        Your task is to analyze the user's text to determine the stylistic wishes (soft_preferences).
        Do not add any text, explanations, or summaries before or after the JSON object.

        --- EXAMPLE ---
        USER REQUEST: "Client Vision: We want a fun, vibrant party. Cuisine Preferences: Italian, Mexican"
        JSON OUTPUT:
        {{
            "style": ["fun", "vibrant"],
            "cuisine": ["Italian", "Mexican"]
        }}
        --- END EXAMPLE ---

        --- TASK ---
        Now, process the following user request. Remember, respond ONLY with the JSON object.

        USER REQUEST:
        "{text_to_analyze}"

        JSON OUTPUT:
        """
        
        response = self.llm.invoke(prompt)
        try:
            return json.loads(response.strip().replace("```json", "").replace("```", ""))
        except json.JSONDecodeError:
            return {"error": "LLM failed to return valid JSON for soft preferences."}

    def _run(self, client_data: dict, service_type: str) -> str:
        """
        Main execution method for the tool.
        Combines hard filters and soft preferences into a structured output.
        """
        hard_filters = self._extract_hard_filters(client_data, service_type)
        soft_preferences = self._extract_soft_preferences_with_llm(client_data, service_type)
        
        final_filter_object = {
            "service_type": service_type,
            "hard_filters": hard_filters,
            "soft_preferences": soft_preferences
        }
        
        return json.dumps(final_filter_object, indent=2)


class VendorDatabaseInput(BaseModel):
    """Input schema for VendorDatabaseTool"""
    filter_json_string: str = Field(..., description="JSON string containing service type, hard filters, and soft preferences")


class VendorDatabaseTool(BaseTool):
    """
    Takes a filter JSON, queries the PostgreSQL database, and ranks the results 
    using an adaptive scoring algorithm with enhanced capabilities.
    
    Preserves existing weighted linear scoring model while adding integration 
    with vendor data MCP server.
    """
    name: str = "Vendor Database Search & Rank Tool"
    description: str = "Takes a filter JSON, queries the PostgreSQL database, and ranks the results using an adaptive scoring algorithm."
    args_schema: Type[BaseModel] = VendorDatabaseInput

    TABLE_CONFIG: ClassVar[dict] = {
        'venue': {
            'table_name': 'venues', 
            'price_col': 'min_veg_price', 
            'weights': {'price': 0.7, 'preference': 0.3}
        },
        'caterer': {
            'table_name': 'caterers', 
            'price_col': 'min_veg_price', 
            'weights': {'price': 0.6, 'preference': 0.4}
        },
        'photographer': {
            'table_name': 'photographers', 
            'price_col': 'photo_package_price', 
            'weights': {'price': 0.4, 'preference': 0.6}
        },
        'makeup_artist': {
            'table_name': 'makeup_artists', 
            'price_col': 'bridal_makeup_price', 
            'weights': {'price': 0.5, 'preference': 0.5}
        }
    }

    def _get_db_connection(self):
        """Get database connection using environment variables"""
        return psycopg2.connect(
            dbname=os.getenv("DB_NAME"), 
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"), 
            host=os.getenv("DB_HOST"), 
            port=os.getenv("DB_PORT")
        )

    def _calculate_preference_score(self, vendor: dict, soft_preferences: dict, service_type: str) -> float:
        """
        Calculate preference score based on soft preferences.
        Maintains existing scoring logic for compatibility.
        """
        score = 0.0
        
        if service_type == 'venue':
            keywords = soft_preferences.get('style_keywords', [])
            about_text = vendor.get('attributes', {}).get('about', '').lower() if vendor.get('attributes') else ''
            matches = sum(1 for keyword in keywords if keyword in about_text)
            score = min(1.0, matches / 2.0)
        
        elif service_type == 'caterer':
            pref_cuisines = set(c.lower() for c in soft_preferences.get('cuisines', []))
            vendor_cuisines_data = vendor.get('attributes', {}).get('cuisines')
            vendor_cuisines = set(c.lower() for c in vendor_cuisines_data if isinstance(c, str)) if vendor_cuisines_data else set()
            matches = len(pref_cuisines.intersection(vendor_cuisines))
            score = min(1.0, matches / 2.0)
        
        return score

    def _run(self, filter_json_string: str) -> str:
        """
        Main execution method for vendor database search and ranking.
        Preserves existing weighted linear scoring model.
        """
        try:
            filters = json.loads(filter_json_string)
            service_type = filters['service_type']
            hard_filters = filters['hard_filters']
            soft_preferences = filters['soft_preferences']
        except (json.JSONDecodeError, KeyError) as e:
            return f"Error: Invalid or incomplete filter JSON provided. Details: {e}"

        if service_type not in self.TABLE_CONFIG:
            return f"Error: Unknown service type '{service_type}'."
        
        config = self.TABLE_CONFIG[service_type]
        table_name = config['table_name']
        price_col = config.get('price_col')
        weights = config['weights']
        budget = hard_filters.get('budget')

        if not budget:
            return "Error: Budget must be provided in hard_filters to perform scoring."

        # Build SQL query with parameterized filters
        query = f"SELECT * FROM {table_name} WHERE 1=1"
        params = []
        
        if 'location_city' in hard_filters:
            query += " AND location_city = %s"
            params.append(hard_filters['location_city'])
        
        if price_col:
            query += f" AND {price_col} IS NOT NULL AND {price_col} <= %s"
            params.append(budget)

        if service_type == 'venue' and 'capacity_min' in hard_filters:
            query += " AND max_seating_capacity >= %s"
            params.append(hard_filters['capacity_min'])
        
        # Execute database query
        conn = self._get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(query, tuple(params))
            candidates = cursor.fetchall()
        except Exception as e:
            conn.close()
            return f"Database query failed: {e}"
        
        cursor.close()
        conn.close()

        # Rank vendors using weighted linear scoring
        ranked_vendors = []
        for vendor in candidates:
            # Calculate price score
            price_score = 0.0
            if price_col:
                price = vendor.get(price_col, 0)
                if price and price > 0:
                    price_score = 1.0 - (price / budget)

            # Calculate preference score
            pref_score = self._calculate_preference_score(vendor, soft_preferences, service_type)

            # Calculate final ranking score using weighted combination
            ranking_score = (weights['price'] * price_score) + (weights['preference'] * pref_score)
            
            vendor['ranking_score'] = round(ranking_score, 4)
            ranked_vendors.append(vendor)

        # Sort by ranking score (highest first)
        ranked_vendors.sort(key=lambda x: x['ranking_score'], reverse=True)
        
        # Convert datetime and UUID objects to strings for JSON serialization
        for vendor in ranked_vendors:
            for key, value in vendor.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    vendor[key] = value.isoformat()
                elif hasattr(value, 'hex'):  # UUID objects
                    vendor[key] = str(value)

        # Return top 5 vendors
        return json.dumps(ranked_vendors[:5], indent=2)


class VendorRankingInput(BaseModel):
    """Input schema for VendorRankingTool"""
    vendors_json_string: str = Field(..., description="JSON string containing list of vendors to rank")
    client_vision: str = Field(..., description="Client's vision text for context")


class VendorRankingTool(BaseTool):
    """
    Enhanced vendor ranking tool that uses LLM for generating vendor summaries.
    Maintains compatibility with existing batch summarization functionality.
    """
    name: str = "Batch Vendor Summarization Tool"
    description: str = "Takes a list of vendors and the client's vision to generate a summary for each vendor in a single call."
    args_schema: Type[BaseModel] = VendorRankingInput
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = None
    
    @property
    def llm(self):
        if self._llm is None:
            self._llm = OllamaLLM(model="gemma:2b")
        return self._llm

    def _run(self, vendors_json_string: str, client_vision: str) -> str:
        """
        Uses an LLM to generate summaries for a full list of vendors in one batch.
        Maintains existing batch summarization logic.
        """
        prompt = f"""
        You are an expert event planner. Your task is to write a short, engaging summary (2-3 sentences) for EACH vendor in the following JSON list.
        
        Respond ONLY with a single, valid JSON object where the keys are the vendor names and the values are their corresponding summaries. Maintain the original order. Do not add any other text.

        CLIENT'S VISION:
        "{client_vision}"

        LIST OF VENDORS:
        "{vendors_json_string}"

        JSON OUTPUT (keys must be vendor names, values must be the summaries):
        """
        
        response = self.llm.invoke(prompt)
        try:
            # Ensure the response is a clean JSON
            return json.dumps(json.loads(response.strip()))
        except json.JSONDecodeError:
            return '{"error": "LLM failed to return a valid JSON object of summaries."}'