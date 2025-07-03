import base64
import os
from typing import List, Dict, Any
import pandas as pd
from PIL import Image
import PyPDF2
from pdf2image import convert_from_path
import io
try:
    from config_sqlite import get_llm_config
except ImportError:
    from config import get_llm_config
import openai
from datetime import datetime
import json


class DocumentProcessor:
    def __init__(self):
        self.llm_config = get_llm_config()
        # Initialize OpenAI client with Azure settings
        config = self.llm_config["config_list"][0]
        self.client = openai.AzureOpenAI(
            api_key=config["api_key"],
            api_version=config["api_version"],
            azure_endpoint=config["base_url"]
        )
    
    def process_excel_file(self, file_path: str, file_type: str) -> List[Dict]:
        """Process Excel files (Citibank or Concur transactions)"""
        try:
            df = pd.read_excel(file_path)
            
            if file_type.lower() == "citibank":
                return self._process_citibank_excel(df)
            elif file_type.lower() == "concur":
                return self._process_concur_excel(df)
            else:
                raise ValueError(f"Unknown file type: {file_type}")
                
        except Exception as e:
            print(f"Error processing Excel file {file_path}: {str(e)}")
            return []
    
    def _process_citibank_excel(self, df: pd.DataFrame) -> List[Dict]:
        """Process Citibank transaction Excel file"""
        transactions = []
        
        for _, row in df.iterrows():
            transaction = {
                "transaction_id": str(row.get("Transaction ID", "")),
                "event_id": str(row.get("Event ID", "")),
                "amount": float(row.get("Amount", 0)),
                "currency": str(row.get("Currency", "USD")),
                "transaction_date": pd.to_datetime(row.get("Date")).to_pydatetime(),
                "description": str(row.get("Description", "")),
                "vendor_name": str(row.get("Vendor", "")),
                "card_number": str(row.get("Card Number", "")),
                "raw_data": row.to_dict()
            }
            transactions.append(transaction)
            
        return transactions
    
    def _process_concur_excel(self, df: pd.DataFrame) -> List[Dict]:
        """Process Concur transaction Excel file"""
        transactions = []
        
        for _, row in df.iterrows():
            transaction = {
                "transaction_id": str(row.get("Transaction ID", "")),
                "event_id": str(row.get("Event ID", "")),
                "amount": float(row.get("Amount", 0)),
                "currency": str(row.get("Currency", "USD")),
                "transaction_date": pd.to_datetime(row.get("Date")).to_pydatetime(),
                "expense_type": str(row.get("Expense Type", "")),
                "vendor_name": str(row.get("Vendor", "")),
                "description": str(row.get("Description", "")),
                "participant_id": str(row.get("Participant ID", "")),
                "raw_data": row.to_dict()
            }
            transactions.append(transaction)
            
        return transactions
    
    def extract_expenses_from_document(self, file_path: str, event_id: str) -> List[Dict]:
        """Extract expense data from document using multimodal LLM"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path, event_id)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                return self._extract_from_image(file_path, event_id)
            else:
                print(f"Unsupported file type: {file_extension}")
                return []
                
        except Exception as e:
            print(f"Error extracting expenses from {file_path}: {str(e)}")
            return []
    
    def _extract_from_pdf(self, file_path: str, event_id: str) -> List[Dict]:
        """Extract expenses from PDF using multimodal LLM"""
        try:
            # Convert PDF to images
            images = convert_from_path(file_path)
            all_expenses = []
            
            for i, image in enumerate(images):
                # Convert PIL image to base64
                image_base64 = self._pil_to_base64(image)
                expenses = self._call_multimodal_llm(image_base64, event_id, f"page_{i+1}")
                all_expenses.extend(expenses)
            
            return all_expenses
            
        except Exception as e:
            print(f"Error processing PDF {file_path}: {str(e)}")
            return []
    
    def _extract_from_image(self, file_path: str, event_id: str) -> List[Dict]:
        """Extract expenses from image using multimodal LLM"""
        try:
            # Open and convert image to base64
            with Image.open(file_path) as image:
                image_base64 = self._pil_to_base64(image)
                return self._call_multimodal_llm(image_base64, event_id, "image")
                
        except Exception as e:
            print(f"Error processing image {file_path}: {str(e)}")
            return []
    
    def _pil_to_base64(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def _call_multimodal_llm(self, image_base64: str, event_id: str, source: str) -> List[Dict]:
        """Call multimodal LLM to extract expense data from image"""
        try:
            prompt = f"""
            Please analyze this expense document/receipt and extract ALL expense items. 
            For each expense item found, provide the following information in JSON format:
            
            {{
                "event_id": "{event_id}",
                "amount": <numeric_amount>,
                "currency": "<currency_code>",
                "expense_date": "<YYYY-MM-DD>",
                "expense_type": "<type_of_expense>",
                "vendor_name": "<vendor_or_merchant_name>",
                "description": "<expense_description>",
                "confidence_score": <0.0_to_1.0>,
                "source": "{source}"
            }}
            
            Rules:
            1. Extract ALL individual expense items, not just totals
            2. If multiple items are on one receipt, list them separately
            3. Use standard expense types: "meals", "accommodation", "transportation", "supplies", etc.
            4. Format dates as YYYY-MM-DD
            5. Include currency symbols if visible
            6. Confidence score should reflect how certain you are about the data
            7. If you can't read a field clearly, use null and lower confidence
            
            Return ONLY a JSON array of expense objects, no other text.
            """
            
            response = self.client.chat.completions.create(
                model=self.llm_config["config_list"][0]["model"],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                expenses_data = json.loads(response_text)
                if isinstance(expenses_data, list):
                    return expenses_data
                else:
                    return [expenses_data]
            except json.JSONDecodeError:
                print(f"Failed to parse LLM response as JSON: {response_text}")
                return []
                
        except Exception as e:
            print(f"Error calling multimodal LLM: {str(e)}")
            return []


def create_document_processor() -> DocumentProcessor:
    """Factory function to create document processor"""
    return DocumentProcessor() 