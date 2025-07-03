import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from autogen import GroupChat, GroupChatManager
try:
    from config_sqlite import get_llm_config, settings
except ImportError:
    from config import get_llm_config, settings
from database import init_database, SessionLocal
from database.models import Event, Participant, EventParticipant, ProcessingLog
from agents import (
    create_data_ingestion_agent,
    create_event_matching_agent,
    create_document_processing_agent,
    create_expense_matching_agent,
    create_expense_splitting_agent,
    create_report_generation_agent,
    create_notification_agent
)


class ExpenseReconciliationOrchestrator:
    """Main orchestrator for the expense reconciliation system"""
    
    def __init__(self):
        self.llm_config = get_llm_config()
        
        # Initialize agents
        self.data_ingestion_agent = create_data_ingestion_agent()
        self.event_matching_agent = create_event_matching_agent()
        self.document_processing_agent = create_document_processing_agent()
        self.expense_matching_agent = create_expense_matching_agent()
        self.expense_splitting_agent = create_expense_splitting_agent()
        self.report_generation_agent = create_report_generation_agent()
        self.notification_agent = create_notification_agent()
        
        # Create directories if they don't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
        os.makedirs(settings.REPORTS_DIR, exist_ok=True)
        
        # Initialize database
        init_database()
    
    def run_full_reconciliation_workflow(
        self, 
        citibank_file: str,
        concur_file: str,
        cvent_documents: List[str],
        participants_data: List[Dict],
        event_info: Optional[Dict] = None
    ) -> Dict:
        """
        Run the complete expense reconciliation workflow
        
        Args:
            citibank_file: Path to Citibank transactions Excel file
            concur_file: Path to Concur transactions Excel file
            cvent_documents: List of paths to Cvent expense documents
            participants_data: List of participant information
            event_info: Optional event information
        
        Returns:
            Dictionary with workflow results
        """
        try:
            workflow_log = {
                "workflow_id": f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "started_at": datetime.now().isoformat(),
                "steps": [],
                "status": "running"
            }
            
            print("🚀 Starting Expense Reconciliation Workflow")
            print("=" * 60)
            
            # Step 1: Data Ingestion
            print("📥 Step 1: Processing transaction files...")
            ingestion_result = self._run_data_ingestion(citibank_file, concur_file)
            workflow_log["steps"].append({
                "step": 1,
                "name": "data_ingestion",
                "result": ingestion_result,
                "completed_at": datetime.now().isoformat()
            })
            
            if ingestion_result["status"] != "completed":
                return self._finalize_workflow_error(workflow_log, "Data ingestion failed", ingestion_result)
            
            # Step 2: Event Matching
            print("🔍 Step 2: Finding matching events...")
            matching_result = self._run_event_matching()
            workflow_log["steps"].append({
                "step": 2,
                "name": "event_matching",
                "result": matching_result,
                "completed_at": datetime.now().isoformat()
            })
            
            if matching_result["status"] != "completed":
                return self._finalize_workflow_error(workflow_log, "Event matching failed", matching_result)
            
            matching_event_ids = matching_result.get("matching_event_ids", [])
            if not matching_event_ids:
                return self._finalize_workflow_error(workflow_log, "No matching events found", matching_result)
            
            print(f"✅ Found {len(matching_event_ids)} matching events: {matching_event_ids}")
            
            # Process each matching event
            for event_id in matching_event_ids:
                print(f"\n📋 Processing Event: {event_id}")
                print("-" * 40)
                
                # Add participants for this event if provided
                if participants_data:
                    self._add_participants_to_event(event_id, participants_data)
                
                # Step 3: Document Processing
                print(f"📄 Step 3: Processing Cvent documents for {event_id}...")
                doc_result = self._run_document_processing(event_id, cvent_documents)
                workflow_log["steps"].append({
                    "step": 3,
                    "event_id": event_id,
                    "name": "document_processing",
                    "result": doc_result,
                    "completed_at": datetime.now().isoformat()
                })
                
                if doc_result["status"] != "completed":
                    print(f"⚠️ Document processing failed for {event_id}")
                    continue
                
                # Step 4: Expense Matching
                print(f"🎯 Step 4: Matching expenses for {event_id}...")
                expense_match_result = self._run_expense_matching(event_id)
                workflow_log["steps"].append({
                    "step": 4,
                    "event_id": event_id,
                    "name": "expense_matching",
                    "result": expense_match_result,
                    "completed_at": datetime.now().isoformat()
                })
                
                if expense_match_result["status"] != "completed":
                    print(f"⚠️ Expense matching failed for {event_id}")
                    continue
                
                # Step 5: Expense Splitting
                print(f"💰 Step 5: Splitting expenses for {event_id}...")
                splitting_result = self._run_expense_splitting(event_id)
                workflow_log["steps"].append({
                    "step": 5,
                    "event_id": event_id,
                    "name": "expense_splitting",
                    "result": splitting_result,
                    "completed_at": datetime.now().isoformat()
                })
                
                if splitting_result["status"] != "completed":
                    print(f"⚠️ Expense splitting failed for {event_id}")
                    continue
                
                # Step 6: Report Generation
                print(f"📊 Step 6: Generating reports for {event_id}...")
                report_result = self._run_report_generation(event_id)
                workflow_log["steps"].append({
                    "step": 6,
                    "event_id": event_id,
                    "name": "report_generation",
                    "result": report_result,
                    "completed_at": datetime.now().isoformat()
                })
                
                if report_result["status"] != "completed":
                    print(f"⚠️ Report generation failed for {event_id}")
                    continue
                
                # Step 7: Export Reports
                print(f"📤 Step 7: Exporting reports to Excel for {event_id}...")
                export_result = self._export_reports(event_id)
                workflow_log["steps"].append({
                    "step": 7,
                    "event_id": event_id,
                    "name": "export_reports",
                    "result": export_result,
                    "completed_at": datetime.now().isoformat()
                })
                
                # Step 8: Send Notifications
                print(f"📧 Step 8: Sending notifications for {event_id}...")
                notification_result = self._send_notifications(event_id)
                workflow_log["steps"].append({
                    "step": 8,
                    "event_id": event_id,
                    "name": "notifications",
                    "result": notification_result,
                    "completed_at": datetime.now().isoformat()
                })
                
                print(f"✅ Completed processing for event {event_id}")
            
            # Finalize workflow
            workflow_log["status"] = "completed"
            workflow_log["completed_at"] = datetime.now().isoformat()
            workflow_log["summary"] = self._generate_workflow_summary(workflow_log)
            
            print("\n🎉 Expense Reconciliation Workflow Completed!")
            print("=" * 60)
            print(f"📊 Summary: {workflow_log['summary']}")
            
            return workflow_log
            
        except Exception as e:
            return self._finalize_workflow_error(workflow_log, f"Workflow failed: {str(e)}", {"error": str(e)})
    
    def _run_data_ingestion(self, citibank_file: str, concur_file: str) -> Dict:
        """Run data ingestion step"""
        files_data = {
            "files": [
                {"path": citibank_file, "type": "citibank"},
                {"path": concur_file, "type": "concur"}
            ]
        }
        
        result = self.data_ingestion_agent.initiate_chat(
            self.data_ingestion_agent,
            message=json.dumps(files_data),
            max_turns=1
        )
        
        # Extract result from the conversation
        return self._extract_agent_result(result)
    
    def _run_event_matching(self) -> Dict:
        """Run event matching step"""
        result = self.event_matching_agent.initiate_chat(
            self.event_matching_agent,
            message="Please find matching events between Citibank and Concur systems",
            max_turns=1
        )
        
        return self._extract_agent_result(result)
    
    def _run_document_processing(self, event_id: str, documents: List[str]) -> Dict:
        """Run document processing step"""
        doc_data = {
            "event_id": event_id,
            "documents": [{"path": doc} for doc in documents]
        }
        
        result = self.document_processing_agent.initiate_chat(
            self.document_processing_agent,
            message=json.dumps(doc_data),
            max_turns=1
        )
        
        return self._extract_agent_result(result)
    
    def _run_expense_matching(self, event_id: str) -> Dict:
        """Run expense matching step"""
        match_data = {"event_id": event_id}
        
        result = self.expense_matching_agent.initiate_chat(
            self.expense_matching_agent,
            message=json.dumps(match_data),
            max_turns=1
        )
        
        return self._extract_agent_result(result)
    
    def _run_expense_splitting(self, event_id: str) -> Dict:
        """Run expense splitting step"""
        split_data = {
            "event_id": event_id,
            "splitting_method": "equal"
        }
        
        result = self.expense_splitting_agent.initiate_chat(
            self.expense_splitting_agent,
            message=json.dumps(split_data),
            max_turns=1
        )
        
        return self._extract_agent_result(result)
    
    def _run_report_generation(self, event_id: str) -> Dict:
        """Run report generation step"""
        report_data = {"event_id": event_id}
        
        result = self.report_generation_agent.initiate_chat(
            self.report_generation_agent,
            message=json.dumps(report_data),
            max_turns=1
        )
        
        return self._extract_agent_result(result)
    
    def _export_reports(self, event_id: str) -> Dict:
        """Export reports to Excel"""
        export_data = {"event_id": event_id}
        
        result = self.report_generation_agent.initiate_chat(
            self.report_generation_agent,
            message=json.dumps(export_data),
            max_turns=1
        )
        
        return self._extract_agent_result(result)
    
    def _send_notifications(self, event_id: str) -> Dict:
        """Send email notifications"""
        notification_data = {"event_id": event_id}
        
        result = self.notification_agent.initiate_chat(
            self.notification_agent,
            message=json.dumps(notification_data),
            max_turns=1
        )
        
        return self._extract_agent_result(result)
    
    def _add_participants_to_event(self, event_id: str, participants_data: List[Dict]):
        """Add participants to an event"""
        try:
            db = SessionLocal()
            
            for participant_info in participants_data:
                # Create or get participant
                participant = db.query(Participant).filter(
                    Participant.participant_id == participant_info["participant_id"]
                ).first()
                
                if not participant:
                    participant = Participant(
                        participant_id=participant_info["participant_id"],
                        name=participant_info["name"],
                        email=participant_info["email"],
                        department=participant_info.get("department"),
                        employee_id=participant_info.get("employee_id")
                    )
                    db.add(participant)
                
                # Create event participant relationship
                event_participant = db.query(EventParticipant).filter(
                    EventParticipant.event_id == event_id,
                    EventParticipant.participant_id == participant_info["participant_id"]
                ).first()
                
                if not event_participant:
                    event_participant = EventParticipant(
                        event_id=event_id,
                        participant_id=participant_info["participant_id"],
                        role=participant_info.get("role", "participant")
                    )
                    db.add(event_participant)
            
            db.commit()
            db.close()
            
        except Exception as e:
            print(f"Error adding participants to event {event_id}: {str(e)}")
    
    def _extract_agent_result(self, chat_result) -> Dict:
        """Extract result from agent chat conversation"""
        try:
            # The chat result contains the conversation history
            # Get the last message from the agent
            if hasattr(chat_result, 'chat_history') and chat_result.chat_history:
                last_message = chat_result.chat_history[-1]['content']
            else:
                # Fallback for different AutoGen versions
                last_message = str(chat_result)
            
            # Try to parse as JSON
            if isinstance(last_message, str):
                try:
                    return json.loads(last_message)
                except json.JSONDecodeError:
                    # If not JSON, wrap in a status object
                    return {
                        "status": "completed",
                        "message": last_message
                    }
            
            return last_message
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to extract agent result"
            }
    
    def _finalize_workflow_error(self, workflow_log: Dict, error_message: str, error_details: Dict) -> Dict:
        """Finalize workflow with error status"""
        workflow_log["status"] = "error"
        workflow_log["error"] = error_message
        workflow_log["error_details"] = error_details
        workflow_log["completed_at"] = datetime.now().isoformat()
        
        print(f"❌ Workflow failed: {error_message}")
        return workflow_log
    
    def _generate_workflow_summary(self, workflow_log: Dict) -> str:
        """Generate a summary of the workflow execution"""
        total_steps = len(workflow_log["steps"])
        successful_steps = len([step for step in workflow_log["steps"] 
                              if step.get("result", {}).get("status") == "completed"])
        
        events_processed = len(set(step.get("event_id") for step in workflow_log["steps"] 
                                 if step.get("event_id")))
        
        return (f"Processed {events_processed} events. "
                f"Completed {successful_steps}/{total_steps} workflow steps successfully.")


def create_sample_data():
    """Create sample data for testing the workflow"""
    sample_participants = [
        {
            "participant_id": "EMP001",
            "name": "Alice Johnson",
            "email": "alice.johnson@company.com",
            "department": "Marketing"
        },
        {
            "participant_id": "EMP002", 
            "name": "Bob Smith",
            "email": "bob.smith@company.com",
            "department": "Sales"
        },
        {
            "participant_id": "EMP003",
            "name": "Carol Brown",
            "email": "carol.brown@company.com",
            "department": "Engineering"
        }
    ]
    
    return sample_participants


# Main execution example
if __name__ == "__main__":
    # Example usage
    orchestrator = ExpenseReconciliationOrchestrator()
    
    # Sample file paths (update these with actual file paths)
    sample_citibank_file = "data/sample_citibank_transactions.xlsx"
    sample_concur_file = "data/sample_concur_transactions.xlsx"
    sample_cvent_docs = [
        "data/receipts/hotel_receipt.pdf",
        "data/receipts/restaurant_receipt.jpg",
        "data/receipts/flight_receipt.pdf"
    ]
    
    sample_participants = create_sample_data()
    
    print("🔧 Example: Starting Expense Reconciliation Workflow")
    print("Note: Update file paths with actual data files")
    print("File paths needed:")
    print(f"- Citibank file: {sample_citibank_file}")
    print(f"- Concur file: {sample_concur_file}")
    print(f"- Cvent documents: {sample_cvent_docs}")
    
    # Uncomment to run with actual files:
    # result = orchestrator.run_full_reconciliation_workflow(
    #     citibank_file=sample_citibank_file,
    #     concur_file=sample_concur_file,
    #     cvent_documents=sample_cvent_docs,
    #     participants_data=sample_participants
    # )
    # 
    # print("\n📋 Workflow Result:")
    # print(json.dumps(result, indent=2)) 