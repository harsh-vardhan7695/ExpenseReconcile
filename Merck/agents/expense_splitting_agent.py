import os
from autogen import ConversableAgent
from typing import Dict, List, Any
try:
    from config_sqlite import get_llm_config
except ImportError:
    from config import get_llm_config
from database.models import (
    ExpenseReport, Participant, EventParticipant, ExtractedExpense,
    ExpenseMatch, Event, ProcessingLog
)
from database import SessionLocal
from datetime import datetime
import json


def create_expense_splitting_agent():
    """Create an enhanced expense splitting agent integrated with the database"""
    
    llm_config = get_llm_config()
    
    def split_expenses_for_event(message: str) -> str:
        """Split expenses for an event among participants"""
        try:
            db = SessionLocal()
            
            data = json.loads(message)
            event_id = data.get("event_id")
            splitting_method = data.get("splitting_method", "equal")  # equal, weighted, custom
            
            if not event_id:
                return json.dumps({
                    "status": "error",
                    "error": "event_id is required",
                    "message": "Please provide event_id to split expenses"
                })
            
            # Log processing start
            log = ProcessingLog(
                event_id=event_id,
                process_type="expense_splitting",
                status="started",
                message=f"Splitting expenses for event {event_id}",
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
            
            # Get participants for the event
            participants = db.query(Participant).join(EventParticipant).filter(
                EventParticipant.event_id == event_id
            ).all()
            
            if not participants:
                return json.dumps({
                    "status": "error",
                    "error": "No participants found",
                    "message": f"No participants found for event {event_id}"
                })
            
            # Get confirmed expense matches
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
            
            # Get expense details
            total_expenses = []
            total_amount = 0
            
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
                        "description": expense.description
                    }
                    total_expenses.append(expense_data)
                    total_amount += expense.amount
            
            # Perform splitting based on method
            if splitting_method == "equal":
                split_result = self._equal_split(total_expenses, participants, total_amount)
            elif splitting_method == "weighted":
                # For weighted splitting, you could add custom weights per participant
                weights = data.get("participant_weights", {})
                split_result = self._weighted_split(total_expenses, participants, total_amount, weights)
            else:
                split_result = self._equal_split(total_expenses, participants, total_amount)
            
            # Update log
            log.status = "completed"
            log.completed_at = datetime.utcnow()
            log.message = f"Split {len(total_expenses)} expenses among {len(participants)} participants"
            db.commit()
            
            db.close()
            
            return json.dumps({
                "status": "completed",
                "event_id": event_id,
                "splitting_method": splitting_method,
                "total_amount": total_amount,
                "total_expenses": len(total_expenses),
                "participants_count": len(participants),
                "split_result": split_result,
                "message": f"Successfully split expenses for {len(participants)} participants"
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
                "message": "Failed to split expenses"
            })
    
    def _equal_split(self, expenses: List[Dict], participants: List, total_amount: float) -> Dict:
        """Split expenses equally among participants"""
        participant_count = len(participants)
        amount_per_participant = total_amount / participant_count
        
        participant_splits = []
        
        for participant in participants:
            # Calculate individual share for each expense
            individual_expenses = []
            individual_total = 0
            
            for expense in expenses:
                individual_share = expense["amount"] / participant_count
                individual_expense = {
                    "original_expense_id": expense["id"],
                    "expense_type": expense["expense_type"],
                    "vendor_name": expense["vendor_name"],
                    "expense_date": str(expense["expense_date"]),
                    "original_amount": expense["amount"],
                    "participant_share": round(individual_share, 2),
                    "currency": expense["currency"],
                    "description": expense["description"]
                }
                individual_expenses.append(individual_expense)
                individual_total += individual_share
            
            # Group by expense type for summary
            expense_summary_by_type = {}
            for exp in individual_expenses:
                exp_type = exp["expense_type"]
                if exp_type not in expense_summary_by_type:
                    expense_summary_by_type[exp_type] = {
                        "total_amount": 0,
                        "count": 0
                    }
                expense_summary_by_type[exp_type]["total_amount"] += exp["participant_share"]
                expense_summary_by_type[exp_type]["count"] += 1
            
            participant_split = {
                "participant_id": participant.participant_id,
                "participant_name": participant.name,
                "participant_email": participant.email,
                "total_share": round(individual_total, 2),
                "expense_count": len(individual_expenses),
                "expenses_by_type": expense_summary_by_type,
                "detailed_expenses": individual_expenses
            }
            
            participant_splits.append(participant_split)
        
        return {
            "splitting_method": "equal",
            "total_event_cost": total_amount,
            "cost_per_participant": round(amount_per_participant, 2),
            "participant_splits": participant_splits,
            "summary": f"Split ${total_amount:.2f} equally among {participant_count} participants (${amount_per_participant:.2f} each)"
        }
    
    def _weighted_split(self, expenses: List[Dict], participants: List, total_amount: float, weights: Dict) -> Dict:
        """Split expenses based on participant weights"""
        # Default equal weights if no weights provided
        total_weight = 0
        participant_weights = {}
        
        for participant in participants:
            weight = weights.get(participant.participant_id, 1.0)
            participant_weights[participant.participant_id] = weight
            total_weight += weight
        
        participant_splits = []
        
        for participant in participants:
            participant_weight = participant_weights[participant.participant_id]
            weight_ratio = participant_weight / total_weight
            
            # Calculate individual share for each expense
            individual_expenses = []
            individual_total = 0
            
            for expense in expenses:
                individual_share = expense["amount"] * weight_ratio
                individual_expense = {
                    "original_expense_id": expense["id"],
                    "expense_type": expense["expense_type"],
                    "vendor_name": expense["vendor_name"],
                    "expense_date": str(expense["expense_date"]),
                    "original_amount": expense["amount"],
                    "participant_share": round(individual_share, 2),
                    "weight_ratio": round(weight_ratio, 3),
                    "currency": expense["currency"],
                    "description": expense["description"]
                }
                individual_expenses.append(individual_expense)
                individual_total += individual_share
            
            # Group by expense type
            expense_summary_by_type = {}
            for exp in individual_expenses:
                exp_type = exp["expense_type"]
                if exp_type not in expense_summary_by_type:
                    expense_summary_by_type[exp_type] = {
                        "total_amount": 0,
                        "count": 0
                    }
                expense_summary_by_type[exp_type]["total_amount"] += exp["participant_share"]
                expense_summary_by_type[exp_type]["count"] += 1
            
            participant_split = {
                "participant_id": participant.participant_id,
                "participant_name": participant.name,
                "participant_email": participant.email,
                "participant_weight": participant_weight,
                "weight_ratio": round(weight_ratio, 3),
                "total_share": round(individual_total, 2),
                "expense_count": len(individual_expenses),
                "expenses_by_type": expense_summary_by_type,
                "detailed_expenses": individual_expenses
            }
            
            participant_splits.append(participant_split)
        
        return {
            "splitting_method": "weighted",
            "total_event_cost": total_amount,
            "total_weight": total_weight,
            "participant_splits": participant_splits,
            "summary": f"Split ${total_amount:.2f} based on participant weights (total weight: {total_weight})"
        }
    
    # Create the expense splitting agent with enhanced system message
    splitting_agent = ConversableAgent(
        name="expense_splitting_agent",
        system_message="""You are an Enhanced Expense Splitting Agent integrated with the database system.

Your responsibilities:
1. Split expenses among participants based on different methods (equal, weighted, custom)
2. Calculate individual participant shares for each expense item  
3. Create detailed expense reports for each participant showing:
   - Participant information and contact details
   - Event details with Event ID
   - Their share of each expense with breakdown
   - Total amount owed by that participant
   - Expense categorization by type
   - Date and vendor information

4. Provide comprehensive summaries showing:
   - Total event cost and methodology used
   - Cost per participant (equal split) or weight ratios (weighted split)
   - Detailed breakdown by expense type
   - Clear audit trail for transparency

Splitting Methods:
- Equal: Divide all expenses equally among participants
- Weighted: Use custom weights per participant for proportional splitting
- Custom: Future extension for complex splitting rules

Input format:
{
    "event_id": "EVENT123",
    "splitting_method": "equal",
    "participant_weights": {"PART1": 1.0, "PART2": 1.5}  // for weighted method
}

Always be fair, logical, and provide clear explanations for splitting decisions with detailed breakdowns.""",
        llm_config=llm_config,
        code_execution_config=False,
        function_map={"split_expenses_for_event": split_expenses_for_event},
        human_input_mode="NEVER",
    )
    
    return splitting_agent 