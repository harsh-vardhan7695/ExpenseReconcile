import os
from autogen import ConversableAgent
from typing import Dict, List, Any
try:
    from config_sqlite import get_llm_config
except ImportError:
    from config import get_llm_config
from utils.matching_engine import create_matching_engine
from database.models import (
    ExtractedExpense, CitibankTransaction, ConcurTransaction, 
    ExpenseMatch, Event, ProcessingLog
)
from database import SessionLocal
from datetime import datetime
import json


def create_expense_matching_agent():
    """Create an expense matching agent for matching extracted expenses with transactions"""
    
    llm_config = get_llm_config()
    
    def match_expenses_for_event(message: str) -> str:
        """Match extracted expenses with Citibank and Concur transactions for a specific event"""
        try:
            db = SessionLocal()
            matcher = create_matching_engine()
            
            data = json.loads(message)
            event_id = data.get("event_id")
            
            if not event_id:
                return json.dumps({
                    "status": "error",
                    "error": "event_id is required",
                    "message": "Please provide event_id to match expenses"
                })
            
            # Log processing start
            log = ProcessingLog(
                event_id=event_id,
                process_type="expense_matching",
                status="started",
                message=f"Matching expenses for event {event_id}",
                started_at=datetime.utcnow()
            )
            db.add(log)
            db.commit()
            
            # Get extracted expenses for the event
            extracted_expenses = db.query(ExtractedExpense).filter(
                ExtractedExpense.event_id == event_id
            ).all()
            
            # Get transactions for the event
            citibank_transactions = db.query(CitibankTransaction).filter(
                CitibankTransaction.event_id == event_id
            ).all()
            
            concur_transactions = db.query(ConcurTransaction).filter(
                ConcurTransaction.event_id == event_id
            ).all()
            
            # Convert to dictionaries for matching
            extracted_data = []
            for expense in extracted_expenses:
                extracted_data.append({
                    "id": expense.id,
                    "event_id": expense.event_id,
                    "amount": expense.amount,
                    "currency": expense.currency,
                    "expense_date": expense.expense_date,
                    "expense_type": expense.expense_type,
                    "vendor_name": expense.vendor_name,
                    "description": expense.description,
                    "confidence_score": expense.confidence_score
                })
            
            citibank_data = []
            for trans in citibank_transactions:
                citibank_data.append({
                    "id": trans.id,
                    "event_id": trans.event_id,
                    "transaction_id": trans.transaction_id,
                    "amount": trans.amount,
                    "currency": trans.currency,
                    "transaction_date": trans.transaction_date,
                    "description": trans.description,
                    "vendor_name": trans.vendor_name
                })
            
            concur_data = []
            for trans in concur_transactions:
                concur_data.append({
                    "id": trans.id,
                    "event_id": trans.event_id,
                    "transaction_id": trans.transaction_id,
                    "amount": trans.amount,
                    "currency": trans.currency,
                    "transaction_date": trans.transaction_date,
                    "expense_type": trans.expense_type,
                    "vendor_name": trans.vendor_name,
                    "description": trans.description
                })
            
            # Perform matching
            matches = matcher.match_expenses(extracted_data, citibank_data, concur_data)
            
            # Store matches in database
            matches_created = 0
            high_confidence_matches = 0
            low_confidence_matches = 0
            
            for match in matches:
                extracted_expense = match["extracted_expense"]
                overall_confidence = match["overall_confidence"]
                
                # Determine match status based on confidence
                if overall_confidence >= 0.8:
                    match_status = "confirmed"
                    high_confidence_matches += 1
                elif overall_confidence >= 0.6:
                    match_status = "pending"
                else:
                    match_status = "rejected"
                    low_confidence_matches += 1
                
                # Create match record
                expense_match = ExpenseMatch(
                    event_id=event_id,
                    extracted_expense_id=extracted_expense["id"],
                    citibank_transaction_id=match["citibank_match"]["transaction"]["id"] if match.get("citibank_match") else None,
                    concur_transaction_id=match["concur_match"]["transaction"]["id"] if match.get("concur_match") else None,
                    match_confidence=overall_confidence,
                    match_criteria={
                        **match["match_criteria"],
                        "llm_reasoning": match.get("llm_reasoning", ""),
                        "citibank_reasoning": match["citibank_match"]["reasoning"] if match.get("citibank_match") else None,
                        "concur_reasoning": match["concur_match"]["reasoning"] if match.get("concur_match") else None,
                    },
                    match_status=match_status
                )
                
                db.add(expense_match)
                matches_created += 1
            
            db.commit()
            
            # Update log
            log.status = "completed"
            log.completed_at = datetime.utcnow()
            log.message = f"Created {matches_created} matches for event {event_id}"
            db.commit()
            
            # Generate summary statistics
            summary = {
                "event_id": event_id,
                "total_extracted_expenses": len(extracted_data),
                "total_citibank_transactions": len(citibank_data),
                "total_concur_transactions": len(concur_data),
                "matches_created": matches_created,
                "high_confidence_matches": high_confidence_matches,
                "low_confidence_matches": low_confidence_matches,
                "match_rate": (matches_created / len(extracted_data)) * 100 if extracted_data else 0
            }
            
            db.close()
            
            return json.dumps({
                "status": "completed",
                "summary": summary,
                "message": f"Successfully matched {matches_created} expenses for event {event_id}"
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
                "message": "Failed to match expenses"
            })
    
    # Create the expense matching agent
    matching_agent = ConversableAgent(
        name="expense_matching_agent",
        system_message="""You are an Expense Matching Agent specialized in matching extracted expenses with transaction records.

Your responsibilities:
1. Match extracted expenses with Citibank transactions
2. Match extracted expenses with Concur transactions
3. Calculate confidence scores based on multiple criteria (amount, date, vendor, currency)
4. Store match results with confidence levels
5. Review and analyze match quality
6. Identify unmatched expenses for manual review

Matching criteria (with weights):
- Amount matching (40%): Within tolerance threshold
- Date matching (30%): Within date tolerance window
- Vendor name matching (20%): Fuzzy string matching
- Currency matching (10%): Exact currency code match

Confidence levels:
- High (≥0.8): Auto-confirmed matches
- Medium (0.6-0.8): Require manual review
- Low (<0.6): Likely false matches

Input format:
{
    "event_id": "EVENT123"
}

Always provide detailed match statistics and flag potential issues for human review.""",
        llm_config=llm_config,
        code_execution_config=False,
        function_map={
            "match_expenses_for_event": match_expenses_for_event
        },
        human_input_mode="NEVER",
    )
    
    return matching_agent 