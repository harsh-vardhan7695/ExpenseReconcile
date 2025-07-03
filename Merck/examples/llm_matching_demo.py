"""
Demonstration of LLM-based expense matching capabilities
This script shows how the intelligent matching engine works with real-world examples
"""

import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.matching_engine import create_matching_engine
from config import get_llm_config


def demo_llm_matching():
    """Demonstrate LLM-based expense matching with sample data"""
    
    print("🤖 LLM-Based Expense Matching Demo")
    print("=" * 50)
    
    # Initialize matching engine
    try:
        matching_engine = create_matching_engine()
        print("✅ LLM Matching Engine initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize matching engine: {e}")
        return
    
    # Sample extracted expenses from Cvent documents
    extracted_expenses = [
        {
            "id": 1,
            "event_id": "CONF2024_NYC",
            "amount": 285.50,
            "currency": "USD",
            "expense_date": "2024-03-15",
            "vendor_name": "Marriott Downtown NYC",
            "description": "Hotel accommodation for conference",
            "expense_type": "lodging"
        },
        {
            "id": 2,
            "event_id": "CONF2024_NYC", 
            "amount": 67.23,
            "currency": "USD",
            "expense_date": "2024-03-16",
            "vendor_name": "Joe's Pizza",
            "description": "Team dinner after conference",
            "expense_type": "meals"
        },
        {
            "id": 3,
            "event_id": "CONF2024_NYC",
            "amount": 150.00,
            "currency": "USD", 
            "expense_date": "2024-03-14",
            "vendor_name": "Yellow Cab Co",
            "description": "Airport transfer and local transport",
            "expense_type": "transportation"
        }
    ]
    
    # Sample Citibank transactions
    citibank_transactions = [
        {
            "id": 101,
            "event_id": "CONF2024_NYC",
            "transaction_id": "CITI_TXN_001",
            "amount": 285.50,
            "currency": "USD",
            "transaction_date": "2024-03-15",
            "description": "MARRIOTT HOTELS NYC",
            "vendor_name": "Marriott Hotels"
        },
        {
            "id": 102,
            "event_id": "CONF2024_NYC",
            "transaction_id": "CITI_TXN_002", 
            "amount": 67.23,
            "currency": "USD",
            "transaction_date": "2024-03-16",
            "description": "JOES PIZZA NYC",
            "vendor_name": "Joe's Pizza Restaurant"
        },
        {
            "id": 103,
            "event_id": "CONF2024_NYC",
            "transaction_id": "CITI_TXN_003",
            "amount": 148.75,  # Slightly different amount
            "currency": "USD",
            "transaction_date": "2024-03-14",
            "description": "YELLOW CAB NYC TAXI",
            "vendor_name": "NYC Taxi & Limousine"
        }
    ]
    
    # Sample Concur transactions
    concur_transactions = [
        {
            "id": 201,
            "event_id": "CONF2024_NYC",
            "transaction_id": "CONCUR_EXP_001",
            "amount": 285.50,
            "currency": "USD",
            "transaction_date": "2024-03-15",
            "expense_type": "Hotel",
            "vendor_name": "Marriott International",
            "description": "Conference hotel booking"
        },
        {
            "id": 202,
            "event_id": "CONF2024_NYC",
            "transaction_id": "CONCUR_EXP_002",
            "amount": 67.23,
            "currency": "USD", 
            "transaction_date": "2024-03-16",
            "expense_type": "Meals",
            "vendor_name": "Joe's Pizza NYC",
            "description": "Business meal - team dinner"
        },
        {
            "id": 203,
            "event_id": "CONF2024_NYC",
            "transaction_id": "CONCUR_EXP_003",
            "amount": 150.00,
            "currency": "USD",
            "transaction_date": "2024-03-14", 
            "expense_type": "Transportation",
            "vendor_name": "NYC Taxi Services",
            "description": "Ground transportation"
        }
    ]
    
    print(f"\n📊 Sample Data:")
    print(f"   - {len(extracted_expenses)} extracted expenses from Cvent documents")
    print(f"   - {len(citibank_transactions)} Citibank transactions")
    print(f"   - {len(concur_transactions)} Concur transactions")
    
    # Perform LLM-based matching
    print(f"\n🔍 Running LLM-based expense matching...")
    
    try:
        matches = matching_engine.match_expenses(
            extracted_expenses,
            citibank_transactions, 
            concur_transactions
        )
        
        print(f"✅ Matching completed! Found {len(matches)} expense matches")
        
        # Display detailed results
        print(f"\n📋 Detailed Matching Results:")
        print("=" * 50)
        
        for i, match in enumerate(matches, 1):
            expense = match["extracted_expense"]
            overall_confidence = match["overall_confidence"]
            
            print(f"\n🎯 Match #{i}: {expense['vendor_name']} - ${expense['amount']}")
            print(f"   Overall Confidence: {overall_confidence:.2%}")
            
            # Citibank match details
            if match.get("citibank_match"):
                citi_match = match["citibank_match"]
                print(f"   🏦 Citibank Match: {citi_match['confidence']:.2%} confidence")
                print(f"      Vendor: {citi_match['transaction']['vendor_name']}")
                print(f"      Amount: ${citi_match['transaction']['amount']}")
                print(f"      Reasoning: {citi_match['reasoning'][:100]}...")
            else:
                print(f"   🏦 Citibank Match: No match found")
            
            # Concur match details  
            if match.get("concur_match"):
                concur_match = match["concur_match"]
                print(f"   📊 Concur Match: {concur_match['confidence']:.2%} confidence")
                print(f"      Vendor: {concur_match['transaction']['vendor_name']}")
                print(f"      Amount: ${concur_match['transaction']['amount']}")
                print(f"      Reasoning: {concur_match['reasoning'][:100]}...")
            else:
                print(f"   📊 Concur Match: No match found")
            
            # LLM overall analysis
            if match.get("llm_reasoning"):
                print(f"   🧠 LLM Analysis: {match['llm_reasoning'][:150]}...")
            
            print(f"   ⚖️ Match Criteria: {json.dumps(match['match_criteria'], indent=4)}")
        
        # Summary statistics
        print(f"\n📈 Matching Statistics:")
        print("=" * 30)
        
        high_confidence = sum(1 for m in matches if m["overall_confidence"] >= 0.8)
        medium_confidence = sum(1 for m in matches if 0.6 <= m["overall_confidence"] < 0.8)
        low_confidence = sum(1 for m in matches if m["overall_confidence"] < 0.6)
        
        print(f"   High Confidence (≥80%): {high_confidence}")
        print(f"   Medium Confidence (60-80%): {medium_confidence}")
        print(f"   Low Confidence (<60%): {low_confidence}")
        
        citibank_matches = sum(1 for m in matches if m.get("citibank_match"))
        concur_matches = sum(1 for m in matches if m.get("concur_match"))
        both_matches = sum(1 for m in matches if m.get("citibank_match") and m.get("concur_match"))
        
        print(f"   Citibank Matches: {citibank_matches}/{len(matches)}")
        print(f"   Concur Matches: {concur_matches}/{len(matches)}")
        print(f"   Both Systems: {both_matches}/{len(matches)}")
        
        avg_confidence = sum(m["overall_confidence"] for m in matches) / len(matches)
        print(f"   Average Confidence: {avg_confidence:.2%}")
        
    except Exception as e:
        print(f"❌ Matching failed: {e}")
        import traceback
        traceback.print_exc()


def demo_complex_vendor_matching():
    """Demonstrate complex vendor name matching capabilities"""
    
    print(f"\n🏪 Complex Vendor Matching Demo")
    print("=" * 40)
    
    # Test cases with vendor name variations
    test_cases = [
        {
            "extracted_vendor": "McDonald's Restaurant",
            "transaction_vendors": [
                "MCDONALD'S #1234 NYC",
                "McDonalds Times Square", 
                "MCD NYC BROADWAY",
                "Burger King",
                "McDonald's Corp"
            ]
        },
        {
            "extracted_vendor": "Uber Technologies", 
            "transaction_vendors": [
                "UBER TRIP NYC",
                "UBER EATS DELIVERY",
                "LYFT INC",
                "UBER BV NETHERLANDS",
                "Yellow Cab Co"
            ]
        },
        {
            "extracted_vendor": "Amazon Web Services",
            "transaction_vendors": [
                "AWS CLOUD SERVICES",
                "AMAZON WEB SERVICES LLC",
                "AMZ AWS USAGE",
                "Microsoft Azure",
                "Amazon.com"
            ]
        }
    ]
    
    matching_engine = create_matching_engine()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case #{i}: {test_case['extracted_vendor']}")
        
        # Create sample expense and transactions for testing
        expense = {
            "id": i,
            "amount": 100.00,
            "currency": "USD",
            "expense_date": "2024-03-15",
            "vendor_name": test_case["extracted_vendor"],
            "description": "Business expense",
            "expense_type": "other"
        }
        
        transactions = []
        for j, vendor in enumerate(test_case["transaction_vendors"]):
            transactions.append({
                "id": j,
                "amount": 100.00 + (j * 5),  # Slight amount variations
                "currency": "USD",
                "transaction_date": "2024-03-15",
                "vendor_name": vendor,
                "description": f"Transaction with {vendor}"
            })
        
        try:
            # Test LLM matching
            match_result = matching_engine._find_best_llm_match(expense, transactions, "Test")
            
            if match_result:
                matched_vendor = match_result["transaction"]["vendor_name"]
                confidence = match_result["confidence"]
                print(f"   ✅ Best Match: {matched_vendor} (Confidence: {confidence:.2%})")
                print(f"   📝 Reasoning: {match_result['reasoning'][:100]}...")
            else:
                print(f"   ❌ No suitable match found")
                
        except Exception as e:
            print(f"   ⚠️ Error in matching: {e}")


if __name__ == "__main__":
    # Check if configuration is available
    try:
        config = get_llm_config()
        print("🔧 Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Please ensure your Azure OpenAI settings are configured in config.py")
        sys.exit(1)
    
    # Run demos
    demo_llm_matching()
    demo_complex_vendor_matching()
    
    print(f"\n🎉 Demo completed!")
    print("This demonstrates how the LLM-based matching engine provides:")
    print("   • Intelligent vendor name matching")
    print("   • Contextual description analysis") 
    print("   • Confidence scoring with detailed reasoning")
    print("   • Robust handling of amount and date variations")
    print("   • Cross-system consistency analysis") 