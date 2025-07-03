import os
from autogen import ConversableAgent
from typing import Dict, List, Any
try:
    from config_sqlite import get_llm_config
except ImportError:
    from config import get_llm_config
from utils.document_processor import create_document_processor
from database.models import ExpenseDocument, ExtractedExpense, Event, ProcessingLog
from database import SessionLocal
from datetime import datetime
import json


def create_document_processing_agent():
    """Create a document processing agent for extracting expenses from Cvent documents"""
    
    llm_config = get_llm_config()
    
    def process_cvent_documents(message: str) -> str:
        """Process Cvent expense documents using multimodal LLM"""
        try:
            db = SessionLocal()
            processor = create_document_processor()
            
            # Parse message to extract file information
            data = json.loads(message)
            event_id = data.get("event_id")
            documents = data.get("documents", [])
            
            # Log processing start
            log = ProcessingLog(
                event_id=event_id,
                process_type="document_processing",
                status="started",
                message=f"Processing {len(documents)} Cvent documents for event {event_id}",
                started_at=datetime.utcnow()
            )
            db.add(log)
            db.commit()
            
            results = []
            total_expenses_extracted = 0
            
            for doc_info in documents:
                file_path = doc_info["path"]
                file_name = os.path.basename(file_path)
                file_type = os.path.splitext(file_path)[1].lower()
                
                try:
                    # Create document record
                    expense_doc = ExpenseDocument(
                        event_id=event_id,
                        document_name=file_name,
                        document_path=file_path,
                        document_type=file_type,
                        processing_status="processing"
                    )
                    db.add(expense_doc)
                    db.commit()
                    
                    # Extract expenses using multimodal LLM
                    extracted_data = processor.extract_expenses_from_document(file_path, event_id)
                    
                    # Store extracted expenses
                    expenses_count = 0
                    for expense_data in extracted_data:
                        # Validate required fields
                        if not expense_data.get("amount") or not expense_data.get("expense_date"):
                            continue
                        
                        try:
                            # Parse date if it's a string
                            if isinstance(expense_data["expense_date"], str):
                                expense_date = datetime.strptime(expense_data["expense_date"], "%Y-%m-%d")
                            else:
                                expense_date = expense_data["expense_date"]
                            
                            extracted_expense = ExtractedExpense(
                                document_id=expense_doc.id,
                                event_id=event_id,
                                amount=float(expense_data["amount"]),
                                currency=expense_data.get("currency", "USD"),
                                expense_date=expense_date,
                                expense_type=expense_data.get("expense_type"),
                                vendor_name=expense_data.get("vendor_name"),
                                description=expense_data.get("description"),
                                confidence_score=float(expense_data.get("confidence_score", 0.0)),
                                raw_extracted_data=expense_data
                            )
                            db.add(extracted_expense)
                            expenses_count += 1
                            
                        except (ValueError, TypeError) as e:
                            print(f"Error processing expense data: {e}")
                            continue
                    
                    # Update document status
                    expense_doc.processing_status = "processed"
                    expense_doc.processed_at = datetime.utcnow()
                    expense_doc.extracted_data = {
                        "total_expenses": expenses_count,
                        "extraction_summary": extracted_data
                    }
                    
                    db.commit()
                    total_expenses_extracted += expenses_count
                    
                    results.append({
                        "document": file_name,
                        "status": "success",
                        "expenses_extracted": expenses_count,
                        "file_type": file_type
                    })
                    
                except Exception as e:
                    # Update document status with error
                    if 'expense_doc' in locals():
                        expense_doc.processing_status = "error"
                        expense_doc.processed_at = datetime.utcnow()
                        db.commit()
                    
                    results.append({
                        "document": file_name,
                        "status": "error",
                        "error": str(e),
                        "file_type": file_type
                    })
            
            # Update log
            log.status = "completed"
            log.completed_at = datetime.utcnow()
            log.message = f"Processed {len(documents)} documents, extracted {total_expenses_extracted} expenses"
            db.commit()
            
            db.close()
            
            return json.dumps({
                "status": "completed",
                "event_id": event_id,
                "documents_processed": len(documents),
                "total_expenses_extracted": total_expenses_extracted,
                "results": results,
                "message": f"Successfully processed {len(documents)} Cvent documents"
            })
            
        except Exception as e:
            # Update log with error
            if 'log' in locals():
                log.status = "error"
                log.completed_at = datetime.utcnow()
                log.error_details = {"error": str(e)}
                db.commit()
            
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Failed to process Cvent documents"
            })
    
    def filter_expenses_by_event(message: str) -> str:
        """Filter extracted expenses by event ID"""
        try:
            db = SessionLocal()
            
            data = json.loads(message)
            event_id = data.get("event_id")
            
            if not event_id:
                return json.dumps({
                    "status": "error",
                    "error": "event_id is required",
                    "message": "Please provide event_id to filter expenses"
                })
            
            # Get all extracted expenses for the event
            expenses = db.query(ExtractedExpense).filter(
                ExtractedExpense.event_id == event_id
            ).all()
            
            # Group by expense type
            expenses_by_type = {}
            total_amount = 0
            
            for expense in expenses:
                expense_type = expense.expense_type or "unclassified"
                
                if expense_type not in expenses_by_type:
                    expenses_by_type[expense_type] = {
                        "expenses": [],
                        "total_amount": 0,
                        "count": 0
                    }
                
                expense_data = {
                    "id": expense.id,
                    "amount": expense.amount,
                    "currency": expense.currency,
                    "expense_date": str(expense.expense_date),
                    "vendor_name": expense.vendor_name,
                    "description": expense.description,
                    "confidence_score": expense.confidence_score
                }
                
                expenses_by_type[expense_type]["expenses"].append(expense_data)
                expenses_by_type[expense_type]["total_amount"] += expense.amount
                expenses_by_type[expense_type]["count"] += 1
                total_amount += expense.amount
            
            db.close()
            
            return json.dumps({
                "status": "completed",
                "event_id": event_id,
                "total_expenses": len(expenses),
                "total_amount": total_amount,
                "expenses_by_type": expenses_by_type,
                "message": f"Found {len(expenses)} expenses for event {event_id}"
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Failed to filter expenses by event"
            })
    
    def get_processing_statistics(message: str) -> str:
        """Get document processing statistics"""
        try:
            db = SessionLocal()
            
            # Get document processing stats
            total_docs = db.query(ExpenseDocument).count()
            processed_docs = db.query(ExpenseDocument).filter(
                ExpenseDocument.processing_status == "processed"
            ).count()
            
            error_docs = db.query(ExpenseDocument).filter(
                ExpenseDocument.processing_status == "error"
            ).count()
            
            pending_docs = db.query(ExpenseDocument).filter(
                ExpenseDocument.processing_status == "pending"
            ).count()
            
            # Get extraction stats
            total_expenses = db.query(ExtractedExpense).count()
            
            # Get stats by event
            event_stats = db.query(Event.event_id, Event.event_name).all()
            
            events_with_docs = []
            for event_id, event_name in event_stats:
                doc_count = db.query(ExpenseDocument).filter(
                    ExpenseDocument.event_id == event_id
                ).count()
                
                expense_count = db.query(ExtractedExpense).filter(
                    ExtractedExpense.event_id == event_id
                ).count()
                
                if doc_count > 0:
                    events_with_docs.append({
                        "event_id": event_id,
                        "event_name": event_name,
                        "documents": doc_count,
                        "extracted_expenses": expense_count
                    })
            
            db.close()
            
            return json.dumps({
                "status": "completed",
                "document_statistics": {
                    "total_documents": total_docs,
                    "processed_documents": processed_docs,
                    "error_documents": error_docs,
                    "pending_documents": pending_docs
                },
                "extraction_statistics": {
                    "total_extracted_expenses": total_expenses
                },
                "events_with_documents": events_with_docs,
                "message": f"Retrieved processing statistics for {total_docs} documents"
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Failed to get processing statistics"
            })
    
    # Create the document processing agent
    processing_agent = ConversableAgent(
        name="document_processing_agent",
        system_message="""You are a Document Processing Agent specialized in extracting expense data from Cvent documents using multimodal LLM.

Your responsibilities:
1. Process Cvent expense documents (PDFs, images)
2. Use multimodal LLM to extract expense information
3. Validate and store extracted expense data
4. Filter expenses by Event ID
5. Generate processing statistics and reports
6. Handle various document formats and error cases

Key functions:
- process_cvent_documents: Extract expenses from document files using multimodal LLM
- filter_expenses_by_event: Get all expenses for a specific event
- get_processing_statistics: Generate processing statistics

When processing documents, you should:
1. Use multimodal LLM to analyze document content
2. Extract structured expense data (amount, date, vendor, type)
3. Validate data quality and confidence scores
4. Store expenses with proper categorization
5. Handle errors gracefully and log issues

Input format for document processing:
{
    "event_id": "EVENT123",
    "documents": [
        {"path": "/path/to/receipt1.pdf"},
        {"path": "/path/to/receipt2.jpg"}
    ]
}

Always ensure high-quality data extraction and provide confidence scores for extracted information.""",
        llm_config=llm_config,
        code_execution_config=False,
        function_map={
            "process_cvent_documents": process_cvent_documents,
            "filter_expenses_by_event": filter_expenses_by_event,
            "get_processing_statistics": get_processing_statistics
        },
        human_input_mode="NEVER",
    )
    
    return processing_agent 