from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
import os
import shutil
from datetime import datetime
import json

from expense_reconciliation_orchestrator import ExpenseReconciliationOrchestrator
try:
    from config_sqlite import settings
except ImportError:
    from config import settings
from database import SessionLocal
from database.models import ProcessingLog, ExpenseReport

app = FastAPI(
    title="Expense Reconciliation System",
    description="Agentic expense reconciliation system using AutoGen",
    version="1.0.0"
)

# Initialize orchestrator
orchestrator = ExpenseReconciliationOrchestrator()


@app.post("/reconcile")
async def reconcile_expenses(
    background_tasks: BackgroundTasks,
    citibank_file: UploadFile = File(...),
    concur_file: UploadFile = File(...),
    cvent_documents: List[UploadFile] = File(...),
    participants: str = None  # JSON string of participant data
):
    """
    Start the complete expense reconciliation workflow
    """
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save uploaded files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save Citibank file
        citibank_path = os.path.join(settings.UPLOAD_DIR, f"citibank_{timestamp}.xlsx")
        with open(citibank_path, "wb") as buffer:
            shutil.copyfileobj(citibank_file.file, buffer)
        
        # Save Concur file
        concur_path = os.path.join(settings.UPLOAD_DIR, f"concur_{timestamp}.xlsx")
        with open(concur_path, "wb") as buffer:
            shutil.copyfileobj(concur_file.file, buffer)
        
        # Save Cvent documents
        cvent_paths = []
        for i, doc in enumerate(cvent_documents):
            doc_path = os.path.join(settings.UPLOAD_DIR, f"cvent_{timestamp}_{i}_{doc.filename}")
            with open(doc_path, "wb") as buffer:
                shutil.copyfileobj(doc.file, buffer)
            cvent_paths.append(doc_path)
        
        # Parse participants data
        participants_data = []
        if participants:
            try:
                participants_data = json.loads(participants)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid participants JSON data")
        
        # Start workflow in background
        workflow_id = f"workflow_{timestamp}"
        background_tasks.add_task(
            run_reconciliation_workflow,
            workflow_id,
            citibank_path,
            concur_path,
            cvent_paths,
            participants_data
        )
        
        return JSONResponse({
            "status": "started",
            "workflow_id": workflow_id,
            "message": "Expense reconciliation workflow started",
            "files_uploaded": {
                "citibank": citibank_file.filename,
                "concur": concur_file.filename,
                "cvent_documents": [doc.filename for doc in cvent_documents]
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start reconciliation: {str(e)}")


async def run_reconciliation_workflow(
    workflow_id: str,
    citibank_file: str,
    concur_file: str,
    cvent_documents: List[str],
    participants_data: List[Dict]
):
    """Background task to run the reconciliation workflow"""
    try:
        result = orchestrator.run_full_reconciliation_workflow(
            citibank_file=citibank_file,
            concur_file=concur_file,
            cvent_documents=cvent_documents,
            participants_data=participants_data
        )
        
        # Log workflow completion
        db = SessionLocal()
        log = ProcessingLog(
            process_type="workflow_completion",
            status="completed",
            message=f"Workflow {workflow_id} completed successfully",
            started_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        db.close()
        
        print(f"✅ Workflow {workflow_id} completed successfully")
        
    except Exception as e:
        # Log workflow error
        db = SessionLocal()
        log = ProcessingLog(
            process_type="workflow_completion",
            status="error",
            message=f"Workflow {workflow_id} failed: {str(e)}",
            error_details={"error": str(e)},
            started_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        db.close()
        
        print(f"❌ Workflow {workflow_id} failed: {str(e)}")


@app.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get the status of a workflow"""
    try:
        db = SessionLocal()
        
        # Get workflow logs
        logs = db.query(ProcessingLog).filter(
            ProcessingLog.message.contains(workflow_id)
        ).order_by(ProcessingLog.started_at.desc()).all()
        
        if not logs:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get latest status
        latest_log = logs[0]
        
        # Get all step logs
        step_logs = []
        for log in logs:
            step_logs.append({
                "process_type": log.process_type,
                "status": log.status,
                "message": log.message,
                "started_at": str(log.started_at),
                "completed_at": str(log.completed_at) if log.completed_at else None,
                "error_details": log.error_details
            })
        
        db.close()
        
        return JSONResponse({
            "workflow_id": workflow_id,
            "overall_status": latest_log.status,
            "latest_message": latest_log.message,
            "step_logs": step_logs
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")


@app.get("/reports/{event_id}")
async def get_expense_reports(event_id: str):
    """Get expense reports for a specific event"""
    try:
        db = SessionLocal()
        
        reports = db.query(ExpenseReport).filter(
            ExpenseReport.event_id == event_id
        ).all()
        
        if not reports:
            raise HTTPException(status_code=404, detail="No reports found for this event")
        
        report_data = []
        for report in reports:
            report_data.append({
                "participant_id": report.participant_id,
                "total_amount": report.total_amount,
                "currency": report.currency,
                "status": report.status,
                "generated_at": str(report.generated_at),
                "sent_at": str(report.sent_at) if report.sent_at else None,
                "report_data": report.report_data
            })
        
        db.close()
        
        return JSONResponse({
            "event_id": event_id,
            "reports_count": len(report_data),
            "reports": report_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reports: {str(e)}")


@app.get("/events")
async def get_events():
    """Get all events in the system"""
    try:
        db = SessionLocal()
        
        from database.models import Event
        events = db.query(Event).all()
        
        event_data = []
        for event in events:
            # Get report count for each event
            report_count = db.query(ExpenseReport).filter(
                ExpenseReport.event_id == event.event_id
            ).count()
            
            event_data.append({
                "event_id": event.event_id,
                "event_name": event.event_name,
                "event_date": str(event.event_date) if event.event_date else None,
                "location": event.location,
                "status": event.status,
                "report_count": report_count,
                "created_at": str(event.created_at),
                "updated_at": str(event.updated_at)
            })
        
        db.close()
        
        return JSONResponse({
            "events_count": len(event_data),
            "events": event_data
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Expense Reconciliation System"
    })


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return JSONResponse({
        "message": "Expense Reconciliation System API",
        "version": "1.0.0",
        "description": "Agentic expense reconciliation using AutoGen framework",
        "endpoints": {
            "POST /reconcile": "Start expense reconciliation workflow",
            "GET /status/{workflow_id}": "Get workflow status",
            "GET /reports/{event_id}": "Get expense reports for event",
            "GET /events": "Get all events",
            "GET /health": "Health check"
        }
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 