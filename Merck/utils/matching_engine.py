from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import pandas as pd
import json
import openai
try:
    from config_sqlite import get_llm_config, settings
except ImportError:
    from config import get_llm_config, settings


class ExpenseMatchingEngine:
    def __init__(self):
        self.amount_tolerance = settings.AMOUNT_TOLERANCE
        self.date_tolerance_days = settings.DATE_TOLERANCE_DAYS
        self.fuzzy_threshold = settings.FUZZY_MATCH_THRESHOLD
        
        # Initialize Azure OpenAI client
        llm_config = get_llm_config()
        config = llm_config["config_list"][0]
        self.client = openai.AzureOpenAI(
            api_key=config["api_key"],
            api_version=config["api_version"],
            azure_endpoint=config["base_url"]
        )
        self.model = config["model"]
    
    def match_expenses(
        self, 
        extracted_expenses: List[Dict],
        citibank_transactions: List[Dict],
        concur_transactions: List[Dict]
    ) -> List[Dict]:
        """
        Match extracted expenses with Citibank and Concur transactions using LLM
        Returns list of matches with confidence scores
        """
        matches = []
        
        for expense in extracted_expenses:
            # Find best matches in both systems using LLM
            citibank_match = self._find_best_llm_match(expense, citibank_transactions, "Citibank")
            concur_match = self._find_best_llm_match(expense, concur_transactions, "Concur")
            
            # Calculate overall confidence and match criteria using LLM
            overall_analysis = self._analyze_overall_match(expense, citibank_match, concur_match)
            
            match_result = {
                "extracted_expense": expense,
                "citibank_match": citibank_match,
                "concur_match": concur_match,
                "overall_confidence": overall_analysis["confidence"],
                "match_criteria": overall_analysis["criteria"],
                "llm_reasoning": overall_analysis["reasoning"]
            }
            
            matches.append(match_result)
        
        return matches
    
    def _find_best_llm_match(self, expense: Dict, transactions: List[Dict], system_name: str) -> Optional[Dict]:
        """Find the best matching transaction using LLM analysis"""
        if not transactions:
            return None
        
        # Prepare data for LLM analysis
        expense_data = {
            "amount": expense.get("amount"),
            "currency": expense.get("currency"),
            "date": str(expense.get("expense_date")),
            "vendor": expense.get("vendor_name"),
            "description": expense.get("description"),
            "expense_type": expense.get("expense_type")
        }
        
        # Create prompt for LLM matching
        prompt = self._create_matching_prompt(expense_data, transactions, system_name)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert expense matching system. Analyze the given expense and find the best matching transaction from the provided list. 

Your analysis should consider:
1. Amount similarity (within reasonable tolerance)
2. Date proximity (within a few days)
3. Vendor/merchant name similarity (accounting for variations, abbreviations)
4. Currency matching
5. Description context

Return a JSON response with:
{
    "best_match_index": <index of best match or null>,
    "confidence": <score 0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "criteria_scores": {
        "amount_match": <0.0-1.0>,
        "date_match": <0.0-1.0>,
        "vendor_match": <0.0-1.0>,
        "currency_match": <0.0-1.0>,
        "description_match": <0.0-1.0>
    }
}"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse LLM response
            llm_result = json.loads(response.choices[0].message.content)
            
            if llm_result["best_match_index"] is not None:
                matched_transaction = transactions[llm_result["best_match_index"]]
                return {
                    "transaction": matched_transaction,
                    "confidence": llm_result["confidence"],
                    "criteria_scores": llm_result["criteria_scores"],
                    "reasoning": llm_result["reasoning"]
                }
            
            return None
            
        except Exception as e:
            print(f"Error in LLM matching for {system_name}: {e}")
            # Fallback to simple rule-based matching
            return self._fallback_rule_based_match(expense, transactions)
    
    def _create_matching_prompt(self, expense: Dict, transactions: List[Dict], system_name: str) -> str:
        """Create a detailed prompt for LLM matching analysis"""
        
        prompt = f"""
EXPENSE TO MATCH:
Amount: {expense['amount']} {expense['currency']}
Date: {expense['date']}
Vendor: {expense['vendor']}
Description: {expense['description']}
Type: {expense['expense_type']}

{system_name.upper()} TRANSACTIONS TO COMPARE:
"""
        
        for i, transaction in enumerate(transactions):
            prompt += f"""
[{i}] Amount: {transaction.get('amount')} {transaction.get('currency')}
    Date: {transaction.get('transaction_date', transaction.get('date'))}
    Vendor: {transaction.get('vendor_name', transaction.get('vendor'))}
    Description: {transaction.get('description')}
    Transaction ID: {transaction.get('transaction_id')}
"""
        
        prompt += f"""
MATCHING CRITERIA:
- Amount tolerance: {self.amount_tolerance * 100}%
- Date tolerance: {self.date_tolerance_days} days
- Consider vendor name variations, abbreviations, and common formats
- Account for different description formats
- Currency must match exactly

Find the best matching transaction and provide confidence score with detailed reasoning.
"""
        
        return prompt
    
    def _analyze_overall_match(self, expense: Dict, citibank_match: Optional[Dict], concur_match: Optional[Dict]) -> Dict:
        """Use LLM to analyze overall match quality across both systems"""
        
        analysis_prompt = f"""
EXPENSE ITEM:
Amount: {expense.get('amount')} {expense.get('currency')}
Date: {expense.get('expense_date')}
Vendor: {expense.get('vendor_name')}
Description: {expense.get('description')}

CITIBANK MATCH:
{json.dumps(citibank_match, indent=2) if citibank_match else "No match found"}

CONCUR MATCH:
{json.dumps(concur_match, indent=2) if concur_match else "No match found"}

Analyze the overall quality of these matches and provide:
1. Overall confidence score (0.0-1.0) for this expense reconciliation
2. Detailed criteria breakdown
3. Reasoning for the confidence score
4. Any red flags or concerns

Consider:
- Having matches in both systems increases confidence
- Consistency between Citibank and Concur matches
- Quality of individual matches
- Any discrepancies that might indicate issues

Return JSON format:
{{
    "confidence": <0.0-1.0>,
    "criteria": {{
        "has_citibank_match": <boolean>,
        "has_concur_match": <boolean>,
        "citibank_confidence": <0.0-1.0 or null>,
        "concur_confidence": <0.0-1.0 or null>,
        "cross_system_consistency": <0.0-1.0>,
        "overall_quality": <0.0-1.0>
    }},
    "reasoning": "<detailed analysis>",
    "concerns": ["<list of any concerns>"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert financial reconciliation analyst. Analyze expense matches across multiple systems and provide comprehensive assessment of match quality and confidence."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error in LLM overall analysis: {e}")
            # Fallback analysis
            return self._fallback_overall_analysis(citibank_match, concur_match)
    
    def _fallback_rule_based_match(self, expense: Dict, transactions: List[Dict]) -> Optional[Dict]:
        """Fallback to simple rule-based matching if LLM fails"""
        best_match = None
        best_score = 0.0
        
        expense_amount = float(expense.get("amount", 0))
        expense_date = expense.get("expense_date")
        
        if isinstance(expense_date, str):
            try:
                expense_date = datetime.strptime(expense_date, "%Y-%m-%d")
            except:
                expense_date = None
        
        for transaction in transactions:
            score = 0.0
            criteria_count = 0
            
            # Amount matching
            trans_amount = float(transaction.get("amount", 0))
            if abs(expense_amount - trans_amount) <= (expense_amount * self.amount_tolerance):
                score += 0.4
            criteria_count += 1
            
            # Date matching
            if expense_date:
                trans_date = transaction.get("transaction_date") or transaction.get("date")
                if isinstance(trans_date, str):
                    try:
                        trans_date = datetime.strptime(trans_date, "%Y-%m-%d")
                        date_diff = abs((expense_date - trans_date).days)
                        if date_diff <= self.date_tolerance_days:
                            score += 0.3 * (1 - date_diff / self.date_tolerance_days)
                    except:
                        pass
            criteria_count += 1
            
            # Simple vendor matching
            expense_vendor = expense.get("vendor_name", "").lower()
            trans_vendor = transaction.get("vendor_name", transaction.get("vendor", "")).lower()
            if expense_vendor and trans_vendor:
                if expense_vendor in trans_vendor or trans_vendor in expense_vendor:
                    score += 0.2
            criteria_count += 1
            
            # Currency matching
            if expense.get("currency") == transaction.get("currency"):
                score += 0.1
            criteria_count += 1
            
            normalized_score = score
            if normalized_score > best_score:
                best_score = normalized_score
                best_match = {
                    "transaction": transaction,
                    "confidence": normalized_score,
                    "criteria_scores": {
                        "amount_match": min(1.0, score * 2.5),  # Approximate breakdown
                        "date_match": 0.5,
                        "vendor_match": 0.5,
                        "currency_match": 1.0 if expense.get("currency") == transaction.get("currency") else 0.0,
                        "description_match": 0.5
                    },
                    "reasoning": "Fallback rule-based matching"
                }
        
        return best_match if best_score > 0.3 else None
    
    def _fallback_overall_analysis(self, citibank_match: Optional[Dict], concur_match: Optional[Dict]) -> Dict:
        """Fallback overall analysis if LLM fails"""
        has_citibank = citibank_match is not None
        has_concur = concur_match is not None
        
        citibank_conf = citibank_match["confidence"] if has_citibank else 0.0
        concur_conf = concur_match["confidence"] if has_concur else 0.0
        
        # Simple confidence calculation
        if has_citibank and has_concur:
            confidence = (citibank_conf + concur_conf) / 2 * 1.2  # Boost for having both
        elif has_citibank or has_concur:
            confidence = max(citibank_conf, concur_conf) * 0.8  # Reduce for having only one
        else:
            confidence = 0.0
        
        confidence = min(1.0, confidence)  # Cap at 1.0
        
        return {
            "confidence": confidence,
            "criteria": {
                "has_citibank_match": has_citibank,
                "has_concur_match": has_concur,
                "citibank_confidence": citibank_conf if has_citibank else None,
                "concur_confidence": concur_conf if has_concur else None,
                "cross_system_consistency": 0.7 if has_citibank and has_concur else 0.5,
                "overall_quality": confidence
            },
            "reasoning": "Fallback analysis: Simple rule-based confidence calculation",
            "concerns": ["LLM analysis unavailable, using fallback logic"]
        }


def create_matching_engine():
    """Factory function to create a matching engine instance"""
    return ExpenseMatchingEngine() 