import os
from autogen import ConversableAgent
from typing import Dict, List, Any
try:
    from config_sqlite import get_llm_config
except ImportError:
    from config import get_llm_config
from utils.document_processor import create_document_processor
from database.models import CitibankTransaction, ConcurTransaction, Event, ProcessingLog
from database import SessionLocal
from datetime import datetime


def create_data_ingestion_agent():
    """Create a data ingestion agent for processing Excel files"""
    
    llm_config = get_llm_config()
    
    def process_excel_files(message: str) -> str:
        """Process Excel files (Citibank and Concur transactions)"""
        try:
            db = SessionLocal()
            processor = create_document_processor()
            
            # Parse message to extract file paths and types
            import json
            data = json.loads(message)
            
            results = []
            
            for file_info in data.get("files", []):
                file_path = file_info["path"]
                file_type = file_info["type"]  # "citibank" or "concur"
                
                # Log processing start
                log = ProcessingLog(
                    process_type="ingestion",
                    status="started",
                    message=f"Processing {file_type} file: {file_path}",
                    started_at=datetime.utcnow()
                )
                db.add(log)
                db.commit()
                
                try:
                    # Process the Excel file
                    transactions = processor.process_excel_file(file_path, file_type)
                    
                    # Store transactions in database
                    stored_count = 0
                    for trans_data in transactions:
                        if file_type.lower() == "citibank":
                            # Create or update event
                            event = db.query(Event).filter(
                                Event.event_id == trans_data["event_id"]
                            ).first()
                            
                            if not event:
                                event = Event(event_id=trans_data["event_id"])
                                db.add(event)
                                db.commit()
                            
                            # Create transaction
                            transaction = CitibankTransaction(**trans_data)
                            db.add(transaction)
                            stored_count += 1
                            
                        elif file_type.lower() == "concur":
                            # Create or update event
                            event = db.query(Event).filter(
                                Event.event_id == trans_data["event_id"]
                            ).first()
                            
                            if not event:
                                event = Event(event_id=trans_data["event_id"])
                                db.add(event)
                                db.commit()
                            
                            # Create transaction
                            transaction = ConcurTransaction(**trans_data)
                            db.add(transaction)
                            stored_count += 1
                    
                    db.commit()
                    
                    # Update log
                    log.status = "completed"
                    log.completed_at = datetime.utcnow()
                    log.message = f"Successfully processed {stored_count} transactions from {file_path}"
                    db.commit()
                    
                    results.append({
                        "file": file_path,
                        "type": file_type,
                        "status": "success",
                        "transactions_processed": stored_count
                    })
                    
                except Exception as e:
                    # Update log with error
                    log.status = "error"
                    log.completed_at = datetime.utcnow()
                    log.error_details = {"error": str(e)}
                    db.commit()
                    
                    results.append({
                        "file": file_path,
                        "type": file_type,
                        "status": "error",
                        "error": str(e)
                    })
            
            db.close()
            
            return json.dumps({
                "status": "completed",
                "results": results,
                "message": f"Processed {len(data.get('files', []))} files"
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Failed to process Excel files"
            })
    
    # Create the data ingestion agent
    ingestion_agent = ConversableAgent(
        name="data_ingestion_agent",
        system_message="""You are a Data Ingestion Agent specialized in processing financial transaction data.

Your responsibilities:
1. Process Citibank transaction Excel files
2. Process Concur transaction Excel files  
3. Extract transaction data and store in PostgreSQL database
4. Group transactions by Event ID
5. Handle data validation and error reporting
6. Log all processing activities

When you receive file processing requests, you should:
1. Parse the Excel files using pandas
2. Validate data integrity (required fields, data types)
3. Store transactions in appropriate database tables
4. Create Event records for new Event IDs
5. Report processing statistics and any errors

Input format expected:
{
    "files": [
        {
            "path": "/path/to/citibank.xlsx",
            "type": "citibank"
        },
        {
            "path": "/path/to/concur.xlsx", 
            "type": "concur"
        }
    ]
}

Always provide detailed status reports and handle errors gracefully.""",
        llm_config=llm_config,
        code_execution_config=False,
        function_map={"process_excel_files": process_excel_files},
        human_input_mode="NEVER",
    )
    
    return ingestion_agent 