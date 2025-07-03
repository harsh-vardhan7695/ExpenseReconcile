import os
from autogen import ConversableAgent
from typing import Dict, List, Any
try:
    from config_sqlite import get_llm_config, settings
except ImportError:
    from config import get_llm_config, settings
from database.models import (
    ExpenseReport, Participant, EventParticipant, ExtractedExpense,
    ExpenseMatch, Event, ProcessingLog
)
from database import SessionLocal
from datetime import datetime
import json
import pandas as pd


def create_report_generation_agent():
    """Create a report generation agent for creating individual expense reports"""
    
    llm_config = get_llm_config()
    
    def generate_expense_reports(message: str) -> str:
        """Generate individual expense reports for all participants of an event"""
        try:
            db = SessionLocal()
            
            data = json.loads(message)
            event_id = data.get("event_id")
            
            if not event_id:
                return json.dumps({
                    "status": "error",
                    "error": "event_id is required",
                    "message": "Please provide event_id to generate reports"
                })
            
            # Log processing start
            log = ProcessingLog(
                event_id=event_id,
                process_type="report_generation",
                status="started",
                message=f"Generating expense reports for event {event_id}",
                started_at=datetime.utcnow()
            )
            db.add(log)
            db.commit()
            
            # Get event information
            event = db.query(Event).filter(Event.event_id == event_id).first()
            if not event:
                return json.dumps({
                    "status": "error",
                    "error": "Event not found",
                    "message": f"Event {event_id} not found in database"
                })
            
            # Get all participants for the event
            participants_query = db.query(Participant).join(EventParticipant).filter(
                EventParticipant.event_id == event_id
            )
            participants = participants_query.all()
            
            if not participants:
                return json.dumps({
                    "status": "error",
                    "error": "No participants found",
                    "message": f"No participants found for event {event_id}"
                })
            
            # Get all confirmed expense matches for the event
            confirmed_matches = db.query(ExpenseMatch).filter(
                ExpenseMatch.event_id == event_id,
                ExpenseMatch.match_status == "confirmed"
            ).all()
            
            if not confirmed_matches:
                return json.dumps({
                    "status": "error",
                    "error": "No confirmed expenses found",
                    "message": f"No confirmed expense matches found for event {event_id}"
                })
            
            # Calculate total event expenses
            total_event_amount = 0
            all_expenses = []
            
            for match in confirmed_matches:
                expense = db.query(ExtractedExpense).filter(
                    ExtractedExpense.id == match.extracted_expense_id
                ).first()
                
                if expense:
                    expense_data = {
                        "id": expense.id,
                        "amount": expense.amount,
                        "currency": expense.currency,
                        "expense_date": expense.expense_date,
                        "expense_type": expense.expense_type or "miscellaneous",
                        "vendor_name": expense.vendor_name,
                        "description": expense.description,
                        "confidence_score": expense.confidence_score
                    }
                    all_expenses.append(expense_data)
                    total_event_amount += expense.amount
            
            # Calculate per-participant amount (equal split)
            participant_count = len(participants)
            amount_per_participant = total_event_amount / participant_count
            
            # Generate individual reports
            reports_generated = 0
            generated_reports = []
            
            for participant in participants:
                # Create individual expense breakdown
                individual_expenses = []
                individual_total = 0
                
                for expense in all_expenses:
                    individual_expense = {
                        "expense_type": expense["expense_type"],
                        "vendor_name": expense["vendor_name"],
                        "expense_date": str(expense["expense_date"]),
                        "original_amount": expense["amount"],
                        "participant_share": expense["amount"] / participant_count,
                        "currency": expense["currency"],
                        "description": expense["description"]
                    }
                    individual_expenses.append(individual_expense)
                    individual_total += individual_expense["participant_share"]
                
                # Group expenses by type for summary
                expense_by_type = {}
                for expense in individual_expenses:
                    exp_type = expense["expense_type"]
                    if exp_type not in expense_by_type:
                        expense_by_type[exp_type] = {
                            "total_amount": 0,
                            "count": 0,
                            "items": []
                        }
                    expense_by_type[exp_type]["total_amount"] += expense["participant_share"]
                    expense_by_type[exp_type]["count"] += 1
                    expense_by_type[exp_type]["items"].append(expense)
                
                # Create report data structure
                report_data = {
                    "participant_info": {
                        "participant_id": participant.participant_id,
                        "name": participant.name,
                        "email": participant.email,
                        "department": participant.department
                    },
                    "event_info": {
                        "event_id": event_id,
                        "event_name": event.event_name,
                        "event_date": str(event.event_date) if event.event_date else None,
                        "location": event.location
                    },
                    "expense_summary": {
                        "total_event_amount": total_event_amount,
                        "total_participants": participant_count,
                        "participant_share": individual_total,
                        "currency": "USD",  # Default currency
                        "expenses_by_type": expense_by_type
                    },
                    "detailed_expenses": individual_expenses,
                    "generation_metadata": {
                        "generated_at": datetime.utcnow().isoformat(),
                        "total_expense_items": len(individual_expenses),
                        "splitting_method": "equal_split"
                    }
                }
                
                # Store report in database
                expense_report = ExpenseReport(
                    event_id=event_id,
                    participant_id=participant.participant_id,
                    report_data=report_data,
                    total_amount=individual_total,
                    currency="USD",
                    status="generated"
                )
                
                db.add(expense_report)
                reports_generated += 1
                
                generated_reports.append({
                    "participant_id": participant.participant_id,
                    "participant_name": participant.name,
                    "participant_email": participant.email,
                    "total_amount": individual_total,
                    "expense_items": len(individual_expenses)
                })
            
            db.commit()
            
            # Update log
            log.status = "completed"
            log.completed_at = datetime.utcnow()
            log.message = f"Generated {reports_generated} expense reports for event {event_id}"
            db.commit()
            
            db.close()
            
            return json.dumps({
                "status": "completed",
                "event_id": event_id,
                "total_event_amount": total_event_amount,
                "participant_count": participant_count,
                "amount_per_participant": amount_per_participant,
                "reports_generated": reports_generated,
                "generated_reports": generated_reports,
                "message": f"Successfully generated {reports_generated} expense reports"
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
                "message": "Failed to generate expense reports"
            })
    
    def export_reports_to_excel(message: str) -> str:
        """Export expense reports to Excel files"""
        try:
            db = SessionLocal()
            
            data = json.loads(message)
            event_id = data.get("event_id")
            
            if not event_id:
                return json.dumps({
                    "status": "error",
                    "error": "event_id is required",
                    "message": "Please provide event_id to export reports"
                })
            
            # Get all reports for the event
            reports = db.query(ExpenseReport).filter(
                ExpenseReport.event_id == event_id
            ).all()
            
            if not reports:
                return json.dumps({
                    "status": "error",
                    "error": "No reports found",
                    "message": f"No expense reports found for event {event_id}"
                })
            
            # Create reports directory if it doesn't exist
            reports_dir = settings.REPORTS_DIR
            os.makedirs(reports_dir, exist_ok=True)
            
            exported_files = []
            
            for report in reports:
                # Get participant info
                participant = db.query(Participant).filter(
                    Participant.participant_id == report.participant_id
                ).first()
                
                if not participant:
                    continue
                
                # Convert report data to DataFrame
                detailed_expenses = report.report_data.get("detailed_expenses", [])
                
                if detailed_expenses:
                    df = pd.DataFrame(detailed_expenses)
                    
                    # Create filename
                    filename = f"expense_report_{event_id}_{participant.participant_id}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    filepath = os.path.join(reports_dir, filename)
                    
                    # Create Excel file with multiple sheets
                    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                        # Summary sheet
                        summary_data = {
                            'Participant Name': [participant.name],
                            'Participant Email': [participant.email],
                            'Event ID': [event_id],
                            'Event Name': [report.report_data.get("event_info", {}).get("event_name", "")],
                            'Total Amount': [report.total_amount],
                            'Currency': [report.currency],
                            'Generated Date': [report.generated_at.strftime('%Y-%m-%d %H:%M:%S')]
                        }
                        summary_df = pd.DataFrame(summary_data)
                        summary_df.to_excel(writer, sheet_name='Summary', index=False)
                        
                        # Detailed expenses sheet
                        df.to_excel(writer, sheet_name='Detailed Expenses', index=False)
                        
                        # Summary by type sheet
                        expense_by_type = report.report_data.get("expense_summary", {}).get("expenses_by_type", {})
                        if expense_by_type:
                            type_summary = []
                            for exp_type, data in expense_by_type.items():
                                type_summary.append({
                                    'Expense Type': exp_type,
                                    'Total Amount': data['total_amount'],
                                    'Number of Items': data['count']
                                })
                            type_df = pd.DataFrame(type_summary)
                            type_df.to_excel(writer, sheet_name='Summary by Type', index=False)
                    
                    exported_files.append({
                        "participant_id": participant.participant_id,
                        "participant_name": participant.name,
                        "filename": filename,
                        "filepath": filepath
                    })
            
            db.close()
            
            return json.dumps({
                "status": "completed",
                "event_id": event_id,
                "reports_exported": len(exported_files),
                "exported_files": exported_files,
                "export_directory": reports_dir,
                "message": f"Successfully exported {len(exported_files)} expense reports to Excel"
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Failed to export reports to Excel"
            })
    
    # Create the report generation agent
    report_agent = ConversableAgent(
        name="report_generation_agent",
        system_message="""You are a Report Generation Agent specialized in creating individual expense reports for event participants.

Your responsibilities:
1. Split event expenses equally among all participants
2. Generate individual expense reports with detailed breakdowns
3. Create summary statistics by expense type
4. Export reports to Excel format for easy sharing
5. Store report data in database for tracking

Key functions:
- generate_expense_reports: Create individual reports for all event participants
- export_reports_to_excel: Export reports to Excel files

Report structure includes:
- Participant information (name, email, department)
- Event details (event ID, name, date, location)
- Expense summary (total amounts, participant share)
- Detailed expense breakdown (by item and type)
- Generation metadata

Expense splitting logic:
- Equal distribution among all participants
- Proportional sharing of each expense item
- Proper currency handling
- Detailed audit trail

Input format:
{
    "event_id": "EVENT123"
}

Always ensure accurate calculations and provide comprehensive expense breakdowns for transparency.""",
        llm_config=llm_config,
        code_execution_config=False,
        function_map={
            "generate_expense_reports": generate_expense_reports,
            "export_reports_to_excel": export_reports_to_excel
        },
        human_input_mode="NEVER",
    )
    
    return report_agent 