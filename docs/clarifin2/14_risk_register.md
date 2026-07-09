# Risk Register - ClariFinOS 2.0

*Technical and business risks with mitigations*

---

## Technical Risks

### 1. Calculation Accuracy Risk
**Risk**: Financial formulas produce incorrect results, misleading users.

**Impact**: HIGH (Financial decisions based on wrong data)

**Probability**: MEDIUM

**Mitigation**:
- Golden master tests against known calculators
- Peer review of all formulas
- Decimal arithmetic (no float)
- Unit tests for every edge case
- User verification step before major actions

### 2. Data Loss Risk
**Risk**: User data lost due to corruption or accidental deletion.

**Impact**: CRITICAL

**Probability**: LOW

**Mitigation**:
- Immutable transactions (triggers prevent UPDATE/DELETE)
- Regular backups
- Export functionality (CSV/JSON)
- Checksum verification on import
- WAL mode for crash recovery

### 3. LLM Hallucination Risk
**Risk**: LLM provides incorrect financial explanations.

**Impact**: MEDIUM (User confusion)

**Probability**: LOW (deterministic core prevents)

**Mitigation**:
- LLM never used for calculations
- All explanations trace back to deterministic data
- User can verify numbers independently
- Cache explanations to prevent drift

### 4. Database Migration Risk
**Risk**: Schema changes break existing user data.

**Impact**: HIGH

**Probability**: MEDIUM

**Mitigation**:
- Non-breaking migrations (nullable columns)
- Migration testing with production snapshots
- Rollback scripts for each migration
- Version backup before migration

### 5. Performance Risk
**Risk**: Queries slow on large datasets (10K+ transactions).

**Impact**: MEDIUM

**Probability**: HIGH

**Mitigation**:
- Indexes on all query paths
- Pagination for large results
- Async processing for heavy operations
- SQLite → PostgreSQL migration path

---

## Business Risks

### 1. Bank Sync Risk
**Risk**: Bank API integration fails or gets rate-limited.

**Impact**: HIGH (Users revert to manual imports)

**Probability**: HIGH

**Mitigation**:
- Multiple aggregator support (Plaid + Yodlee + FinBox)
- Local fallback optimized
- Rate limit handling
- Clear error messages to users

### 2. Competition Risk
**Risk**: Established players release better features.

**Impact**: HIGH

**Probability**: HIGH

**Mitigation**:
- Focus on India-specific features
- Build community around precision
- Open-source core for transparency
- Faster iteration on reconciliation

### 3. User Adoption Risk
**Risk**: Users don't understand value proposition.

**Impact**: HIGH

**Probability**: MEDIUM

**Mitigation**:
- Onboarding with clear examples
- Wellness score gamification
- Shareable insights
- Referral program

### 4. Regulatory Risk
**Risk**: Financial regulations change (data storage, privacy).

**Impact**: MEDIUM

**Probability**: MEDIUM

**Mitigation**:
- All data local by default
- No PII in analytics
- Export/delete functionality
- DPDP Act compliance ready

---

## Operational Risks

### 1. LLM Resource Risk
**Risk**: Local LLM inference too slow or resource-intensive.

**Impact**: MEDIUM

**Probability**: LOW

**Mitigation**:
- Q4_K_M quantization reduces RAM
- Cached responses for common queries
- Async processing
- CPU fallback if no GPU

### 2. Accuracy Drift Risk
**Risk**: Behaviour scores change unexpectedly.

**Impact**: MEDIUM

**Probability**: LOW

**Mitigation**:
- Version all scoring formulas
- Explainable components
- User can see contributing factors
- Monthly score validation

### 3. Reconciliation False Positive Risk
**Risk**: Wrong matches create incorrect money flow graph.

**Impact**: MEDIUM

**Probability**: LOW

**Mitigation**:
- Confidence thresholds (0.7+ for auto)
- Undo functionality
- Manual override
- Audit trail for all matches

---

## Risk Matrix

| Risk ID | Risk | Impact | Probability | Priority | Owner |
|---------|------|--------|-------------|----------|-------|
| TEC-01 | Calculation inaccuracy | HIGH | MEDIUM | HIGH | Lead Engineer |
| TEC-02 | Data loss/corruption | CRITICAL | LOW | HIGH | All Engineers |
| TEC-03 | LLM hallucination | MEDIUM | LOW | MEDIUM | ML Engineer |
| TEC-04 | Migration failure | HIGH | MEDIUM | HIGH | DB Admin |
| TEC-05 | Performance degradation | MEDIUM | HIGH | HIGH | Backend Team |
| BUS-01 | Bank sync failure | HIGH | HIGH | CRITICAL | Product Manager |
| BUS-02 | Competition ahead | HIGH | HIGH | HIGH | Product Manager |
| BUS-03 | User adoption low | HIGH | MEDIUM | MEDIUM | Growth Team |
| BUS-04 | Regulatory non-compliance | MEDIUM | MEDIUM | MEDIUM | Legal Team |
| OPR-01 | LLM resource exhaustion | MEDIUM | LOW | MEDIUM | ML Engineer |
| OPR-02 | Score drift | MEDIUM | LOW | LOW | Lead Engineer |
| OPR-03 | Reconciliation errors | MEDIUM | LOW | LOW | Backend Team |

---

## Risk Monitoring

### Weekly Checks
- Test coverage > 85%
- No precision errors in calculations
- Migration passes on test DB

### Monthly Checks
- Reconciliation accuracy > 95%
- Performance benchmarks met
- User satisfaction scores

### Quarterly Checks
- Competitive feature gap analysis
- Regulatory compliance review
- Security audit

---

## Contingency Plans

### If Bank Sync Fails
- Double down on import UX
- Add OFX/QFX support
- Build sharing templates

### If Reconciliation < 90% Accuracy
- Add user feedback loop for corrections
- Improve rule engine
- Add fuzzy matching

### If LLM Performance Poor
- Remove LLM layer temporarily
- Revert to rule-based explanations
- Upgrade hardware requirements

---

## Risk Acceptance

| Risk | Acceptance | Notes |
|------|------------|-------|
| TEC-05 (Performance) | Accepted | SQLite scales to 100K transactions |
| BUS-02 (Competition) | Mitigated | Differentiated by precision + India focus |
| OPR-02 (Score drift) | Monitored | Users expect gradual improvements |