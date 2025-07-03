# Expense Reconciliation System - Complete Overview

## 🎯 System Architecture

### High-Level Flow
```
📧 Email Trigger → 📥 Data Ingestion → 🔍 Event Matching → 📄 Document Processing → 
🎯 Expense Matching → 💰 Expense Splitting → 📊 Report Generation → 📧 Notifications
```

## 🤖 Agentic Components

### 1. **Data Ingestion Agent** (`agents/data_ingestion_agent.py`)
- **Purpose**: Process Citibank and Concur Excel files
- **Functions**: 
  - `process_excel_files()`: Parse and store transaction data
- **Output**: Transactions stored in PostgreSQL with Event IDs

### 2. **Event Matching Agent** (`agents/event_matching_agent.py`)
- **Purpose**: Group transactions by Event ID and find matches
- **Functions**:
  - `find_matching_events()`: Identify events in both systems
  - `analyze_event_coverage()`: Check transaction coverage
- **Output**: List of matching Event IDs for processing

### 3. **Document Processing Agent** (`agents/document_processing_agent.py`)
- **Purpose**: Extract expenses from Cvent documents using multimodal LLM
- **Functions**:
  - `process_cvent_documents()`: Extract structured data from PDFs/images
  - `filter_expenses_by_event()`: Group expenses by Event ID
- **AI Integration**: Azure OpenAI multimodal model for document analysis

### 4. **Expense Matching Agent** (`agents/expense_matching_agent.py`)
- **Purpose**: Match extracted expenses with transaction records
- **Functions**:
  - `match_expenses_for_event()`: Sophisticated multi-criteria matching
- **Algorithm**: 40% amount, 30% date, 20% vendor, 10% currency matching

### 5. **Expense Splitting Agent** (`agents/expense_splitting_agent.py`)
- **Purpose**: Split expenses among participants
- **Functions**:
  - `split_expenses_for_event()`: Equal or weighted splitting
- **Methods**: Equal distribution, weighted by participant, custom rules

### 6. **Report Generation Agent** (`agents/report_generation_agent.py`)
- **Purpose**: Create individual expense reports
- **Functions**:
  - `generate_expense_reports()`: Individual participant reports
  - `export_reports_to_excel()`: Excel export with multiple sheets
- **Output**: Comprehensive reports with breakdowns

### 7. **Notification Agent** (`agents/notification_agent.py`)
- **Purpose**: Send email notifications to participants
- **Functions**:
  - `send_expense_notifications()`: Automated email with attachments
  - `send_custom_notification()`: Custom messaging
- **Features**: SMTP integration, Excel attachments, status tracking

## 🏗️ Core Infrastructure

### Database Layer (`database/`)
**Models** (`database/models.py`):
- `Event`: Event information and status
- `CitibankTransaction`: Citibank transaction data
- `ConcurTransaction`: Concur transaction data
- `ExpenseDocument`: Cvent document metadata
- `ExtractedExpense`: LLM-extracted expense data
- `ExpenseMatch`: Matching results with confidence scores
- `Participant`: Participant information
- `EventParticipant`: Event-participant relationships
- `ExpenseReport`: Generated individual reports
- `ProcessingLog`: Comprehensive system logging

### Utility Layer (`utils/`)
**Document Processor** (`utils/document_processor.py`):
- Excel file parsing for Citibank/Concur
- Multimodal LLM integration for document extraction
- PDF and image processing capabilities
- Structured data extraction with confidence scores

**Matching Engine** (`utils/matching_engine.py`):
- Multi-criteria matching algorithm
- Fuzzy string matching for vendor names
- Confidence scoring system
- Amount and date tolerance handling

### Configuration (`config.py`)
- Azure OpenAI settings
- Database configuration
- Email SMTP settings
- Matching algorithm parameters
- File processing directories

## 🔄 Complete Workflow

### Phase 1: Data Ingestion
1. **Email Trigger**: System receives Excel files
2. **File Processing**: Parse Citibank and Concur Excel files
3. **Database Storage**: Store transactions with Event IDs
4. **Validation**: Verify data integrity and completeness

### Phase 2: Event Analysis
1. **Event Grouping**: Group transactions by Event ID
2. **Coverage Analysis**: Check which events have both Citibank and Concur data
3. **Match Identification**: Find events ready for reconciliation
4. **Database Updates**: Mark events as "matched" status

### Phase 3: Document Processing
1. **Document Upload**: Receive Cvent expense documents
2. **Multimodal Extraction**: Use LLM to extract structured expense data
3. **Event Association**: Link expenses to specific Event IDs
4. **Confidence Scoring**: Rate extraction quality

### Phase 4: Intelligent Matching
1. **Multi-Criteria Analysis**: Match expenses with transactions using:
   - Amount tolerance (40% weight)
   - Date proximity (30% weight)
   - Vendor similarity (20% weight)
   - Currency matching (10% weight)
2. **Confidence Classification**:
   - High (≥0.8): Auto-confirmed
   - Medium (0.6-0.8): Manual review
   - Low (<0.6): Auto-rejected
3. **Match Storage**: Store results with detailed criteria

### Phase 5: Expense Splitting
1. **Participant Identification**: Get event participants from metadata
2. **Splitting Algorithm**: Equal distribution among participants
3. **Individual Calculations**: Calculate per-person expense shares
4. **Breakdown Generation**: Create detailed expense categorization

### Phase 6: Report Generation
1. **Individual Reports**: Generate personal expense summaries
2. **Excel Export**: Multi-sheet Excel files with:
   - Summary sheet (participant info, totals)
   - Detailed expenses (itemized breakdown)
   - Category summary (by expense type)
3. **Database Storage**: Store report metadata and status

### Phase 7: Notification System
1. **Email Composition**: Create personalized emails with:
   - Event details and summary
   - Individual expense totals
   - Submission instructions
2. **Attachment Handling**: Include Excel reports
3. **Delivery Tracking**: Monitor email delivery status
4. **Status Updates**: Update report status to "sent"

## 🌐 API Interface (`api.py`)

### REST Endpoints
- `POST /reconcile`: Start complete workflow
- `GET /status/{workflow_id}`: Check workflow progress
- `GET /reports/{event_id}`: Retrieve generated reports
- `GET /events`: List all events and status
- `GET /health`: System health check

### Features
- **File Upload**: Multi-file upload support
- **Background Processing**: Async workflow execution
- **Status Tracking**: Real-time progress monitoring
- **Error Handling**: Comprehensive error responses

## 🎮 Orchestration (`expense_reconciliation_orchestrator.py`)

### Main Orchestrator Class
**`ExpenseReconciliationOrchestrator`**:
- **Agent Coordination**: Manages all 7 specialized agents
- **Workflow Management**: Sequential step execution with error handling
- **Status Tracking**: Comprehensive logging and monitoring
- **Error Recovery**: Graceful failure handling and rollback

### Key Features
- **Parallel Processing**: Agents can work concurrently where possible
- **Error Isolation**: Individual agent failures don't crash entire workflow
- **Comprehensive Logging**: Every step logged to database
- **Flexible Configuration**: Customizable parameters and thresholds

## 📊 Key Innovations

### 1. **Multimodal LLM Integration**
- Direct PDF and image processing
- Structured data extraction from unstructured documents
- Confidence scoring for extraction quality
- No manual data entry required

### 2. **Intelligent Matching Algorithm**
- Multi-criteria weighted scoring
- Fuzzy string matching for vendor names
- Date and amount tolerance handling
- Machine learning-based confidence scoring

### 3. **Agentic Design Patterns**
- **Specialist Agents**: Each agent has single responsibility
- **Orchestrator Pattern**: Central coordination with distributed execution
- **Observer Pattern**: Comprehensive monitoring and logging
- **Pipeline Pattern**: Sequential processing with error recovery

### 4. **Comprehensive Audit Trail**
- Every operation logged with timestamps
- Match criteria stored for transparency
- Error details captured for debugging
- Complete workflow history maintained

## 🚀 Deployment Architecture

### Recommended Production Setup
```
Internet → Load Balancer → API Gateway → FastAPI Application
                                      ↓
                                 Orchestrator
                                      ↓
                     [7 Specialized AutoGen Agents]
                                      ↓
                                PostgreSQL DB
                                      ↓
                              File Storage (S3/Azure)
                                      ↓
                              Email Service (SMTP)
```

### Scalability Features
- **Horizontal Scaling**: Multiple orchestrator instances
- **Database Optimization**: Indexed queries and connection pooling
- **File Processing**: Cloud storage integration
- **Background Tasks**: Async task queues
- **Monitoring**: Application performance monitoring

## 🔧 Configuration Management

### Environment Variables Required
```env
# Database
DATABASE_URL=postgresql://...

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_BASE_URL=...
AZURE_OPENAI_MODEL=...

# Email
SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=...
EMAIL_PASSWORD=...

# Processing
UPLOAD_DIR=data/uploads
REPORTS_DIR=data/reports

# Algorithm Tuning
AMOUNT_TOLERANCE=0.01
DATE_TOLERANCE_DAYS=3
FUZZY_MATCH_THRESHOLD=80
```

## 📈 Performance Metrics

### Expected Processing Times
- **Data Ingestion**: ~30 seconds per 1000 transactions
- **Document Processing**: ~10 seconds per document (using multimodal LLM)
- **Expense Matching**: ~5 seconds per 100 expense items
- **Report Generation**: ~2 seconds per participant
- **Email Notifications**: ~1 second per email

### Scalability Targets
- **Concurrent Workflows**: 10+ simultaneous reconciliations
- **Transaction Volume**: 10,000+ transactions per workflow
- **Document Processing**: 100+ documents per event
- **Participants**: 500+ participants per event

This system represents a comprehensive, production-ready solution for automated expense reconciliation using cutting-edge agentic AI design patterns with AutoGen framework. 