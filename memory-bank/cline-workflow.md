# Cline Workflow

Before code changes:
1. Read memory-bank/*.md
2. Inspect relevant architecture using cgc
3. Use grep only as fallback

After code changes:
1. Run verify-fast.sh
2. Fix all failures
3. Run verify-local.sh for behavioural changes

Never:
- bypass verification
- remove failing tests without analysis
- modify architecture boundaries casually
