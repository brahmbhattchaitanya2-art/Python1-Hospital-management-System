import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MedicalAI:
    def __init__(self):
        try:
            # Configure the API
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
                
            genai.configure(api_key=api_key)
            
            # Initialize the model
            self.model = genai.GenerativeModel('gemini-flash-latest')
            self.available = True
        except Exception as e:
            print(f"AI Module failed to initialize: {e}")
            self.available = False

    def predict_treatment(self, symptoms, patient_history):
        if not self.available:
            return {"error": "AI System Offline", "risk_level": "Unknown"}

        prompt = f"""
        Act as a Senior Medical Assistant.
        Analyze these symptoms: {symptoms}
        Patient History: {patient_history}

        Provide a diagnosis and treatment plan.
        Output MUST be strictly valid JSON with no markdown formatting.
        Required fields:
        - diagnosis (string)
        - treatment_plan (string)
        - suggested_rx (list of strings)
        - resources (list of strings, e.g., "Oxygen", "Bed")
        - risk_level (string: "Low", "Medium", "High")
        """

        try:
            response = self.model.generate_content(prompt)
            text_response = response.text
            
            # Clean possible markdown backticks
            if "```json" in text_response:
                text_response = text_response.replace("```json", "").replace("```", "")
            elif "```" in text_response:
                 text_response = text_response.replace("```", "")
            
            ai_data = json.loads(text_response.strip())
            ai_data["disclaimer"] = "⚠️ AI SUGGESTION ONLY. Doctor must verify before approval."
            return ai_data
            
        except Exception as e:
            print(f"Prediction Error: {e}")
            return self._fallback_response()

    def _fallback_response(self):
        return {
            "diagnosis": "Currently facing technical difficulties",
            "treatment_plan": "Please consult a doctor directly.",
            "suggested_rx": [],
            "resources": [],
            "risk_level": "Unknown",
            "disclaimer": "⚠️ AI SUGGESTION ONLY. Doctor must verify before approval."
        }
