# Product Context

## Why This Project Exists

ClariFin_OS was created to solve a common personal finance management problem: the difficulty of extracting meaningful insights from bank statements that are often provided in PDF format with inconsistent layouts and formats. Traditional methods require manual data entry or expensive software solutions.

ClariFin_OS is a Personal Financial Operating System.

Core Promise:
- Mathematically consistent
- Ledger verified
- Cross-account reconciliation capable
- No silent auto-balancing
- Any mismatch triggers explicit user confirmation

## Problems It Solves

1. **Manual Data Entry**: Eliminates the need to manually copy transaction data from PDF statements into spreadsheets or financial software
2. **Multi-Bank Support**: Handles statements from multiple Indian banks (HDFC, ICICI, SBI, Axis, IDFC, IndusInd) with different formats
3. **Time-Consuming Analysis**: Automates the extraction and categorization of transactions for quick financial insights
4. **Data Silos**: Provides a unified view of credit card transactions across different banks in one application
5. **Expense Tracking**: Automatically categorizes transactions to help users understand their spending patterns

## How It Should Work

### Core User Flow
1. **Upload**: User uploads PDF bank statements via drag-and-drop interface
2. **Parse**: System automatically detects bank format and extracts transactions and metadata
3. **Categorize**: Transactions are automatically categorized based on merchant keywords
4. **Visualize**: Data is presented through interactive dashboards with spending insights
5. **Manage**: Users can filter, search, and export transaction data

### Key Features
- **Multi-PDF Upload**: Support for uploading multiple statements at once
- **Real-time Processing**: Sequential parsing with progress indicators
- **Smart Categorization**: 10+ predefined categories with keyword-based classification
- **Dashboard Analytics**: Spending overview, category breakdown, and card management
- **Data Export**: CSV export functionality for external analysis
- **REST API**: FastAPI backend for data persistence and querying

## User Experience Goals

### Primary Users
- **Personal Finance Enthusiasts**: Individuals who track their spending and want detailed insights
- **Small Business Owners**: Those who need to separate personal and business expenses
- **Budget-Conscious Users**: People looking to understand and control their spending habits

### User Experience Principles
1. **Zero Learning Curve**: Intuitive interface that requires no training
2. **Instant Gratification**: Quick parsing and immediate visualization of results
3. **Mobile-Friendly**: Responsive design that works on all devices
4. **Privacy-First**: Local deployment, user controls their data

### Success Metrics
- **Parse Accuracy**: 100% accuracy in extracting transaction data from supported bank formats
- **Processing Speed**: Under 30 seconds for typical statement PDFs
- **User Retention**: Ongoing expense tracking with meaningful insights

## Technical Requirements

### Architecture
- **Frontend**: Next.js 16 with React 19
- **Backend**: FastAPI with SQLite database
- **Single Source of Truth**: Backend is authoritative for all financial data

### Performance Goals
- **Efficient Processing**: Handle large PDF files without memory issues
- **Browser Compatibility**: Support for modern browsers

### Security & Privacy
- **Local Deployment**: User controls their own data
- **SQLite Database**: Data stored locally, not in cloud

## Business Context

### Market Position
- **Competitive Advantage**: 100% parsing accuracy for Indian bank statements
- **Niche Focus**: Specialized for Indian banking formats and currency
- **Cost-Effective**: Free, open-source alternative to expensive personal finance software
- **Privacy-Focused**: Self-hosted, no data monetization

### Future Vision
- **Phase 1**: Budget setting and tracking features
- **Phase 2**: Due date reminders and payment tracking
- **Phase 3**: AI-powered insights and spending predictions
