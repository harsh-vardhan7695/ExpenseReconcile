from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    event_name = Column(String, nullable=True)
    event_date = Column(DateTime, nullable=True)
    location = Column(String, nullable=True)
    status = Column(String, default="active")  # active, reconciled, error
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    citibank_transactions = relationship("CitibankTransaction", back_populates="event")
    concur_transactions = relationship("ConcurTransaction", back_populates="event")
    expense_documents = relationship("ExpenseDocument", back_populates="event")
    expense_reports = relationship("ExpenseReport", back_populates="event")


class CitibankTransaction(Base):
    __tablename__ = "citibank_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.event_id"), nullable=False)
    transaction_id = Column(String, unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    transaction_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)
    vendor_name = Column(String, nullable=True)
    card_number = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="citibank_transactions")


class ConcurTransaction(Base):
    __tablename__ = "concur_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.event_id"), nullable=False)
    transaction_id = Column(String, unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    transaction_date = Column(DateTime, nullable=False)
    expense_type = Column(String, nullable=True)
    vendor_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    participant_id = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="concur_transactions")


class ExpenseDocument(Base):
    __tablename__ = "expense_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.event_id"), nullable=False)
    document_name = Column(String, nullable=False)
    document_path = Column(String, nullable=False)
    document_type = Column(String, nullable=False)  # pdf, image, etc.
    extracted_data = Column(JSON, nullable=True)  # Multimodal LLM extracted data
    processing_status = Column(String, default="pending")  # pending, processed, error
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="expense_documents")
    extracted_expenses = relationship("ExtractedExpense", back_populates="document")


class ExtractedExpense(Base):
    __tablename__ = "extracted_expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("expense_documents.id"), nullable=False)
    event_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    expense_date = Column(DateTime, nullable=False)
    expense_type = Column(String, nullable=True)
    vendor_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0)
    raw_extracted_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("ExpenseDocument", back_populates="extracted_expenses")
    matches = relationship("ExpenseMatch", back_populates="extracted_expense")


class ExpenseMatch(Base):
    __tablename__ = "expense_matches"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, nullable=False)
    extracted_expense_id = Column(Integer, ForeignKey("extracted_expenses.id"), nullable=False)
    citibank_transaction_id = Column(Integer, ForeignKey("citibank_transactions.id"), nullable=True)
    concur_transaction_id = Column(Integer, ForeignKey("concur_transactions.id"), nullable=True)
    match_confidence = Column(Float, nullable=False)
    match_criteria = Column(JSON, nullable=True)  # What criteria were used for matching
    match_status = Column(String, default="pending")  # pending, confirmed, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    extracted_expense = relationship("ExtractedExpense", back_populates="matches")


class Participant(Base):
    __tablename__ = "participants"
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    department = Column(String, nullable=True)
    employee_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event_participants = relationship("EventParticipant", back_populates="participant")
    expense_reports = relationship("ExpenseReport", back_populates="participant")


class EventParticipant(Base):
    __tablename__ = "event_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.event_id"), nullable=False)
    participant_id = Column(String, ForeignKey("participants.participant_id"), nullable=False)
    role = Column(String, default="participant")  # participant, organizer
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    participant = relationship("Participant", back_populates="event_participants")


class ExpenseReport(Base):
    __tablename__ = "expense_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.event_id"), nullable=False)
    participant_id = Column(String, ForeignKey("participants.participant_id"), nullable=False)
    report_data = Column(JSON, nullable=False)  # Individual expense breakdown
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    status = Column(String, default="generated")  # generated, sent, submitted
    generated_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="expense_reports")
    participant = relationship("Participant", back_populates="expense_reports")


class ProcessingLog(Base):
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, nullable=True)
    process_type = Column(String, nullable=False)  # ingestion, matching, splitting, notification
    status = Column(String, nullable=False)  # started, completed, error
    message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True) 