import os
from autogen import ConversableAgent
from typing import Dict, List, Any
try:
    from config_sqlite import get_llm_config
except ImportError:
    from config import get_llm_config
from utils.matching_engine import create_matching_engine
from database.models import CitibankTransaction, ConcurTransaction, Event, ProcessingLog
from database import SessionLocal
from datetime import datetime
import json


def create_event_matching_agent():
    """Create an event matching agent for grouping transactions by Event ID"""
    
    llm_config = get_llm_config()
    
    def find_matching_events(message: str) -> str:
        """Find events that have transactions in both Citibank and Concur"""
        try:
            db = SessionLocal()
            matcher = create_matching_engine()
            
            # Log processing start
            log = ProcessingLog(
                process_type="event_matching",
                status="started",
                message="Finding matching events between Citibank and Concur",
                started_at=datetime.utcnow()
            )
            db.add(log)
            db.commit()
            
            # Get all transactions from database
            citibank_transactions = db.query(CitibankTransaction).all()
            concur_transactions = db.query(ConcurTransaction).all()
            
            # Convert to dictionaries for processing
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
                    "vendor_name": trans.vendor_name,
                    "card_number": trans.card_number
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
                    "description": trans.description,
                    "participant_id": trans.participant_id
                })
            
            # Find matching event IDs
            matching_event_ids = matcher.find_matching_event_ids(citibank_data, concur_data)
            
            # Group transactions by event ID
            citibank_grouped = matcher.group_by_event_id(citibank_data)
            concur_grouped = matcher.group_by_event_id(concur_data)
            
            # Analyze matching events
            event_analysis = []
            for event_id in matching_event_ids:
                citibank_count = len(citibank_grouped.get(event_id, []))
                concur_count = len(concur_grouped.get(event_id, []))
                citibank_total = sum(t["amount"] for t in citibank_grouped.get(event_id, []))
                concur_total = sum(t["amount"] for t in concur_grouped.get(event_id, []))
                
                # Update event status in database
                event = db.query(Event).filter(Event.event_id == event_id).first()
                if event:
                    event.status = "matched"
                    event.updated_at = datetime.utcnow()
                
                event_analysis.append({
                    "event_id": event_id,
                    "citibank_transactions": citibank_count,
                    "concur_transactions": concur_count,
                    "citibank_total_amount": citibank_total,
                    "concur_total_amount": concur_total,
                    "amount_difference": abs(citibank_total - concur_total),
                    "status": "matched"
                })
            
            db.commit()
            
            # Update log
            log.status = "completed"
            log.completed_at = datetime.utcnow()
            log.message = f"Found {len(matching_event_ids)} matching events"
            db.commit()
            
            db.close()
            
            return json.dumps({
                "status": "completed",
                "matching_events_count": len(matching_event_ids),
                "matching_event_ids": matching_event_ids,
                "event_analysis": event_analysis,
                "total_citibank_transactions": len(citibank_data),
                "total_concur_transactions": len(concur_data),
                "message": f"Successfully identified {len(matching_event_ids)} events with transactions in both systems"
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
                "message": "Failed to find matching events"
            })
    
    def analyze_event_coverage(message: str) -> str:
        """Analyze which events have incomplete transaction coverage"""
        try:
            db = SessionLocal()
            
            # Get all events
            all_events = db.query(Event).all()
            
            coverage_analysis = []
            
            for event in all_events:
                citibank_count = db.query(CitibankTransaction).filter(
                    CitibankTransaction.event_id == event.event_id
                ).count()
                
                concur_count = db.query(ConcurTransaction).filter(
                    ConcurTransaction.event_id == event.event_id
                ).count()
                
                status = "complete" if citibank_count > 0 and concur_count > 0 else "incomplete"
                missing_system = []
                
                if citibank_count == 0:
                    missing_system.append("citibank")
                if concur_count == 0:
                    missing_system.append("concur")
                
                coverage_analysis.append({
                    "event_id": event.event_id,
                    "event_name": event.event_name,
                    "citibank_transactions": citibank_count,
                    "concur_transactions": concur_count,
                    "coverage_status": status,
                    "missing_systems": missing_system
                })
            
            db.close()
            
            complete_events = [e for e in coverage_analysis if e["coverage_status"] == "complete"]
            incomplete_events = [e for e in coverage_analysis if e["coverage_status"] == "incomplete"]
            
            return json.dumps({
                "status": "completed",
                "total_events": len(coverage_analysis),
                "complete_events": len(complete_events),
                "incomplete_events": len(incomplete_events),
                "coverage_analysis": coverage_analysis,
                "message": f"Analyzed {len(coverage_analysis)} events. {len(complete_events)} have complete coverage."
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Failed to analyze event coverage"
            })
    
    # Create the event matching agent
    matching_agent = ConversableAgent(
        name="event_matching_agent",
        system_message="""You are an Event Matching Agent specialized in analyzing transaction coverage across systems.

Your responsibilities:
1. Group Citibank transactions by Event ID
2. Group Concur transactions by Event ID  
3. Identify events that have transactions in BOTH systems
4. Store matching Event IDs in database for further processing
5. Analyze transaction coverage and identify gaps
6. Generate reports on event matching statistics

Key functions:
- find_matching_events: Identifies events present in both Citibank and Concur
- analyze_event_coverage: Analyzes which events have incomplete coverage

When identifying matching events, you should:
1. Compare Event IDs between both transaction systems
2. Calculate transaction counts and amounts for each event
3. Flag events for reconciliation processing
4. Report any discrepancies in amounts between systems
5. Update event status in database

Always provide detailed statistics and insights about the matching process.""",
        llm_config=llm_config,
        code_execution_config=False,
        function_map={
            "find_matching_events": find_matching_events,
            "analyze_event_coverage": analyze_event_coverage
        },
        human_input_mode="NEVER",
    )
    
    return matching_agent 