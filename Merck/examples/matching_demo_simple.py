"""
Simple Expense Matching Demo - Core Functionality
This demo showcases the LLM-based expense matching engine
"""

import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.matching_engine import create_matching_engine
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def demonstrate_matching_engine():
    """Demonstrate the intelligent expense matching capabilities"""
    
    print("🤖 Expense Reconciliation System - Core Matching Demo")
    print("=" * 60)
    
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
        },
        {
            "id": 4,
            "event_id": "CONF2024_NYC",
            "amount": 42.99,
            "currency": "USD",
            "expense_date": "2024-03-16",
            "vendor_name": "Starbucks Coffee",
            "description": "Coffee for morning meeting",
            "expense_type": "meals"
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
        },
        {
            "id": 104,
            "event_id": "CONF2024_NYC",
            "transaction_id": "CITI_TXN_004",
            "amount": 42.99,
            "currency": "USD",
            "transaction_date": "2024-03-16",
            "description": "STARBUCKS #1234 NYC",
            "vendor_name": "Starbucks Corporation"
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
        },
        {
            "id": 204,
            "event_id": "CONF2024_NYC",
            "transaction_id": "CONCUR_EXP_004",
            "amount": 42.99,
            "currency": "USD",
            "transaction_date": "2024-03-16",
            "expense_type": "Meals",
            "vendor_name": "Starbucks",
            "description": "Coffee and breakfast"
        }
    ]
    
    print(f"\n📊 Sample Data Overview:")
    print(f"   - {len(extracted_expenses)} extracted expenses from Cvent documents")
    print(f"   - {len(citibank_transactions)} Citibank transactions")
    print(f"   - {len(concur_transactions)} Concur transactions")
    
    # Initialize matching engine
    print(f"\n🔧 Initializing Matching Engine...")
    try:
        matching_engine = create_matching_engine()
        print("✅ LLM-based matching engine initialized successfully")
        print("💡 Note: Falls back to rule-based matching if LLM unavailable")
    except Exception as e:
        print(f"❌ Failed to initialize matching engine: {e}")
        return
    
    # Perform matching
    print(f"\n🔍 Running Intelligent Expense Matching...")
    try:
        matches = matching_engine.match_expenses(
            extracted_expenses,
            citibank_transactions,
            concur_transactions
        )
        
        print(f"✅ Matching completed successfully!")
        
        # Analyze results
        analyze_matching_results(matches)
        
        # Show detailed results
        display_detailed_results(matches)
        
    except Exception as e:
        print(f"❌ Matching failed: {e}")
        import traceback
        traceback.print_exc()


def analyze_matching_results(matches):
    """Analyze and display matching statistics"""
    
    print(f"\n📈 Matching Analysis")
    print("=" * 25)
    
    # Confidence analysis
    high_confidence = [m for m in matches if m["overall_confidence"] >= 0.8]
    medium_confidence = [m for m in matches if 0.6 <= m["overall_confidence"] < 0.8]
    low_confidence = [m for m in matches if m["overall_confidence"] < 0.6]
    
    print(f"🎯 Confidence Distribution:")
    print(f"   High (≥80%): {len(high_confidence)}/{len(matches)} matches")
    print(f"   Medium (60-80%): {len(medium_confidence)}/{len(matches)} matches")
    print(f"   Low (<60%): {len(low_confidence)}/{len(matches)} matches")
    
    # System coverage
    citibank_matches = [m for m in matches if m.get("citibank_match")]
    concur_matches = [m for m in matches if m.get("concur_match")]
    both_matches = [m for m in matches if m.get("citibank_match") and m.get("concur_match")]
    
    print(f"\n🏦 System Coverage:")
    print(f"   Citibank matches: {len(citibank_matches)}/{len(matches)}")
    print(f"   Concur matches: {len(concur_matches)}/{len(matches)}")
    print(f"   Both systems: {len(both_matches)}/{len(matches)}")
    
    # Confidence statistics
    if matches:
        avg_confidence = sum(m["overall_confidence"] for m in matches) / len(matches)
        max_confidence = max(m["overall_confidence"] for m in matches)
        min_confidence = min(m["overall_confidence"] for m in matches)
        
        print(f"\n📊 Confidence Statistics:")
        print(f"   Average: {avg_confidence:.1%}")
        print(f"   Highest: {max_confidence:.1%}")
        print(f"   Lowest: {min_confidence:.1%}")


def display_detailed_results(matches):
    """Display detailed matching results"""
    
    print(f"\n📋 Detailed Matching Results")
    print("=" * 35)
    
    for i, match in enumerate(matches, 1):
        expense = match["extracted_expense"]
        overall_confidence = match["overall_confidence"]
        
        print(f"\n🎯 Match #{i}: {expense['vendor_name']}")
        print(f"   💰 Amount: ${expense['amount']} {expense['currency']}")
        print(f"   📅 Date: {expense['expense_date']}")
        print(f"   📋 Type: {expense['expense_type']}")
        print(f"   ⭐ Overall Confidence: {overall_confidence:.1%}")
        
        # Citibank match details
        if match.get("citibank_match"):
            citi_match = match["citibank_match"]
            print(f"   🏦 Citibank Match:")
            print(f"      Vendor: {citi_match['transaction']['vendor_name']}")
            print(f"      Amount: ${citi_match['transaction']['amount']}")
            print(f"      Confidence: {citi_match['confidence']:.1%}")
            if len(citi_match.get('reasoning', '')) > 0:
                reasoning = citi_match['reasoning'][:80] + "..." if len(citi_match['reasoning']) > 80 else citi_match['reasoning']
                print(f"      Reasoning: {reasoning}")
        else:
            print(f"   🏦 Citibank Match: ❌ No match found")
        
        # Concur match details
        if match.get("concur_match"):
            concur_match = match["concur_match"]
            print(f"   📊 Concur Match:")
            print(f"      Vendor: {concur_match['transaction']['vendor_name']}")
            print(f"      Amount: ${concur_match['transaction']['amount']}")
            print(f"      Confidence: {concur_match['confidence']:.1%}")
            if len(concur_match.get('reasoning', '')) > 0:
                reasoning = concur_match['reasoning'][:80] + "..." if len(concur_match['reasoning']) > 80 else concur_match['reasoning']
                print(f"      Reasoning: {reasoning}")
        else:
            print(f"   📊 Concur Match: ❌ No match found")
        
        # Overall analysis
        if match.get("llm_reasoning"):
            reasoning = match['llm_reasoning'][:100] + "..." if len(match['llm_reasoning']) > 100 else match['llm_reasoning']
            print(f"   🧠 LLM Analysis: {reasoning}")


def demonstrate_vendor_matching_intelligence():
    """Demonstrate intelligent vendor matching capabilities"""
    
    print(f"\n🏪 Vendor Matching Intelligence Demo")
    print("=" * 45)
    
    # Test cases showcasing intelligent vendor matching
    test_cases = [
        {
            "name": "Restaurant Chain Variations",
            "expense": {
                "vendor_name": "McDonald's Restaurant",
                "amount": 15.99,
                "currency": "USD",
                "expense_date": "2024-03-15"
            },
            "transactions": [
                {"vendor_name": "MCDONALD'S #1234 NYC", "amount": 15.99},
                {"vendor_name": "McDonalds Times Square", "amount": 16.05},
                {"vendor_name": "MCD NYC BROADWAY", "amount": 15.99},
                {"vendor_name": "Burger King", "amount": 15.99},
            ]
        },
        {
            "name": "Technology Services",
            "expense": {
                "vendor_name": "Amazon Web Services",
                "amount": 125.50,
                "currency": "USD",
                "expense_date": "2024-03-15"
            },
            "transactions": [
                {"vendor_name": "AWS CLOUD SERVICES", "amount": 125.50},
                {"vendor_name": "AMAZON WEB SERVICES LLC", "amount": 125.50},
                {"vendor_name": "AMZ AWS USAGE", "amount": 125.50},
                {"vendor_name": "Microsoft Azure", "amount": 125.50},
            ]
        },
        {
            "name": "Transportation Services",
            "expense": {
                "vendor_name": "Uber Technologies",
                "amount": 23.45,
                "currency": "USD",
                "expense_date": "2024-03-15"
            },
            "transactions": [
                {"vendor_name": "UBER TRIP NYC", "amount": 23.45},
                {"vendor_name": "UBER EATS DELIVERY", "amount": 23.45},
                {"vendor_name": "UBER BV NETHERLANDS", "amount": 23.45},
                {"vendor_name": "LYFT INC", "amount": 23.45},
            ]
        }
    ]
    
    matching_engine = create_matching_engine()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case #{i}: {test_case['name']}")
        print(f"   Expense Vendor: {test_case['expense']['vendor_name']}")
        
        # Prepare transaction data
        transactions = []
        for j, trans in enumerate(test_case['transactions']):
            transactions.append({
                "id": j,
                "amount": trans["amount"],
                "currency": "USD",
                "transaction_date": "2024-03-15",
                "vendor_name": trans["vendor_name"],
                "description": f"Transaction with {trans['vendor_name']}"
            })
        
        try:
            # Test matching
            match_result = matching_engine._find_best_llm_match(
                test_case['expense'], 
                transactions, 
                "Demo"
            )
            
            if match_result:
                matched_vendor = match_result["transaction"]["vendor_name"]
                confidence = match_result["confidence"]
                print(f"   ✅ Best Match: {matched_vendor}")
                print(f"   📊 Confidence: {confidence:.1%}")
                
                # Show criteria breakdown if available
                if "criteria_scores" in match_result:
                    criteria = match_result["criteria_scores"]
                    print(f"   📋 Criteria Breakdown:")
                    for criterion, score in criteria.items():
                        print(f"      {criterion.replace('_', ' ').title()}: {score:.1%}")
            else:
                print(f"   ❌ No suitable match found")
                
        except Exception as e:
            print(f"   ⚠️ Error in matching: {e}")


if __name__ == "__main__":
    try:
        # Run core matching demo
        demonstrate_matching_engine()
        
        # Run vendor intelligence demo
        demonstrate_vendor_matching_intelligence()
        
        print(f"\n🎉 Demo Completed Successfully!")
        print("\n💡 Key Takeaways:")
        print("   🤖 LLM-based matching provides intelligent vendor understanding")
        print("   🛡️ System gracefully falls back to rule-based matching")
        print("   📊 Detailed confidence scoring and reasoning")
        print("   🔄 Handles complex vendor name variations automatically")
        print("   ⚡ Ready for production use with proper API credentials")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc() 