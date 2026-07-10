# AI Architecture - ClariFinOS 2.0

*Hybrid deterministic + LLM-assisted design*

---

## Core Principle

**Never use LLMs for numerical calculations.**

All financial figures (EMI, interest, credit scores, reconciliation matches) are computed via deterministic logic. LLMs only assist with:

1. Natural language explanations
2. Receipt/document understanding
3. Conversational Q&A
4. Narrative generation

---

## Responsibility Matrix

| Capability | Approach | LLM Model | Justification |
|------------|----------|-----------|---------------|
| EMI Calculation | Pure Deterministic | N/A | Mathematical formula |
| XIRR Calculation | Deterministic | N/A | Newton-Raphson iteration |
| Reconciliation Match | Deterministic | N/A | Rule-based matching |
| Credit Utilization | Deterministic | N/A | Simple percentage |
| Financial Health Score | Deterministic | N/A | Weighted formula |
| **Payment Recommendations** | Rule-based | N/A | Decision logic |
| **Loan Payoff Strategy** | Deterministic | N/A | Avalanche/snowball formulas |
| Natural Language Explanations | LLM-Assisted | Phi-3 Mini | Human-readable narratives |
| Receipt Understanding | LLM-Assisted | Qwen-VL 2B | Layout parsing |
| Investment Commentary | LLM-Assisted | Phi-3 Mini | Market narrative |
| Financial Q&A | LLM-Assisted + Retrieval | Phi-3 Mini | Query understanding |
| Personalized Coaching | LLM-Assisted | Phi-3 Mini | Conversational flow |
| Merchant Normalization | Statistical | N/A | Pattern matching |
| Subscription Detection | Statistical | N/A | Recurring pattern analysis |
| Forecast Generation | Statistical | N/A | Time series models |
| Risk Assessment | Deterministic + Rules | N/A | Known patterns |

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              ORCHESTRATION SERVICE LAYER                     │
│  - Receives user query                                        │
│  - Routes to deterministic or LLM path                       │
│  - Combines results                                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│           DETERMINISTIC FINANCE ENGINE LAYER                 │
│                                                            │
│  [Account Engine] [Reconciliation] [Loan Engine] [CreditCard]│
│                                                            │
│  All calculations in integer paise                          │
│  All decisions documented and traceable                    │
│  All outputs reproducible                                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              LLM-ASSISTED EXPERIENCE LAYER                 │
│  - Phi-3 Mini (3.8B params, 2GB RAM)                      │
│  - Qwen-VL 2B for vision                                   │
│  - All inference local                                       │
│  - Responses cached                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## LLM Integration Patterns

### Pattern 1: Explanation Generation
```
Input: Deterministic result (e.g., "EMI = ₹87,996")
Prompt: "Explain why this EMI amount is calculated. Use simple terms."
Output: "Your EMI is ₹87,996 because..."

Implementation:
1. Compute EMI deterministically
2. Format prompt with inputs
3. Call Phi-3 Mini locally
4. Cache explanation with hash of inputs
```

### Pattern 2: Receipt Understanding
```
Input: Image of receipt
Processing:
1. Preprocess image (resize, normalize)
2. Run Qwen-VL 2B
3. Extract: merchant, date, amount, items
4. Post-process: clean to paise integers
Output: Structured data for transaction creation

Privacy: Image never leaves device
```

### Pattern 3: Financial Q&A
```
Query: "Why is my credit utilization high?"
Process:
1. Parse intent (LLM)
2. Retrieve relevant data (det)
3. Format context for LLM
4. Generate explanation
5. Include deterministic recommendations

Example response:
"Your ICICI card is at 78% utilization... To improve, pay ₹15,000 by due date..."
```

---

## Model Selection

### Phi-3 Mini (Recommended)
```
Size: 3.8B parameters
RAM: 2GB (Q4_K_M quantization)
Speed: 5-10 tokens/sec (CPU)
Accuracy: Excellent for financial text
License: MIT
```

### Qwen-VL 2B (For Vision)
```
Size: 2B parameters vision + 1.5B text
RAM: 1.5GB (vision model only)
Use: Receipt line item extraction
Privacy: Fully local
```

### Deployment Architecture
```
Local LLM Server (Docker container):
- llama.cpp backend
- REST API wrapper
- Model files mounted as volumes
- Quantization: Q4_K_M for efficiency
```

---

## Prompt Engineering

### Financial Explanation Template
```
You are a financial advisor. Explain the following in 3-4 sentences:

[FINANCIAL_DATA]

Keep explanation simple, avoid jargon, focus on actionable insight.
```

### Receipt Parsing Template
```
Extract from this receipt image:
- Merchant name
- Date (YYYY-MM-DD)
- Total amount (numbers only)
- Individual items with prices
- Payment method

Return as JSON.
```

### Q&A Template
```
You are a financial assistant. Answer based on user data:

[USER_QUESTION]

[RELEVANT_DATA]

Keep answer factual, cite numbers, suggest action if relevant.
```

---

## Caching Strategy

### Why Cache
- Identical queries should return identical answers
- Reduce LLM inference time
- Enable offline access to explanations

### Cache Key
```
cache_key = SHA256(prompt_template + sorted_inputs)
TTL = 30 days (user data changes slowly)
```

### Storage
```
Table: llm_cache
- prompt_hash TEXT PRIMARY KEY
- response_text TEXT
- created_at TEXT
- inputs_json TEXT  -- for debugging
```

---

## Performance Targets

| Operation | Target Time |
|-----------|-------------|
| Deterministic calculation | < 10ms |
| LLM explanation (cached) | < 5ms |
| LLM explanation (fresh) | 200-400ms |
| Receipt parsing | 500-800ms |
| Q&A response | 300-600ms |

---

## Privacy & Security

### Data Handling
- No transaction data sent to external LLM
- All inference runs local via llama.cpp
- Cache stored encrypted at rest

### Model Updates
- Version models with semantic versioning
- Update only via explicit download
- Verify model integrity with SHA-256

### Compliance
- GDPR compliant (no data export)
- Ready for financial data protection (DPDP Act)
- Audit trail for all LLM interactions