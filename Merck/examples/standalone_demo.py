"""
Standalone Expense Reconciliation System Demo
This demo showcases the complete system functionality with mock data
"""

import json
import os
import sys
from datetime import datetime, timedelta
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.matching_engine import create_matching_engine
from agents.data_ingestion_agent import DataIngestionAgent
from agents.event_matching_agent import EventMatchingAgent
from agents.expense_splitting_agent import ExpenseSplittingAgent
from agents.report_generation_agent import ReportGenerationAgent


def create_sample_data():
    """Create comprehensive sample data for demonstration"""
    
    print("📋 Creating Sample Data")
    print("=" * 30)
    
    # Create sample directories
    os.makedirs("data/demo", exist_ok=True)
    
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
        }
    ]
    
    # Create Excel files
    citibank_df = pd.DataFrame(citibank_data)
    concur_df = pd.DataFrame(concur_data)
    
    citibank_file = "data/demo/citibank_transactions.xlsx"
    concur_file = "data/demo/concur_transactions.xlsx"
    
    citibank_df.to_excel(citibank_file, index=False)
    concur_df.to_excel(concur_file, index=False)
    
    print(f"✅ Created {citibank_file} with {len(citibank_data)} transactions")
    print(f"✅ Created {concur_file} with {len(concur_data)} transactions")
    
    # Sample extracted expenses (simulating LLM extraction from documents)
    extracted_expenses = [
        {
            "id": 1,
            "event_id": "CONF2024_NYC",
            "amount": 285.50,
            "currency": "USD",
            "expense_date": "2024-03-15",
            "vendor_name": "Marriott Downtown NYC",
            "description": "Hotel accommodation for conference",
            "expense_type": "lodging",
            "document_source": "receipt_001.pdf"
        },
        {
            "id": 2,
            "event_id": "CONF2024_NYC",
            "amount": 67.23,
            "currency": "USD", 
            "expense_date": "2024-03-16",
            "vendor_name": "Joe's Pizza",
            "description": "Team dinner after conference",
            "expense_type": "meals",
            "document_source": "receipt_002.jpg"
        },
        {
            "id": 3,
            "event_id": "CONF2024_NYC",
            "amount": 150.00,
            "currency": "USD",
            "expense_date": "2024-03-14",
            "vendor_name": "Yellow Cab Co",
            "description": "Airport transfer and local transport",
            "expense_type": "transportation",
            "document_source": "receipt_003.pdf"
        }
    ]
    
    # Sample participants
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
    
    return {
        "citibank_file": citibank_file,
        "concur_file": concur_file,
        "extracted_expenses": extracted_expenses,
        "participants": participants,
        "citibank_transactions": citibank_data,
        "concur_transactions": concur_data
    }


def demo_data_ingestion(sample_data):
    """Demonstrate data ingestion capabilities"""
    
    print("\n🔄 Data Ingestion Demo")
    print("=" * 30)
    
    try:
        # Initialize data ingestion agent
        ingestion_agent = DataIngestionAgent()
        
        # Process Citibank file
        print("📊 Processing Citibank transactions...")
        citibank_result = ingestion_agent.process_citibank_file(sample_data["citibank_file"])
        print(f"✅ Processed {len(citibank_result['transactions'])} Citibank transactions")
        
        # Process Concur file  
        print("📊 Processing Concur transactions...")
        concur_result = ingestion_agent.process_concur_file(sample_data["concur_file"])
        print(f"✅ Processed {len(concur_result['transactions'])} Concur transactions")
        
        return {
            "citibank_result": citibank_result,
            "concur_result": concur_result
        }
        
    except Exception as e:
        print(f"❌ Data ingestion failed: {e}")
        return None


def demo_event_matching(ingestion_result):
    """Demonstrate event matching capabilities"""
    
    print("\n🎯 Event Matching Demo")
    print("=" * 30)
    
    try:
        # Initialize event matching agent
        event_agent = EventMatchingAgent()
        
        # Group transactions by event ID
        citibank_transactions = ingestion_result["citibank_result"]["transactions"]
        concur_transactions = ingestion_result["concur_result"]["transactions"]
        
        print("🔍 Grouping transactions by Event ID...")
        event_result = event_agent.group_transactions_by_event(
            citibank_transactions,
            concur_transactions
        )
        
        print(f"✅ Found {len(event_result['matching_event_ids'])} matching events:")
        for event_id in event_result['matching_event_ids']:
            citi_count = len(event_result['citibank_groups'][event_id])
            concur_count = len(event_result['concur_groups'][event_id])
            print(f"   📋 {event_id}: {citi_count} Citibank + {concur_count} Concur transactions")
            
        return event_result
        
    except Exception as e:
        print(f"❌ Event matching failed: {e}")
        return None


def demo_expense_matching(sample_data, event_result):
    """Demonstrate LLM-based expense matching with fallback"""
    
    print("\n🤖 Expense Matching Demo (with Fallback)")
    print("=" * 45)
    
    try:
        # Initialize matching engine
        matching_engine = create_matching_engine()
        
        # Prepare transaction data
        citibank_transactions = []
        concur_transactions = []
        
        for event_id in event_result['matching_event_ids']:
            citibank_transactions.extend(event_result['citibank_groups'][event_id])
            concur_transactions.extend(event_result['concur_groups'][event_id])
        
        print(f"🔍 Matching {len(sample_data['extracted_expenses'])} extracted expenses...")
        print("💡 Note: Using rule-based fallback (LLM may not be available)")
        
        # Perform matching
        matches = matching_engine.match_expenses(
            sample_data['extracted_expenses'],
            citibank_transactions,
            concur_transactions
        )
        
        print(f"✅ Matching completed! Found {len(matches)} expense matches")
        
        # Display results
        print("\n📋 Matching Results:")
        print("-" * 40)
        
        for i, match in enumerate(matches, 1):
            expense = match["extracted_expense"]
            confidence = match["overall_confidence"]
            
            print(f"\n🎯 Match #{i}: {expense['vendor_name']} - ${expense['amount']}")
            print(f"   Overall Confidence: {confidence:.1%}")
            
            if match.get("citibank_match"):
                citi_conf = match["citibank_match"]["confidence"]
                print(f"   🏦 Citibank: {citi_conf:.1%} confidence")
            else:
                print(f"   🏦 Citibank: No match")
                
            if match.get("concur_match"):
                concur_conf = match["concur_match"]["confidence"]
                print(f"   📊 Concur: {concur_conf:.1%} confidence")
            else:
                print(f"   📊 Concur: No match")
        
        return matches
        
    except Exception as e:
        print(f"❌ Expense matching failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def demo_expense_splitting(sample_data, matches):
    """Demonstrate expense splitting capabilities"""
    
    print("\n💰 Expense Splitting Demo")
    print("=" * 30)
    
    try:
        # Initialize splitting agent
        splitting_agent = ExpenseSplittingAgent()
        
        # Prepare expense data with matches
        expenses_to_split = []
        for match in matches:
            if match["overall_confidence"] >= 0.5:  # Only split confident matches
                expense = match["extracted_expense"].copy()
                expense["match_confidence"] = match["overall_confidence"]
                expenses_to_split.append(expense)
        
        print(f"🔄 Splitting {len(expenses_to_split)} expenses among {len(sample_data['participants'])} participants")
        
        # Perform equal splitting
        split_result = splitting_agent.split_expenses_equally(
            "CONF2024_NYC",
            expenses_to_split,
            sample_data['participants']
        )
        
        print(f"✅ Expenses split successfully!")
        print(f"   Total Amount: ${split_result['total_amount']:.2f}")
        print(f"   Per Participant: ${split_result['amount_per_participant']:.2f}")
        
        # Display individual allocations
        print("\n👥 Individual Allocations:")
        print("-" * 35)
        
        for allocation in split_result['participant_allocations']:
            participant = allocation['participant']
            amount = allocation['total_amount']
            count = len(allocation['expense_shares'])
            print(f"   {participant['name']}: ${amount:.2f} ({count} expenses)")
            
        return split_result
        
    except Exception as e:
        print(f"❌ Expense splitting failed: {e}")
        return None


def demo_report_generation(split_result):
    """Demonstrate report generation capabilities"""
    
    print("\n📊 Report Generation Demo") 
    print("=" * 30)
    
    try:
        # Initialize report generation agent
        report_agent = ReportGenerationAgent()
        
        # Create reports directory
        os.makedirs("data/demo/reports", exist_ok=True)
        
        print("📄 Generating individual expense reports...")
        
        reports_generated = []
        for allocation in split_result['participant_allocations']:
            participant = allocation['participant']
            
            # Generate individual report
            report_path = report_agent.generate_individual_report(
                participant,
                allocation['expense_shares'],
                split_result['event_id'],
                output_dir="data/demo/reports"
            )
            
            reports_generated.append({
                "participant": participant,
                "report_path": report_path,
                "total_amount": allocation['total_amount']
            })
            
            print(f"   ✅ {participant['name']}: {report_path}")
        
        print(f"\n📈 Report Summary:")
        print(f"   Reports Generated: {len(reports_generated)}")
        print(f"   Output Directory: data/demo/reports/")
        
        return reports_generated
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return None


def demo_system_integration():
    """Demonstrate complete system integration"""
    
    print("\n🎉 Complete System Integration Demo")
    print("=" * 45)
    
    # Step 1: Create sample data
    sample_data = create_sample_data()
    
    # Step 2: Data ingestion
    ingestion_result = demo_data_ingestion(sample_data)
    if not ingestion_result:
        return
    
    # Step 3: Event matching
    event_result = demo_event_matching(ingestion_result)
    if not event_result:
        return
        
    # Step 4: Expense matching
    matches = demo_expense_matching(sample_data, event_result)
    if not matches:
        return
        
    # Step 5: Expense splitting
    split_result = demo_expense_splitting(sample_data, matches)
    if not split_result:
        return
        
    # Step 6: Report generation
    reports = demo_report_generation(split_result)
    if not reports:
        return
    
    # Final summary
    print("\n🏆 Demo Completion Summary")
    print("=" * 35)
    print(f"✅ Data Ingestion: {len(sample_data['citibank_transactions'])} + {len(sample_data['concur_transactions'])} transactions")
    print(f"✅ Event Matching: {len(event_result['matching_event_ids'])} events identified")
    print(f"✅ Expense Matching: {len(matches)} expenses processed")
    print(f"✅ Expense Splitting: ${split_result['total_amount']:.2f} split among {len(sample_data['participants'])} participants")
    print(f"✅ Report Generation: {len(reports)} individual reports created")
    
    print(f"\n💡 Key Insights:")
    high_confidence = sum(1 for m in matches if m["overall_confidence"] >= 0.8)
    print(f"   🎯 High confidence matches: {high_confidence}/{len(matches)}")
    print(f"   💰 Average expense per participant: ${split_result['amount_per_participant']:.2f}")
    print(f"   📊 System successfully handled fallback when LLM unavailable")
    
    print(f"\n📁 Generated Files:")
    print(f"   📋 Sample data: data/demo/")
    print(f"   📊 Reports: data/demo/reports/")


if __name__ == "__main__":
    print("🚀 Expense Reconciliation System - Standalone Demo")
    print("=" * 55)
    print("This demo showcases the complete system without requiring:")
    print("   • Database setup")
    print("   • Valid LLM API credentials")  
    print("   • Email configuration")
    print("\nThe system gracefully falls back to rule-based matching!")
    print("=" * 55)
    
    try:
        demo_system_integration()
        
        print(f"\n🎉 Demo completed successfully!")
        print("The system demonstrates:")
        print("   🔄 End-to-end workflow orchestration")
        print("   🤖 Intelligent matching with fallback")
        print("   💰 Fair expense splitting")
        print("   📊 Professional report generation")
        print("   🛡️ Robust error handling")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc() 