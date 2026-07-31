# Graph Runtime Audit

## Node Types

### Implemented Node Types
The graph runtime currently supports the following node types for code analysis:

| Node Type       | Description                                      | Example Use Case                          |
|-----------------|--------------------------------------------------|--------------------------------------------|
| **Parameter**   | Function or method parameters                    | `def compute_wellness_score(cashflow_stability: Decimal)` |
| **Interface**   | TypeScript interfaces                            | `interface BehaviorScore { score: number }` |
| **Module**      | Python/TypeScript modules                        | `behaviour_engine.wellness`                |
| **Variable**    | Variables in code                                | `wellness_score = 85`                      |
| **Function**    | Functions and methods                            | `def compute_wellness_score():`            |
| **File**        | Source code files                                | `/backend/src/engines/behaviour_engine/wellness.py` |
| **Directory**   | Source code directories                          | `/backend/src/engines/behaviour_engine`    |
| **Class**       | Classes in code                                  | `class Money:`                             |
| **ExternalClass** | External classes (dependencies)               | `Decimal` from `decimal` module            |
| **Repository**  | Code repositories                                | `ClariFin_OS`                              |

### Missing Node Types
The following financial data node types are **not implemented**:

| Node Type          | Description                                      | Potential Use Case                        |
|--------------------|--------------------------------------------------|--------------------------------------------|
| **Account**        | Financial accounts                               | Savings account, current account           |
| **Transaction**    | Financial transactions                           | Debit/credit transactions                 |
| **Statement**      | Bank statements                                  | Monthly credit card statements             |
| **Loan**           | Loan accounts                                    | Personal loan, home loan                  |
| **Investment**     | Investment accounts                              | Mutual funds, stocks, bonds               |
| **CreditCard**     | Credit card accounts                             | Visa, Mastercard, Amex cards              |
| **Category**       | Transaction categories                           | Food, Transportation, Entertainment       |
| **Merchant**       | Merchants/vendors                                | Amazon, Swiggy, Uber                      |
| **Pattern**        | Spending/income patterns                         | Subscription pattern, impulse spending    |
| **Metric**         | Financial metrics                                | Net worth, savings rate, utilization      |
| **Insight**        | Financial insights                               | "High credit utilization detected"        |
| **Alert**          | Financial alerts                                 | "Low emergency buffer"                    |
| **Temporal**       | Time-based nodes                                 | Monthly snapshots, daily balances         |

---

## Edge Types

### Implemented Edge Types
The graph runtime currently supports the following relationship types for code analysis:

| Edge Type         | Description                                      | Example Use Case                          |
|-------------------|--------------------------------------------------|--------------------------------------------|
| **HAS_PARAMETER** | Function has parameter                           | `compute_wellness_score` HAS_PARAMETER `cashflow_stability` |
| **CONTAINS**      | Directory contains file, file contains function  | `behaviour_engine` CONTAINS `wellness.py`  |
| **IMPORTS**       | Module imports another module                    | `behaviour_engine` IMPORTS `money`         |
| **CALLS**         | Function calls another function                  | `get_behaviour_summary` CALLS `compute_wellness_score` |
| **INHERITS**      | Class inherits from another class                | `class SavingsAccount` INHERITS `Account`  |

### Missing Edge Types
The following financial data relationship types are **not implemented**:

| Edge Type             | Description                                      | Potential Use Case                        |
|-----------------------|--------------------------------------------------|--------------------------------------------|
| **HAS_TRANSACTION**   | Account has transaction                          | `Account` HAS_TRANSACTION `Transaction`    |
| **IN_CATEGORY**       | Transaction in category                          | `Transaction` IN_CATEGORY `Food`           |
| **WITH_MERCHANT**     | Transaction with merchant                        | `Transaction` WITH_MERCHANT `Amazon`       |
| **HAS_BALANCE**       | Account has balance                              | `Account` HAS_BALANCE `100000` (paise)     |
| **HAS_STATEMENT**     | Credit card has statement                        | `CreditCard` HAS_STATEMENT `Statement`     |
| **HAS_LOAN**          | User has loan                                    | `User` HAS_LOAN `Loan`                    |
| **HAS_INVESTMENT**    | User has investment                              | `User` HAS_INVESTMENT `Investment`        |
| **EXHIBITS_PATTERN**  | User exhibits spending pattern                   | `User` EXHIBITS_PATTERN `Subscription`     |
| **HAS_METRIC**        | User has financial metric                        | `User` HAS_METRIC `NetWorth`              |
| **HAS_INSIGHT**       | User has financial insight                       | `User` HAS_INSIGHT `HighUtilization`       |
| **HAS_ALERT**         | User has financial alert                         | `User` HAS_ALERT `LowEmergencyBuffer`     |
| **PRECEDES**          | Temporal precedence                              | `Transaction` PRECEDES `Transaction`       |
| **PART_OF**           | Part-of relationships                            | `Transaction` PART_OF `Statement`          |
| **RELATED_TO**        | Generic relationships                            | `Insight` RELATED_TO `Metric`             |

---

## Traversal Capabilities

### Implemented Traversal Capabilities
The graph runtime supports the following traversal capabilities for code analysis:

| Traversal Type          | Description                                      | Example Query                              |
|-------------------------|--------------------------------------------------|--------------------------------------------|
| **Code Structure**      | Traverse file/directory hierarchy                | `MATCH (d:Directory)-[:CONTAINS]->(f:File)` |
| **Import Analysis**     | Traverse module import dependencies              | `MATCH (m1:Module)-[:IMPORTS]->(m2:Module)` |
| **Call Graph**          | Traverse function call hierarchy                 | `MATCH (f1:Function)-[:CALLS]->(f2:Function)` |
| **Inheritance**         | Traverse class inheritance hierarchy             | `MATCH (c1:Class)-[:INHERITS]->(c2:Class)`  |
| **Parameter Analysis**  | Traverse function parameters                     | `MATCH (f:Function)-[:HAS_PARAMETER]->(p:Parameter)` |

### Missing Traversal Capabilities
The following financial data traversal capabilities are **not implemented**:

| Traversal Type          | Description                                      | Potential Use Case                        |
|-------------------------|--------------------------------------------------|--------------------------------------------|
| **Account Transactions** | Traverse transactions for an account            | Find all transactions for a savings account |
| **Category Spending**   | Traverse spending by category                    | Analyze food spending over time           |
| **Merchant Analysis**   | Traverse spending by merchant                    | Identify top merchants by spending        |
| **Temporal Analysis**   | Traverse financial data over time                | Analyze monthly net worth trends          |
| **Pattern Detection**   | Traverse spending/income patterns                | Detect subscription patterns              |
| **Metric Calculation**  | Traverse financial metrics                       | Calculate net worth from assets/liabilities |
| **Insight Generation**  | Traverse insights for a user                     | Find all high-severity insights           |
| **Alert Management**    | Traverse alerts for a user                       | Find all unacknowledged alerts            |
| **Statement Analysis**  | Traverse transactions within a statement         | Reconcile statement transactions          |
| **Loan Amortization**   | Traverse loan payment schedule                   | Analyze interest vs principal payments    |
| **Cash Flow**           | Traverse income/expense flows                    | Analyze monthly cash flow trends          |

---

## Selection Capabilities

### Implemented Selection Capabilities
The graph runtime supports basic selection through Cypher queries:

| Selection Type         | Description                                      | Example Query                              |
|------------------------|--------------------------------------------------|--------------------------------------------|
| **Node Selection**     | Select nodes by type and properties              | `MATCH (f:Function {name: 'compute_wellness_score'})` |
| **Relationship Selection** | Select relationships by type                | `MATCH ()-[r:CALLS]->() RETURN r`          |
| **Property Filtering** | Filter by node/relationship properties           | `MATCH (f:Function) WHERE f.name CONTAINS 'score'` |
| **Path Selection**     | Select paths through the graph                   | `MATCH path = (f1:Function)-[:CALLS*]->(f2:Function)` |

### Missing Selection Capabilities
The following financial data selection capabilities are **not implemented**:

| Selection Type         | Description                                      | Potential Use Case                        |
|------------------------|--------------------------------------------------|--------------------------------------------|
| **Date Range**         | Select financial data within date ranges         | Transactions between Jan 1 and Jan 31      |
| **Amount Range**       | Select transactions by amount range              | Transactions over ₹10,000                 |
| **Category Filter**    | Select transactions by category                  | All food transactions                     |
| **Merchant Filter**    | Select transactions by merchant                  | All Amazon transactions                   |
| **Account Filter**     | Select data by account                           | All transactions for HDFC account         |
| **Metric Threshold**   | Select based on metric thresholds                | Accounts with utilization > 80%           |
| **Pattern Type**       | Select by spending pattern type                  | All subscription patterns                 |
| **Insight Severity**   | Select insights by severity                      | All high-severity insights                |
| **Alert Status**       | Select alerts by status                          | All unacknowledged alerts                 |
| **Temporal Granularity** | Select by time granularity (daily, monthly)    | Monthly net worth snapshots               |
| **Financial Entity**   | Select by financial entity type                  | All credit cards                          |

---

## Metrics Capabilities

### Implemented Metrics
The graph runtime supports code analysis metrics:

| Metric Type            | Description                                      | Example Use Case                          |
|------------------------|--------------------------------------------------|--------------------------------------------|
| **Call Graph Metrics** | Function call relationships                      | Identify most-called functions            |
| **Import Metrics**     | Module import dependencies                       | Identify circular dependencies            |
| **Inheritance Depth**  | Class inheritance hierarchy depth                | Identify deep inheritance chains          |
| **Parameter Count**    | Number of parameters per function                | Identify complex functions                |
| **Code Structure**     | File/directory organization                      | Analyze repository structure              |

### Missing Metrics
The following financial metrics are **not implemented** in the graph runtime:

| Metric Type            | Description                                      | Potential Use Case                        |
|------------------------|--------------------------------------------------|--------------------------------------------|
| **Net Worth**          | Total assets minus total liabilities             | Track overall financial health            |
| **Savings Rate**       | Percentage of income saved                       | Monitor savings behavior                  |
| **Cash Flow**          | Income minus expenses                            | Track monthly cash flow                   |
| **Utilization**        | Credit utilization percentage                    | Monitor credit card usage                 |
| **Debt-to-Income**     | Debt payments to income ratio                    | Assess debt burden                        |
| **FOIR**               | Fixed Obligation to Income Ratio                 | Assess loan eligibility                   |
| **Liquidity**          | Emergency fund coverage in months                | Assess financial resilience               |
| **Spending Patterns**  | Category-based spending distribution             | Identify spending habits                  |
| **Income Stability**   | Income source stability                          | Assess income diversification             |
| **Wellness Score**     | Composite financial wellness score               | Track overall financial health            |
| **Resilience Index**   | Ability to weather financial shocks              | Assess financial safety net               |
| **Interest Costs**     | Total interest paid on loans                     | Analyze loan costs                        |
| **Returns**            | Investment returns                               | Track investment performance              |
| **Match Rate**         | Reconciliation match rate                        | Assess reconciliation accuracy            |

---

## Explainability

### Implemented Explainability
The graph runtime provides structural explainability for code:

| Explainability Feature | Description                                      | Example Use Case                          |
|------------------------|--------------------------------------------------|--------------------------------------------|
| **Code Structure**     | Visualize file/directory relationships           | Understand repository organization        |
| **Call Graph**         | Visualize function call relationships            | Trace function dependencies               |
| **Import Graph**       | Visualize module import relationships            | Understand module dependencies            |
| **Inheritance Graph**  | Visualize class inheritance                      | Understand class hierarchy                |

### Missing Explainability
The following financial explainability features are **not implemented**:

| Explainability Feature | Description                                      | Potential Use Case                        |
|------------------------|--------------------------------------------------|--------------------------------------------|
| **Evidence Chains**    | Step-by-step calculation evidence                | Explain how net worth is calculated        |
| **Data Provenance**    | Source of financial data                         | Show which transactions contribute to net worth |
| **Confidence Scores**  | Confidence in financial metrics                  | Show confidence in savings rate calculation |
| **Calculation Steps**  | Detailed calculation breakdown                   | Show how wellness score is calculated     |
| **Source References**  | References to underlying data sources            | Show which accounts contribute to net worth |
| **Metric Composition** | Component breakdown of composite metrics         | Show wellness score component breakdown    |
| **Temporal Changes**   | Changes in financial metrics over time           | Show how net worth changed month-over-month |
| **Anomaly Detection**  | Explanation of detected anomalies                | Explain why a transaction is flagged      |
| **Pattern Explanation** | Explanation of detected patterns                | Explain subscription pattern detection    |
| **Insight Justification** | Justification for insights                     | Explain why high utilization is a concern |

---

## Adapters

### Implemented Adapters
The graph runtime has adapters for code analysis:

| Adapter Type           | Description                                      | Supported Languages                      |
|------------------------|--------------------------------------------------|--------------------------------------------|
| **Code Analysis**      | Code structure and relationships                 | Python, TypeScript                        |
| **Repository Analysis** | Repository structure                             | Git repositories                          |

### Missing Adapters
The following financial data adapters are **not implemented**:

| Adapter Type           | Description                                      | Potential Data Sources                   |
|------------------------|--------------------------------------------------|--------------------------------------------|
| **Account Data**       | Financial account data                           | Bank accounts, investment accounts        |
| **Transaction Data**   | Financial transaction data                       | Bank transactions, credit card transactions |
| **Statement Data**     | Bank statement data                              | PDF statements, CSV statements            |
| **Loan Data**          | Loan account data                                | Personal loans, home loans                |
| **Investment Data**    | Investment portfolio data                        | Mutual funds, stocks, bonds               |
| **Credit Card Data**   | Credit card account data                         | Visa, Mastercard, Amex statements         |
| **Metric Data**        | Financial metric data                            | Net worth, savings rate, utilization      |
| **Insight Data**       | Financial insight data                           | Behavioral insights, recommendations      |
| **Alert Data**         | Financial alert data                             | High utilization, low savings             |
| **Temporal Data**      | Time-series financial data                       | Monthly snapshots, daily balances         |

---

## Registry

### Implemented Registry
The graph runtime has a basic repository registry:

| Registry Feature       | Description                                      | Example Use Case                          |
|------------------------|--------------------------------------------------|--------------------------------------------|
| **Repository Registry** | Index of indexed repositories                    | List all indexed repositories             |

### Missing Registry
The following registry capabilities are **not implemented**:

| Registry Feature       | Description                                      | Potential Use Case                        |
|------------------------|--------------------------------------------------|--------------------------------------------|
| **Node Type Registry** | Registry of available node types                 | List all financial node types             |
| **Edge Type Registry** | Registry of available edge types                 | List all financial relationship types     |
| **Metric Registry**    | Registry of available financial metrics          | List all available metrics                |
| **Visualization Registry** | Registry of available visualizations        | List all chart types                      |
| **Adapter Registry**   | Registry of available data adapters              | List all data source adapters             |
| **Schema Registry**    | Registry of financial data schemas               | List all DTO schemas                      |
| **Query Registry**     | Registry of common Cypher queries                | List common financial queries             |
| **Pattern Registry**   | Registry of spending/income patterns             | List all detectable patterns              |

---

## Runtime API

### Implemented API
The CodeGraphContext provides the following runtime API:

| API Method                     | Description                                      | Example Use Case                          |
|--------------------------------|--------------------------------------------------|--------------------------------------------|
| `find_code`                    | Search for code by name or content               | Find `compute_wellness_score` function    |
| `analyze_code_relationships`   | Analyze code relationships                       | Find callers of `compute_wellness_score`  |
| `execute_cypher_query`         | Execute custom Cypher queries                    | Custom graph traversal                    |
| `list_indexed_repositories`    | List indexed repositories                        | List all indexed code repositories        |

### Missing API
The following financial graph API capabilities are **not implemented**:

| API Method                     | Description                                      | Potential Use Case                        |
|--------------------------------|--------------------------------------------------|--------------------------------------------|
| `find_financial_data`          | Search for financial data                        | Find all credit card transactions         |
| `analyze_financial_relationships` | Analyze financial relationships              | Find all transactions for an account      |
| `traverse_temporal_data`       | Traverse time-series financial data              | Analyze monthly net worth trends          |
| `calculate_metric`             | Calculate financial metrics                      | Calculate net worth                       |
| `generate_insight`             | Generate financial insights                      | Generate high utilization insight         |
| `create_alert`                 | Create financial alerts                          | Create low emergency buffer alert         |
| `reconcile_transactions`       | Reconcile transactions                           | Match transactions to statements          |
| `detect_patterns`              | Detect spending/income patterns                  | Detect subscription patterns              |
| `simulate_scenario`            | Simulate financial scenarios                     | Simulate loan prepayment impact           |
| `get_evidence_chain`           | Get evidence chain for metrics/insights          | Get evidence for net worth calculation    |

---

## Current Limitations

### Technical Limitations
1. **Code-Only Focus**: The graph runtime is currently focused on code analysis, not financial data
2. **No Financial Schema**: No schema for financial entities (accounts, transactions, loans, etc.)
3. **No Temporal Support**: Limited support for time-series financial data
4. **No Metric Calculation**: No support for financial metric calculation
5. **No Evidence Chains**: No support for financial evidence chains
6. **No Confidence Scoring**: No confidence scoring for financial metrics
7. **No Pattern Detection**: No support for spending/income pattern detection
8. **No Insight Generation**: No support for financial insight generation
9. **No Alert Management**: No support for financial alert management
10. **No Data Adapters**: No adapters for financial data sources

### Functional Limitations
1. **No Financial Traversal**: Cannot traverse financial relationships
2. **No Financial Selection**: Cannot select financial data by criteria
3. **No Financial Metrics**: Cannot calculate or store financial metrics
4. **No Explainability**: Cannot explain financial calculations
5. **No Provenance**: Cannot track data provenance for financial data
6. **No Temporal Analysis**: Cannot analyze financial data over time
7. **No Pattern Analysis**: Cannot detect spending/income patterns
8. **No Insight Management**: Cannot generate or manage financial insights
9. **No Alert Workflow**: Cannot create or manage financial alerts
10. **No Scenario Simulation**: Cannot simulate financial scenarios

### Integration Limitations
1. **No Workspace Integration**: No integration with financial workspaces
2. **No Command Center Integration**: No integration with command center visualizations
3. **No Intelligence Engine Integration**: No integration with intelligence engines
4. **No Component Integration**: No integration with UI components
5. **No Navigation Integration**: No integration with navigation system
6. **No Data Flow Integration**: No integration with data processing pipelines
7. **No API Integration**: No integration with financial API endpoints
8. **No DTO Integration**: No integration with financial DTOs
9. **No Visualization Integration**: No integration with charting components
10. **No State Management Integration**: No integration with frontend state management