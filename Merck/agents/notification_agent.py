import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from autogen import ConversableAgent
from typing import Dict, List, Any
try:
    from config_sqlite import get_llm_config, settings
except ImportError:
    from config import get_llm_config, settings
from database.models import ExpenseReport, Participant, Event, ProcessingLog
from database import SessionLocal
from datetime import datetime
import json


def create_notification_agent():
    """Create a notification agent for sending email notifications"""
    
    llm_config = get_llm_config()
    
    def send_expense_notifications(message: str) -> str:
        """Send email notifications to participants about their expense reports"""
        try:
            db = SessionLocal()
            
            data = json.loads(message)
            event_id = data.get("event_id")
            
            if not event_id:
                return json.dumps({
                    "status": "error",
                    "error": "event_id is required",
                    "message": "Please provide event_id to send notifications"
                })
            
            # Check email configuration
            if not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD:
                return json.dumps({
                    "status": "error",
                    "error": "Email configuration missing",
                    "message": "Please configure email settings in environment variables"
                })
            
            # Log processing start
            log = ProcessingLog(
                event_id=event_id,
                process_type="notification",
                status="started",
                message=f"Sending expense notifications for event {event_id}",
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
            
            # Get all expense reports for the event
            reports = db.query(ExpenseReport).filter(
                ExpenseReport.event_id == event_id,
                ExpenseReport.status == "generated"
            ).all()
            
            if not reports:
                return json.dumps({
                    "status": "error",
                    "error": "No reports found",
                    "message": f"No generated expense reports found for event {event_id}"
                })
            
            # Setup SMTP connection
            try:
                server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
                server.starttls()
                server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "error": f"SMTP connection failed: {str(e)}",
                    "message": "Failed to connect to email server"
                })
            
            # Send notifications
            notifications_sent = 0
            notification_results = []
            
            for report in reports:
                try:
                    # Get participant information
                    participant = db.query(Participant).filter(
                        Participant.participant_id == report.participant_id
                    ).first()
                    
                    if not participant or not participant.email:
                        notification_results.append({
                            "participant_id": report.participant_id,
                            "status": "error",
                            "error": "No email address found"
                        })
                        continue
                    
                    # Create email content
                    email_subject = f"Expense Report Ready - {event.event_name or event_id}"
                    
                    email_body = f"""
Dear {participant.name},

Your expense report for {event.event_name or event_id} is now ready for submission.

Event Details:
- Event ID: {event_id}
- Event Name: {event.event_name or "N/A"}
- Event Date: {event.event_date.strftime('%Y-%m-%d') if event.event_date else "N/A"}
- Location: {event.location or "N/A"}

Expense Summary:
- Your Total Amount: ${report.total_amount:.2f} {report.currency}
- Number of Expense Items: {len(report.report_data.get('detailed_expenses', []))}
- Report Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}

Please review your expense report and submit it through the Concur system.

If you have any questions about your expense report, please contact the finance team.

Best regards,
Expense Reconciliation System
"""
                    
                    # Create email message
                    msg = MIMEMultipart()
                    msg['From'] = settings.FROM_EMAIL or settings.EMAIL_USERNAME
                    msg['To'] = participant.email
                    msg['Subject'] = email_subject
                    
                    # Attach body to email
                    msg.attach(MIMEText(email_body, 'plain'))
                    
                    # Optional: Attach Excel report if available
                    excel_path = f"{settings.REPORTS_DIR}/expense_report_{event_id}_{participant.participant_id}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    if os.path.exists(excel_path):
                        try:
                            with open(excel_path, "rb") as attachment:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(attachment.read())
                            
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= expense_report_{participant.participant_id}.xlsx'
                            )
                            msg.attach(part)
                        except Exception as e:
                            print(f"Warning: Could not attach Excel file for {participant.participant_id}: {e}")
                    
                    # Send email
                    text = msg.as_string()
                    server.sendmail(settings.FROM_EMAIL or settings.EMAIL_USERNAME, participant.email, text)
                    
                    # Update report status
                    report.status = "sent"
                    report.sent_at = datetime.utcnow()
                    
                    notifications_sent += 1
                    notification_results.append({
                        "participant_id": participant.participant_id,
                        "participant_name": participant.name,
                        "participant_email": participant.email,
                        "status": "sent",
                        "amount": report.total_amount
                    })
                    
                except Exception as e:
                    notification_results.append({
                        "participant_id": report.participant_id,
                        "status": "error",
                        "error": str(e)
                    })
            
            # Close SMTP connection
            server.quit()
            
            # Commit database changes
            db.commit()
            
            # Update log
            log.status = "completed"
            log.completed_at = datetime.utcnow()
            log.message = f"Sent {notifications_sent} notifications for event {event_id}"
            db.commit()
            
            db.close()
            
            return json.dumps({
                "status": "completed",
                "event_id": event_id,
                "total_reports": len(reports),
                "notifications_sent": notifications_sent,
                "notification_results": notification_results,
                "message": f"Successfully sent {notifications_sent} expense notifications"
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
                "message": "Failed to send expense notifications"
            })
    
    def send_custom_notification(message: str) -> str:
        """Send custom notification to specific participants"""
        try:
            data = json.loads(message)
            participant_emails = data.get("participant_emails", [])
            subject = data.get("subject", "Expense System Notification")
            body = data.get("body", "")
            
            if not participant_emails:
                return json.dumps({
                    "status": "error",
                    "error": "No participant emails provided",
                    "message": "Please provide participant_emails list"
                })
            
            if not body:
                return json.dumps({
                    "status": "error",
                    "error": "No email body provided",
                    "message": "Please provide email body content"
                })
            
            # Check email configuration
            if not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD:
                return json.dumps({
                    "status": "error",
                    "error": "Email configuration missing",
                    "message": "Please configure email settings"
                })
            
            # Setup SMTP connection
            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            
            # Send notifications
            sent_count = 0
            results = []
            
            for email in participant_emails:
                try:
                    # Create email message
                    msg = MIMEText(body, 'plain')
                    msg['From'] = settings.FROM_EMAIL or settings.EMAIL_USERNAME
                    msg['To'] = email
                    msg['Subject'] = subject
                    
                    # Send email
                    server.sendmail(settings.FROM_EMAIL or settings.EMAIL_USERNAME, email, msg.as_string())
                    
                    sent_count += 1
                    results.append({
                        "email": email,
                        "status": "sent"
                    })
                    
                except Exception as e:
                    results.append({
                        "email": email,
                        "status": "error",
                        "error": str(e)
                    })
            
            # Close SMTP connection
            server.quit()
            
            return json.dumps({
                "status": "completed",
                "notifications_sent": sent_count,
                "total_recipients": len(participant_emails),
                "results": results,
                "message": f"Successfully sent {sent_count} custom notifications"
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Failed to send custom notifications"
            })
    
    def get_notification_status(message: str) -> str:
        """Get notification status for an event"""
        try:
            db = SessionLocal()
            
            data = json.loads(message)
            event_id = data.get("event_id")
            
            if not event_id:
                return json.dumps({
                    "status": "error",
                    "error": "event_id is required",
                    "message": "Please provide event_id"
                })
            
            # Get notification statistics
            total_reports = db.query(ExpenseReport).filter(
                ExpenseReport.event_id == event_id
            ).count()
            
            sent_reports = db.query(ExpenseReport).filter(
                ExpenseReport.event_id == event_id,
                ExpenseReport.status == "sent"
            ).count()
            
            pending_reports = db.query(ExpenseReport).filter(
                ExpenseReport.event_id == event_id,
                ExpenseReport.status == "generated"
            ).count()
            
            # Get detailed status
            reports = db.query(ExpenseReport).filter(
                ExpenseReport.event_id == event_id
            ).all()
            
            detailed_status = []
            for report in reports:
                participant = db.query(Participant).filter(
                    Participant.participant_id == report.participant_id
                ).first()
                
                detailed_status.append({
                    "participant_id": report.participant_id,
                    "participant_name": participant.name if participant else "Unknown",
                    "participant_email": participant.email if participant else "Unknown",
                    "report_status": report.status,
                    "generated_at": str(report.generated_at),
                    "sent_at": str(report.sent_at) if report.sent_at else None,
                    "total_amount": report.total_amount
                })
            
            db.close()
            
            return json.dumps({
                "status": "completed",
                "event_id": event_id,
                "summary": {
                    "total_reports": total_reports,
                    "sent_notifications": sent_reports,
                    "pending_notifications": pending_reports,
                    "completion_rate": (sent_reports / total_reports * 100) if total_reports > 0 else 0
                },
                "detailed_status": detailed_status,
                "message": f"Retrieved notification status for {total_reports} reports"
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Failed to get notification status"
            })
    
    # Create the notification agent
    notification_agent = ConversableAgent(
        name="notification_agent",
        system_message="""You are a Notification Agent specialized in sending email notifications to participants about their expense reports.

Your responsibilities:
1. Send automated expense report notifications to participants
2. Include expense summary and submission instructions
3. Attach Excel reports when available
4. Send custom notifications for special cases
5. Track notification delivery status
6. Handle email configuration and SMTP connection

Key functions:
- send_expense_notifications: Send automated notifications for expense reports
- send_custom_notification: Send custom messages to specific participants
- get_notification_status: Check notification delivery status

Email content includes:
- Event details (ID, name, date, location)
- Expense summary (total amount, number of items)
- Submission instructions
- Contact information for questions
- Optional Excel report attachment

Configuration requirements:
- SMTP server settings (server, port, username, password)
- From email address
- Email templates and formatting

Input format:
{
    "event_id": "EVENT123"
}

Always ensure professional email formatting and track delivery status for follow-up actions.""",
        llm_config=llm_config,
        code_execution_config=False,
        function_map={
            "send_expense_notifications": send_expense_notifications,
            "send_custom_notification": send_custom_notification,
            "get_notification_status": get_notification_status
        },
        human_input_mode="NEVER",
    )
    
    return notification_agent 