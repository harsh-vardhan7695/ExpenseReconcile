# Expense Reconciliation System

A comprehensive agentic expense reconciliation system using AutoGen framework that automates the process of matching, splitting, and reporting expenses from multiple sources.

## 🎯 Overview

This system implements the complete expense reconciliation workflow shown in your flowchart:

1. **Data Ingestion**: Process Citibank and Concur transaction Excel files
2. **Event Matching**: Group transactions by Event ID and identify matching events
3. **Document Processing**: Extract expense data from Cvent documents using multimodal LLM
4. **Expense Matching**: Match extracted expenses with transaction records using advanced algorithms
5. **Expense Splitting**: Split expenses equally among participants
6. **Report Generation**: Create individual expense reports for each participant
7. **Notification**: Send email notifications with expense reports

## 🏗️ Architecture

### Agentic Design Patterns Used

- **Orchestrator Pattern**: Main coordinator that manages the entire workflow
- **Specialist Agents**: Each agent handles a specific domain (ingestion, matching, processing, etc.)
- **Pipeline Pattern**: Sequential processing with error handling and rollback
- **Observer Pattern**: Comprehensive logging and status tracking

### Key Agents

1. **Data Ingestion Agent**: Processes Excel files from Citibank and Concur
2. **Event Matching Agent**: Groups transactions by Event ID
3. **Document Processing Agent**: Extracts expenses using multimodal LLM
4. **Expense Matching Agent**: Sophisticated matching algorithm
5. **Expense Splitting Agent**: Fair expense distribution among participants
6. **Report Generation Agent**: Creates detailed individual reports
7. **Notification Agent**: Sends email notifications with attachments

## 🚀 Features

### Core Capabilities
- ✅ **Multimodal LLM Integration**: Extract expenses from PDFs and images
- ✅ **🤖 LLM-Powered Matching**: AI-based expense matching with contextual reasoning
- ✅ **Equal Expense Splitting**: Fair distribution among participants
- ✅ **Automated Reporting**: Individual Excel reports with breakdowns
- ✅ **Email Notifications**: Automated participant notifications
- ✅ **Database Integration**: PostgreSQL with comprehensive logging
- ✅ **REST API**: FastAPI interface for integration
- ✅ **Error Handling**: Robust error recovery and logging

### Advanced Features
- **Confidence Scoring**: Machine learning-based match confidence
- **Weighted Splitting**: Custom participant weights for proportional splitting
- **Audit Trail**: Complete transaction history and matching criteria
- **Status Tracking**: Real-time workflow progress monitoring
- **Flexible Configuration**: Configurable matching thresholds and tolerances

## 📦 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Azure OpenAI access

### Setup

1. **Clone and install dependencies**:
```bash
git clone <repository>
cd expense-reconciliation
pip install -r requirements.txt
```

2. **Configure environment variables**:
Create a `.env` file with the following:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/expense_reconciliation

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_BASE_URL=your_base_url
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_MODEL=your_model_name

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com

# File Processing Directories
UPLOAD_DIR=data/uploads
PROCESSED_DIR=data/processed
REPORTS_DIR=data/reports

# Matching Algorithm Settings
AMOUNT_TOLERANCE=0.01
DATE_TOLERANCE_DAYS=3
FUZZY_MATCH_THRESHOLD=80
```

3. **Initialize database**:
```bash
python -c "from database import init_database; init_database()"
```

## 🔧 Usage

### Option 1: Direct Orchestrator Usage

```python
from expense_reconciliation_orchestrator import ExpenseReconciliationOrchestrator

# Initialize orchestrator
orchestrator = ExpenseReconciliationOrchestrator()

# Sample participant data
participants = [
    {
        "participant_id": "EMP001",
        "name": "Alice Johnson", 
        "email": "alice@company.com",
        "department": "Marketing"
    },
    # ... more participants
]

# Run complete workflow
result = orchestrator.run_full_reconciliation_workflow(
    citibank_file="data/citibank_transactions.xlsx",
    concur_file="data/concur_transactions.xlsx", 
    cvent_documents=["data/receipt1.pdf", "data/receipt2.jpg"],
    participants_data=participants
)

print(f"Workflow completed: {result['status']}")
```

### Option 2: REST API

Start the API server:
```bash
python api.py
# or
uvicorn api:app --host 0.0.0.0 --port 8000
```

Upload files and start reconciliation:
```bash
curl -X POST "http://localhost:8000/reconcile" \
  -F "citibank_file=@citibank_transactions.xlsx" \
  -F "concur_file=@concur_transactions.xlsx" \
  -F "cvent_documents=@receipt1.pdf" \
  -F "cvent_documents=@receipt2.jpg" \
  -F 'participants=[{"participant_id":"EMP001","name":"Alice","email":"alice@company.com"}]'
```

Check workflow status:
```bash
curl "http://localhost:8000/status/workflow_20241201_143022"
```

## 🧪 LLM Matching Demonstration

### Test the LLM Matching Engine
Run the interactive demonstration to see how the LLM-based matching works:

```bash
python examples/llm_matching_demo.py
```

This demo showcases:
- **Real-world vendor matching**: See how the LLM handles vendor name variations like "McDonald's" vs "MCD NYC BROADWAY"
- **Contextual understanding**: Analysis of descriptions and business context
- **Confidence scoring**: Detailed reasoning behind each match decision
- **Cross-system analysis**: How matches between Citibank and Concur are evaluated
- **Complex scenarios**: Examples with amount discrepancies, date variations, and vendor abbreviations

### Sample Demo Output
```
🤖 LLM-Based Expense Matching Demo
==================================================
✅ LLM Matching Engine initialized successfully

📊 Sample Data:
   - 3 extracted expenses from Cvent documents
   - 3 Citibank transactions
   - 3 Concur transactions

🔍 Running LLM-based expense matching...
✅ Matching completed! Found 3 expense matches

🎯 Match #1: Marriott Downtown NYC - $285.50
   Overall Confidence: 95%
   🏦 Citibank Match: 98% confidence
      Vendor: Marriott Hotels
      Amount: $285.50
      Reasoning: Exact amount match and vendor name "Marriott Hotels" closely matches...
   📊 Concur Match: 96% confidence
      Vendor: Marriott International
      Amount: $285.50
      Reasoning: Perfect amount and date match with vendor variations...
```

## 📊 Expected File Formats

### Citibank Transactions Excel
Required columns:
- `Transaction ID`: Unique transaction identifier
- `Event ID`: Event identifier for grouping
- `Amount`: Transaction amount
- `Currency`: Currency code (e.g., USD)
- `Date`: Transaction date
- `Description`: Transaction description
- `Vendor`: Merchant/vendor name
- `Card Number`: Card number (optional)

### Concur Transactions Excel
Required columns:
- `Transaction ID`: Unique transaction identifier
- `Event ID`: Event identifier for grouping
- `Amount`: Transaction amount
- `Currency`: Currency code
- `Date`: Transaction date
- `Expense Type`: Category of expense
- `Vendor`: Merchant/vendor name
- `Description`: Transaction description
- `Participant ID`: Employee/participant identifier

### Cvent Documents
Supported formats:
- **PDF files**: Receipts, invoices, expense documents
- **Image files**: JPG, PNG, TIFF receipts and invoices

The multimodal LLM will extract:
- Amount and currency
- Date of expense
- Vendor/merchant name
- Expense type/category
- Description

## 🔍 LLM-Powered Matching Algorithm

The system uses an intelligent LLM-based matching engine that provides contextual understanding and detailed reasoning:

### 🤖 LLM-Based Matching Features
- **Contextual Analysis**: Understanding of vendor variations, abbreviations, and formats
- **Intelligent Reasoning**: Detailed explanations for each matching decision  
- **Multi-Criteria Evaluation**: Comprehensive analysis of amount, date, vendor, currency, and description
- **Confidence Scoring**: AI-generated confidence scores with supporting evidence
- **Cross-System Consistency**: Analysis of matches across Citibank and Concur systems
- **Fallback Protection**: Rule-based backup when LLM is unavailable

### Matching Process
1. **Individual System Matching**: LLM analyzes expenses against Citibank and Concur transactions separately
2. **Criteria Evaluation**: AI considers amount tolerance, date proximity, vendor similarity, currency matching, and description context
3. **Overall Analysis**: LLM evaluates consistency between systems and provides overall confidence
4. **Detailed Reasoning**: Each match includes AI-generated explanations and concerns

### Confidence Levels
- **High (≥0.8)**: Strong AI confidence with consistent cross-system matches
- **Medium (0.6-0.8)**: Moderate confidence, may require review
- **Low (<0.6)**: Weak confidence, likely false matches

### Advanced Capabilities
- **Vendor Name Intelligence**: Handles variations like "McDonald's" vs "MCD NYC BROADWAY"
- **Contextual Description Matching**: Understands business context and expense purposes
- **Amount Tolerance**: Smart handling of small discrepancies and currency conversions
- **Date Proximity**: Intelligent date matching considering weekends and processing delays

## 📈 Monitoring & Logging

### Database Logging
All operations are logged to `processing_logs` table:
- Process type and status
- Start/completion times
- Error details
- Event association

### Workflow Tracking
- Real-time status updates
- Step-by-step progress
- Error recovery points
- Performance metrics

### API Endpoints for Monitoring
- `GET /status/{workflow_id}`: Workflow status
- `GET /events`: All events and their status
- `GET /reports/{event_id}`: Generated reports
- `GET /health`: System health check

## 🎨 Customization

### Customizing LLM Matching Prompts
Modify the LLM prompts in `ExpenseMatchingEngine` to add custom criteria:

```python
def _create_matching_prompt(self, expense: Dict, transactions: List[Dict], system_name: str) -> str:
    prompt = f"""
    EXPENSE TO MATCH:
    {self._format_expense_data(expense)}
    
    CUSTOM CRITERIA:
    - Consider project codes and cost centers
    - Account for regional vendor variations
    - Apply company-specific matching rules
    
    TRANSACTIONS TO COMPARE:
    {self._format_transactions(transactions)}
    """
    return prompt
```

### Testing LLM Matching
Run the demonstration script to test matching capabilities:

```bash
python examples/llm_matching_demo.py
```

### Custom Splitting Methods
Extend `ExpenseSpittingAgent` to add new splitting logic:

```python
def _custom_split(self, expenses: List[Dict], participants: List, total_amount: float, custom_params: Dict) -> Dict:
    # Implement custom splitting logic
    return split_result
```

### New Document Types
Add support for additional document formats in `DocumentProcessor`:

```python
def _extract_from_new_format(self, file_path: str, event_id: str) -> List[Dict]:
    # Implement extraction for new format
    return extracted_expenses
```

## 🔧 Configuration

### Matching Thresholds
Adjust in `config.py`:
- `AMOUNT_TOLERANCE`: Amount matching tolerance (default: 1%)
- `DATE_TOLERANCE_DAYS`: Date matching window (default: 3 days)
- `FUZZY_MATCH_THRESHOLD`: Text similarity threshold (default: 80%)

### Email Templates
Customize email content in `NotificationAgent`:
- Subject line format
- Email body template
- Attachment handling

### Database Schema
The system uses comprehensive database models:
- `events`: Event information
- `citibank_transactions`: Citibank transaction data
- `concur_transactions`: Concur transaction data
- `expense_documents`: Cvent document metadata
- `extracted_expenses`: LLM-extracted expense data
- `expense_matches`: Matching results with confidence
- `participants`: Participant information
- `expense_reports`: Generated reports
- `processing_logs`: System logs

## 🚨 Error Handling

The system includes robust error handling:

### Workflow Level
- Graceful failure recovery
- Partial success handling
- Comprehensive error logging
- Status tracking

### Agent Level
- Individual agent error isolation
- Retry mechanisms
- Fallback procedures
- Detailed error reporting

### Data Level
- Input validation
- Data type checking
- Missing field handling
- Corruption detection

## 🔒 Security Considerations

- **API Authentication**: Implement authentication for production
- **Data Encryption**: Encrypt sensitive financial data
- **Audit Logging**: Complete audit trail
- **Access Control**: Role-based access to reports
- **Email Security**: Secure email transmission

## 🚀 Production Deployment

### Recommended Architecture
- **Application**: Deploy with Docker/Kubernetes
- **Database**: PostgreSQL with replication
- **File Storage**: Cloud storage (AWS S3, Azure Blob)
- **Email**: Enterprise email service
- **Monitoring**: Application monitoring and alerting

### Performance Optimization
- **Database Indexing**: Index on Event ID, dates, amounts
- **Caching**: Cache frequent queries
- **Async Processing**: Background task queues
- **Parallel Processing**: Multi-agent parallel execution

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the workflow logs for debugging

## 🏆 Acknowledgments

- AutoGen framework for multi-agent orchestration
- OpenAI for multimodal LLM capabilities
- FastAPI for web framework
- SQLAlchemy for database ORM
- The broader open-source community

---

Built with ❤️ using AutoGen and modern AI technologies. 