# AI Strategy & Lightweight LLM Feasibility

*Evaluating where AI genuinely adds value vs deterministic logic*

---

## AI Opportunity Assessment

### Transaction Categorization

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | Statistical + Rule-based hybrid |
| **Expected Accuracy** | 90-95% with merchant learning |
| **Operational Cost** | Near-zero (local fuzzy matching) |
| **Latency** | <10ms (string operations) |
| **Maintenance Burden** | Low (merchant dictionary grows organically) |
| **Privacy Implications** | None (local only) |
| **Offline Capability** | ✅ Full offline |

**Why NOT LLM**: Deterministic rules (merchant → category) and fuzzy matching (Levenshtein distance) are faster, cheaper, and deterministic. LLMs introduce inconsistency and monthly API costs.

---

### Merchant Normalization

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | Rule-based + Statistical learning |
| **Expected Accuracy** | 95%+ for known merchants, 80% for variants |
| **Operational Cost** | Near-zero (local fuzzy matching) |
| **Latency** | <50ms |
| **Maintenance Burden** | Low (merchant canonical map) |
| **Privacy Implications** | None |
| **Offline Capability** | ✅ Full offline |

**Why NOT LLM**: Merchant names follow patterns (e.g., "SWIGGY*" → Swiggy). Rules + fuzzy matching are deterministic and privacy-safe.

---

### Receipt Understanding

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | LLM-assisted |
| **Expected Accuracy** | 85-90% with vision models |
| **Operational Cost** | Low (local GGUF quantized model) |
| **Latency** | 200-500ms (CPU) |
| **Maintenance Burden** | Medium (model updates) |
| **Privacy Implications** | High (image data) |
| **Offline Capability** | ✅ CPU-only models work offline |

**Why LLM-Assist**: Receipts have varied layouts. OCR + template matching has limits. LLaVA or Qwen-VL can extract line items without cloud dependency.

---

### PDF Extraction

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | Hybrid (rules + lightweight OCR) |
| **Expected Accuracy** | 90% for clean PDFs, 70% for scanned |
| **Operational Cost** | Low (local OCR) |
| **Latency** | 1-3s per page |
| **Maintenance Burden** | Low (no learning required) |
| **Privacy Implications** | Medium (statement image) |
| **Offline Capability** | ✅ Tesseract works offline |

**Why NOT LLM**: Bank statements have consistent formats. Layout analysis + OCR suffices for 90%+ accuracy.

---

### Financial Explanations

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | LLM-assisted |
| **Expected Accuracy** | N/A (generative) |
| **Operational Cost** | Low (local inference) |
| **Latency** | 100-300ms (3B model) |
| **Maintenance Burden** | Medium (prompt tuning) |
| **Privacy Implications** | Low (summarization only) |
| **Offline Capability** | ✅ Quantized model |

**Why LLM**: Natural language generation for financial insights has no deterministic equivalent. Users expect plain-English summaries.

---

### Spending Insights

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | Statistical |
| **Expected Accuracy** | 95% (pattern analysis) |
| **Operational Cost** | Near-zero |
| **Latency** | <20ms |
| **Maintenance Burden** | Low |
| **Privacy Implications** | None |
| **Offline Capability** | ✅ Full offline |

**Why NOT LLM**: Insights are derived from known patterns (trend, volatility). Deterministic algorithms are more maintainable.

---

### Personalized Coaching

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | LLM-assisted + Rules |
| **Expected Accuracy** | Subjective |
| **Operational Cost** | Low (local) |
| **Latency** | 200-400ms |
| **Maintenance Burden** | High (regular prompt iteration) |
| **Privacy Implications** | Low |
| **Offline Capability** | ✅ Quantized model |

**Why LLM**: Coaching requires conversational ability. Rules can trigger LLM for explanation, but core logic stays deterministic.

---

### Goal Recommendations

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | Deterministic rules |
| **Expected Accuracy** | 90% (rule-based) |
| **Operational Cost** | Near-zero |
| **Latency** | <10ms |
| **Maintenance Burden** | Low |
| **Privacy Implications** | None |
| **Offline Capability** | ✅ Full offline |

**Why NOT LLM**: Goals follow standard formulas (retirement corpus = years × expenses). Rules are transparent and auditable.

---

### Debt Optimization

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | Deterministic calculations |
| **Expected Accuracy** | 100% (math) |
| **Operational Cost** | Near-zero |
| **Latency** | <10ms |
| **Maintenance Burden** | Low |
| **Privacy Implications** | None |
| **Offline Capability** | ✅ Full offline |

**Why NOT LLM**: EMI, prepayment impact, and payoff optimization are pure mathematics. No ambiguity exists.

---

### Investment Commentary

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | LLM-assisted |
| **Expected Accuracy** | N/A (generative) |
| **Operational Cost** | Low (local) |
| **Latency** | 200-500ms |
| **Maintenance Burden** | Medium |
| **Privacy Implications** | Low |
| **Offline Capability** | ✅ Quantized model |

**Why LLM**: Market commentary is inherently language-based. However, core portfolio analytics stay deterministic.

---

### Fraud Detection

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | Statistical + Rules |
| **Expected Accuracy** | 85-90% |
| **Operational Cost** | Near-zero |
| **Latency** | <50ms |
| **Maintenance Burden** | Medium (threshold tuning) |
| **Privacy Implications** | None |
| **Offline Capability** | ✅ Full offline |

**Why NOT LLM**: Fraud detection uses known patterns (amount spikes, unusual time, new merchant). Rules are explainable and auditable.

---

### Duplicate Detection

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | Deterministic rules |
| **Expected Accuracy** | High |
| **Operational Cost** | Near-zero |
| **Latency** | <10ms |
| **Maintenance Burden** | Low |
| **Privacy Implications** | None |
| **Offline Capability** | ✅ Full offline |

**Why NOT LLM**: Duplicates are exact matches on hash_signature or amount+date+account. Pure logic.

---

### Cashflow Forecasting

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | Statistical time-series |
| **Expected Accuracy** | 70-85% (user-dependent) |
| **Operational Cost** | Near-zero |
| **Latency** | <50ms |
| **Maintenance Burden** | Low |
| **Privacy Implications** | None |
| **Offline Capability** | ✅ Full offline |

**Why NOT LLM**: Forecasting uses moving averages, seasonality, and extrapolation. Deterministic algorithms are predictable.

---

### Budget Suggestions

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | Statistical + Rules |
| **Expected Accuracy** | 80-90% |
| **Operational Cost** | Near-zero |
| **Latency** | <20ms |
| **Maintenance Burden** | Low |
| **Privacy Implications** | None |
| **Offline Capability** | ✅ Full offline |

**Why NOT LLM**: Budgets are income × percentage rules. Priority ranking is deterministic.

---

### Natural Language Search

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | LLM-assisted |
| **Expected Accuracy** | 85-90% |
| **Operational Cost** | Low (local) |
| **Latency** | 100-300ms |
| **Maintenance Burden** | Medium |
| **Privacy Implications** | Low |
| **Offline Capability** | ✅ Quantized model |

**Why LLM**: Parsing "Show me all Zomato spends last month" into SQL requires semantic understanding.

---

### Financial Q&A

| Aspect | Recommendation |
|--------|----------------|
| **Recommended Approach** | LLM-assisted + Deterministic retrieval |
| **Expected Accuracy** | Variable |
| **Operational Cost** | Low (local) |
| **Latency** | 300-600ms |
| **Maintenance Burden** | High |
| **Privacy Implications** | Low (no data sent) |
| **Offline Capability** | ✅ Quantized model |

**Why LLM**: Questions like "Why am I spending more?" require narrative synthesis. Core data retrieval stays deterministic.

---

## Lightweight LLM Feasibility Assessment

### Model Comparison Matrix

| Model | RAM Required | CPU-Only Feasible | Quantized GGUF | Inference Speed | Cost | Privacy | Suitability |
|-------|--------------|-------------------|----------------|-----------------|------|---------|-------------|
| **Phi-3 Mini (3.8B)** | 2GB | ✅ Yes | ✅ Q4_K_M | 5-10 tokens/sec | Free (local) | ✅ Full | ⭐⭐⭐⭐⭐ Best fit |
| **Phi-4 Mini** | 2GB | ✅ Yes | ✅ Q4_K_M | 4-8 tokens/sec | Free (local) | ✅ Full | ⭐⭐⭐⭐☆ Excellent |
| **Qwen 2.5 Instruct (3B)** | 2GB | ✅ Yes | ✅ Q4_K_M | 6-12 tokens/sec | Free (local) | ✅ Full | ⭐⭐⭐⭐☆ Strong |
| **Gemma 3 (2B)** | 1.5GB | ✅ Yes | ✅ Q4_K_M | 8-15 tokens/sec | Free (local) | ✅ Full | ⭐⭐⭐⭐ Good |
| **Llama 3.2 3B** | 3GB | ✅ Yes | ✅ Q4_K_M | 4-8 tokens/sec | Free (local) | ✅ Full | ⭐⭐⭐ Decent |
| **Mistral 7B** | 4GB | ⚠️ Slow | ✅ Q4_K_M | 2-4 tokens/sec | Free (local) | ✅ Full | ⭐⭐ Heavy |
| **TinyLlama (1.1B)** | 1GB | ✅ Yes | ✅ Q4_K_M | 15-25 tokens/sec | Free (local) | ✅ Full | ⚠️ Limited for finance |

---

### Recommended Architecture

**Hybrid Architecture - Keep Deterministic Core**

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                 DETERMINISTIC FINANCE ENGINE             │
│  (All calculations: EMI, XIRR, reconciliation, budgets)  │
│                    Zero LLM involvement                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                   LLM-ASSISTED LAYER                     │
│  - Natural language explanations                          │
│  - Receipt understanding                                  │
│  - Investment commentary                                    │
│  - Financial Q&A                                          │
│  - Personalized coaching                                  │
└─────────────────────────────────────────────────────────────┘
```

---

### Deployment Recommendation

**Recommendation: Hybrid Architecture with Local LLM (Phi-3 Mini)**

1. **Core Financial Calculations → Deterministic Only**
   - EMI, amortization, XIRR, CAGR, cashflow
   - Reconciliation matching, audit validation
   - Budget calculations, goal projections

2. **Natural Language Explanations → LLM-assisted**
   - Use Phi-3 Mini locally via llama.cpp
   - Prompt: "Explain this transaction spike in 2 sentences"
   - Cache responses to avoid re-computation

3. **Document Understanding → LLM-assisted**
   - Receipt parsing with small vision model (Qwen-VL 2B)
   - No image sent to cloud, all local

4. **Forecasting → Statistical Models**
   - ARIMA-light or exponential smoothing
   - No LLM needed for numerical prediction

5. **Decision Making → Deterministic Rules**
   - Budget alerts, prepayment decisions, goal tracking
   - LLM can only explain decisions, never make them

---

### Implementation Path

| Phase | LLM Capability | Model | Use Case |
|-------|----------------|-------|----------|
| Q1 | Reasoning only | Phi-3 Mini Q4 | Financial explanations, Q&A |
| Q2 | Vision | Qwen-VL 2B | Receipt line item extraction |
| Q3 | Conversational | Phi-3 Mini | Personalized coaching |
| Q4 | All above | Same | Full hybrid deployment |

---

### Why NOT Pure LLM Architecture

1. **Financial Accuracy**: LLMs hallucinate numbers. "Your portfolio grew 15%" when it actually grew 8% erodes trust.
2. **Regulatory Compliance**: Deterministic logic is auditable. LLMs cannot explain why a prepayment decision was made to a regulator.
3. **Performance**: 100ms deterministic xirr vs 300ms LLM for simple calculations is unacceptable.
4. **Cost**: API calls at scale ($10K+/month) vs $0 for local models.
5. **Privacy**: Users trust local processing for their financial data.