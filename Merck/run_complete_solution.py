#!/usr/bin/env python3
"""
Complete Expense Reconciliation Solution Runner
This script demonstrates the full end-to-end workflow with SQLite database
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
import shutil

# Use SQLite configuration
import config_sqlite as config
from config_sqlite import settings

# Import the orchestrator and utilities
from expense_reconciliation_orchestrator import ExpenseReconciliationOrchestrator
from utils.matching_engine import create_matching_engine


def setup_demo_environment():
    """Set up the complete demo environment"""
    print("🔧 Setting Up Demo Environment")
    print("=" * 40)
    
    # Create all necessary directories
    directories = [
        "data/uploads",
        "data/processed", 
        "data/reports",
        "data/demo",
        "data/cvent_documents"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ Created directory: {directory}")
    
    print(f"   ✅ Environment setup complete!")


def create_sample_excel_files():
    """Create sample Excel files for Citibank and Concur transactions"""
    print("\n📊 Creating Sample Transaction Files")
    print("=" * 40)
    
    # Sample Citibank transactions
    citibank_data = [
        {
            "Transaction ID": "CITI_001",
            "Event ID": "CONF2024_NYC",
            "Amount": 285.50,
            "Currency": "USD",
            "Date": "2024-03-15",
            "Description": "MARRIOTT HOTELS NYC",
            "Vendor": "Marriott Hotels",
            "Card Number": "*1234"
        },
        {
            "Transaction ID": "CITI_002",
            "Event ID": "CONF2024_NYC", 
            "Amount": 67.23,
            "Currency": "USD",
            "Date": "2024-03-16",
            "Description": "JOES PIZZA NYC",
            "Vendor": "Joe's Pizza Restaurant",
            "Card Number": "*1234"
        },
        {
            "Transaction ID": "CITI_003",
            "Event ID": "CONF2024_NYC",
            "Amount": 148.75,
            "Currency": "USD",
            "Date": "2024-03-14",
            "Description": "YELLOW CAB NYC TAXI",
            "Vendor": "NYC Taxi & Limousine",
            "Card Number": "*1234"
        },
        {
            "Transaction ID": "CITI_004",
            "Event ID": "WORKSHOP2024_SF",
            "Amount": 425.00,
            "Currency": "USD",
            "Date": "2024-04-20",
            "Description": "HILTON GARDEN INN SF",
            "Vendor": "Hilton Hotels",
            "Card Number": "*1234"
        }
    ]
    
    # Sample Concur transactions
    concur_data = [
        {
            "Transaction ID": "CONCUR_001",
            "Event ID": "CONF2024_NYC",
            "Amount": 285.50,
            "Currency": "USD",
            "Date": "2024-03-15",
            "Expense Type": "Hotel",
            "Vendor": "Marriott International",
            "Description": "Conference hotel booking",
            "Participant ID": "EMP001"
        },
        {
            "Transaction ID": "CONCUR_002",
            "Event ID": "CONF2024_NYC",
            "Amount": 67.23,
            "Currency": "USD",
            "Date": "2024-03-16",
            "Expense Type": "Meals",
            "Vendor": "Joe's Pizza NYC", 
            "Description": "Business meal - team dinner",
            "Participant ID": "EMP002"
        },
        {
            "Transaction ID": "CONCUR_003",
            "Event ID": "CONF2024_NYC",
            "Amount": 150.00,
            "Currency": "USD",
            "Date": "2024-03-14",
            "Expense Type": "Transportation",
            "Vendor": "NYC Taxi Services",
            "Description": "Ground transportation",
            "Participant ID": "EMP003"
        },
        {
            "Transaction ID": "CONCUR_004",
            "Event ID": "WORKSHOP2024_SF",
            "Amount": 425.00,
            "Currency": "USD",
            "Date": "2024-04-20",
            "Expense Type": "Hotel",
            "Vendor": "Hilton Garden Inn",
            "Description": "Workshop accommodation",
            "Participant ID": "EMP001"
        }
    ]
    
    # Create Excel files
    citibank_df = pd.DataFrame(citibank_data)
    concur_df = pd.DataFrame(concur_data)
    
    citibank_file = "data/uploads/citibank_transactions.xlsx"
    concur_file = "data/uploads/concur_transactions.xlsx"
    
    citibank_df.to_excel(citibank_file, index=False)
    concur_df.to_excel(concur_file, index=False)
    
    print(f"   ✅ Created {citibank_file} with {len(citibank_data)} transactions")
    print(f"   ✅ Created {concur_file} with {len(concur_data)} transactions")
    
    return citibank_file, concur_file


def create_sample_cvent_documents():
    """Create sample Cvent document data (simulating extracted expenses)"""
    print("\n📄 Creating Sample Cvent Document Data")
    print("=" * 40)
    
    # Sample extracted expenses from Cvent documents
    cvent_expenses = [
        {
            "event_id": "CONF2024_NYC",
            "amount": 285.50,
            "currency": "USD",
            "expense_date": "2024-03-15",
            "vendor_name": "Marriott Downtown NYC",
            "description": "Hotel accommodation for conference",
            "expense_type": "lodging",
            "document_source": "receipt_hotel_001.pdf"
        },
        {
            "event_id": "CONF2024_NYC",
            "amount": 67.23,
            "currency": "USD",
            "expense_date": "2024-03-16", 
            "vendor_name": "Joe's Pizza",
            "description": "Team dinner after conference",
            "expense_type": "meals",
            "document_source": "receipt_dinner_002.jpg"
        },
        {
            "event_id": "CONF2024_NYC",
            "amount": 150.00,
            "currency": "USD",
            "expense_date": "2024-03-14",
            "vendor_name": "Yellow Cab Co",
            "description": "Airport transfer and local transport",
            "expense_type": "transportation",
            "document_source": "receipt_taxi_003.pdf"
        },
        {
            "event_id": "WORKSHOP2024_SF",
            "amount": 425.00,
            "currency": "USD",
            "expense_date": "2024-04-20",
            "vendor_name": "Hilton Garden Inn",
            "description": "Workshop hotel accommodation",
            "expense_type": "lodging",
            "document_source": "receipt_hotel_004.pdf"
        }
    ]
    
    # Save sample documents data
    cvent_file = "data/cvent_documents/extracted_expenses.json"
    with open(cvent_file, 'w') as f:
        json.dump(cvent_expenses, f, indent=2)
    
    print(f"   ✅ Created {cvent_file} with {len(cvent_expenses)} extracted expenses")
    
    # Create dummy document files
    doc_files = []
    for expense in cvent_expenses:
        doc_path = f"data/cvent_documents/{expense['document_source']}"
        with open(doc_path, 'w') as f:
            f.write(f"Sample document for {expense['vendor_name']} - ${expense['amount']}")
        doc_files.append(doc_path)
        print(f"   ✅ Created sample document: {doc_path}")
    
    return doc_files, cvent_expenses


def create_sample_participants():
    """Create sample participant data"""
    print("\n👥 Creating Sample Participant Data")
    print("=" * 40)
    
    participants = [
        {
            "participant_id": "EMP001",
            "name": "Alice Johnson",
            "email": "alice@company.com",
            "department": "Marketing"
        },
        {
            "participant_id": "EMP002",
            "name": "Bob Smith", 
            "email": "bob@company.com",
            "department": "Engineering"
        },
        {
            "participant_id": "EMP003",
            "name": "Carol Davis",
            "email": "carol@company.com",
            "department": "Sales"
        }
    ]
    
    print(f"   ✅ Created {len(participants)} participant records")
    for p in participants:
        print(f"      - {p['name']} ({p['participant_id']})")
    
    return participants


def run_complete_workflow():
    """Run the complete expense reconciliation workflow"""
    print("\n🚀 Running Complete Expense Reconciliation Workflow")
    print("=" * 55)
    
    # Step 1: Setup environment and data
    setup_demo_environment()
    
    # Step 2: Create sample data
    citibank_file, concur_file = create_sample_excel_files()
    cvent_files, cvent_expenses = create_sample_cvent_documents()
    participants = create_sample_participants()
    
    # Step 3: Initialize orchestrator
    print("\n🤖 Initializing Expense Reconciliation Orchestrator")
    print("=" * 50)
    try:
        orchestrator = ExpenseReconciliationOrchestrator()
        print("   ✅ Orchestrator initialized successfully")
        print("   ✅ SQLite database created")
        print("   ✅ All agents loaded and ready")
    except Exception as e:
        print(f"   ❌ Failed to initialize orchestrator: {e}")
        return False
    
    # Step 4: Run full workflow
    print("\n⚡ Executing Full Reconciliation Workflow")
    print("=" * 45)
    
    try:
        # Run the complete workflow
        result = orchestrator.run_full_reconciliation_workflow(
            citibank_file=citibank_file,
            concur_file=concur_file,
            cvent_documents=cvent_files,
            participants_data=participants
        )
        
        print(f"\n🎉 Workflow Execution Complete!")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   Workflow ID: {result.get('workflow_id', 'N/A')}")
        
        # Display detailed results
        if result.get('status') == 'completed':
            display_workflow_results(result)
        else:
            print(f"   ⚠️ Workflow completed with issues:")
            for step, step_result in result.get('steps', {}).items():
                status = step_result.get('status', 'unknown')
                print(f"      {step}: {status}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def display_workflow_results(result):
    """Display comprehensive workflow results"""
    print(f"\n📈 Detailed Workflow Results")
    print("=" * 35)
    
    steps = result.get('steps', {})
    
    # Data ingestion results
    if 'data_ingestion' in steps:
        ingestion = steps['data_ingestion']
        print(f"📊 Data Ingestion:")
        print(f"   Citibank Transactions: {ingestion.get('citibank_count', 0)}")
        print(f"   Concur Transactions: {ingestion.get('concur_count', 0)}")
        print(f"   Status: {ingestion.get('status', 'Unknown')}")
    
    # Event matching results
    if 'event_matching' in steps:
        events = steps['event_matching']
        print(f"\n🎯 Event Matching:")
        print(f"   Events Found: {len(events.get('matching_events', []))}")
        for event in events.get('matching_events', []):
            print(f"      - {event}")
    
    # Document processing results
    if 'document_processing' in steps:
        docs = steps['document_processing']
        print(f"\n📄 Document Processing:")
        print(f"   Documents Processed: {docs.get('documents_processed', 0)}")
        print(f"   Expenses Extracted: {docs.get('expenses_extracted', 0)}")
    
    # Expense matching results
    if 'expense_matching' in steps:
        matching = steps['expense_matching']
        print(f"\n🤖 Expense Matching:")
        print(f"   Matches Found: {matching.get('matches_found', 0)}")
        print(f"   High Confidence: {matching.get('high_confidence', 0)}")
        print(f"   Average Confidence: {matching.get('avg_confidence', 0):.1%}")
    
    # Expense splitting results
    if 'expense_splitting' in steps:
        splitting = steps['expense_splitting']
        print(f"\n💰 Expense Splitting:")
        print(f"   Total Amount: ${splitting.get('total_amount', 0):.2f}")
        print(f"   Participants: {splitting.get('participant_count', 0)}")
        print(f"   Per Participant: ${splitting.get('amount_per_participant', 0):.2f}")
    
    # Report generation results
    if 'report_generation' in steps:
        reports = steps['report_generation']
        print(f"\n📊 Report Generation:")
        print(f"   Reports Created: {reports.get('reports_generated', 0)}")
        print(f"   Output Directory: {reports.get('output_directory', 'N/A')}")
    
    # File locations
    print(f"\n📁 Generated Files:")
    print(f"   Database: expense_reconciliation.db")
    print(f"   Reports: data/reports/")
    print(f"   Sample Data: data/uploads/")
    
    # Performance metrics
    print(f"\n⚡ Performance Metrics:")
    start_time = result.get('start_time')
    end_time = result.get('end_time')
    if start_time and end_time:
        duration = (datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds()
        print(f"   Total Duration: {duration:.2f} seconds")
    print(f"   Workflow ID: {result.get('workflow_id')}")


def start_api_server():
    """Start the FastAPI server"""
    print(f"\n🌐 Starting API Server")
    print("=" * 25)
    
    try:
        import uvicorn
        print("   🚀 Starting FastAPI server on http://localhost:8000")
        print("   📖 API Documentation: http://localhost:8000/docs")
        print("   🔍 Health Check: http://localhost:8000/health")
        print("\n   Press Ctrl+C to stop the server")
        
        # Update imports to use SQLite config
        import api
        
        # Start the server
        uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
        
    except KeyboardInterrupt:
        print(f"\n   ⚠️ Server stopped by user")
    except Exception as e:
        print(f"   ❌ Failed to start server: {e}")


def main():
    """Main execution function"""
    print("🎉 COMPLETE EXPENSE RECONCILIATION SOLUTION")
    print("=" * 50)
    print("This demo showcases the full end-to-end workflow:")
    print("   🔄 Data ingestion from Excel files")
    print("   🎯 Event matching and grouping")
    print("   📄 Document processing (simulated)")
    print("   🤖 LLM-powered expense matching")
    print("   💰 Intelligent expense splitting")
    print("   📊 Professional report generation")
    print("   📧 Notification system (demo mode)")
    print("=" * 50)
    
    # Ask user what they want to run
    print(f"\nChoose an option:")
    print(f"1. Run Complete Workflow (Recommended)")
    print(f"2. Start API Server Only")
    print(f"3. Run Workflow + Start API Server")
    
    try:
        choice = input(f"\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            success = run_complete_workflow()
            if success:
                print(f"\n🎉 Complete workflow executed successfully!")
                print(f"Check the data/reports/ directory for generated reports.")
            
        elif choice == "2":
            start_api_server()
            
        elif choice == "3":
            success = run_complete_workflow()
            if success:
                print(f"\n🎉 Workflow complete! Starting API server...")
                start_api_server()
            
        else:
            print(f"Invalid choice. Running complete workflow...")
            run_complete_workflow()
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Execution interrupted by user")
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 