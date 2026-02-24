/**
 * Test Report Generator
 * ======================
 * 
 * Generates comprehensive test reports:
 * - Test coverage summary
 * - CSS stability report
 * - Navigation integrity report
 * - Runtime error report
 * - API stability report
 * - Mode isolation validation
 * - Performance benchmark summary
 */

// ============================================================================
// Types
// ============================================================================

interface TestSummary {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
}

interface CategoryResult {
  category: string;
  total: number;
  passed: number;
  failed: number;
  tests: string[];
}

interface ReportData {
  timestamp: string;
  summary: TestSummary;
  categories: CategoryResult[];
  errors: string[];
  warnings: string[];
  performance: {
    pageLoadTimes: Record<string, number>;
    apiResponseTimes: Record<string, number>;
  };
}

// ============================================================================
// Report Generator
// ============================================================================

class ReportGenerator {
  private report: ReportData;

  constructor() {
    this.report = {
      timestamp: new Date().toISOString(),
      summary: { total: 0, passed: 0, failed: 0, skipped: 0, duration: 0 },
      categories: [],
      errors: [],
      warnings: [],
      performance: { pageLoadTimes: {}, apiResponseTimes: {} },
    };
  }

  /**
   * Add a test result
   */
  addTest(title: string, status: 'passed' | 'failed' | 'skipped', duration: number): void {
    this.report.summary.total++;
    this.report.summary.duration += duration;

    switch (status) {
      case 'passed':
        this.report.summary.passed++;
        break;
      case 'failed':
        this.report.summary.failed++;
        this.report.errors.push(`FAILED: ${title}`);
        break;
      case 'skipped':
        this.report.summary.skipped++;
        break;
    }

    const category = this.categorizeTest(title);
    this.addToCategory(category, title, status === 'passed');
  }

  /**
   * Categorize test based on title
   */
  private categorizeTest(title: string): string {
    const lowerTitle = title.toLowerCase();
    
    if (lowerTitle.includes('navigation') || lowerTitle.includes('route') || lowerTitle.includes('page load')) {
      return 'Navigation';
    }
    if (lowerTitle.includes('dashboard')) {
      return 'Dashboard';
    }
    if (lowerTitle.includes('transaction')) {
      return 'Transactions';
    }
    if (lowerTitle.includes('reconciliation')) {
      return 'Reconciliation';
    }
    if (lowerTitle.includes('behavior') || lowerTitle.includes('insight')) {
      return 'Behavior';
    }
    if (lowerTitle.includes('mode') || lowerTitle.includes('personal') || lowerTitle.includes('family')) {
      return 'Mode Isolation';
    }
    if (lowerTitle.includes('css') || lowerTitle.includes('layout') || lowerTitle.includes('overflow')) {
      return 'CSS Integrity';
    }
    if (lowerTitle.includes('visual') || lowerTitle.includes('screenshot')) {
      return 'Visual Regression';
    }
    if (lowerTitle.includes('performance') || lowerTitle.includes('load') || lowerTitle.includes('render')) {
      return 'Performance';
    }
    return 'Other';
  }

  /**
   * Add test to category
   */
  private addToCategory(category: string, testName: string, passed: boolean): void {
    let cat = this.report.categories.find(c => c.category === category);
    if (!cat) {
      cat = { category, total: 0, passed: 0, failed: 0, tests: [] };
      this.report.categories.push(cat);
    }
    cat.total++;
    if (passed) {
      cat.passed++;
    } else {
      cat.failed++;
    }
    cat.tests.push(testName);
  }

  /**
   * Add a warning
   */
  addWarning(warning: string): void {
    this.report.warnings.push(warning);
  }

  /**
   * Add performance metric
   */
  addPageLoadTime(page: string, time: number): void {
    this.report.performance.pageLoadTimes[page] = time;
  }

  /**
   * Add API response time
   */
  addApiResponseTime(endpoint: string, time: number): void {
    this.report.performance.apiResponseTimes[endpoint] = time;
  }

  /**
   * Generate markdown report
   */
  generateMarkdown(): string {
    const lines: string[] = [];

    lines.push('# 🧪 ClariFin_OS Test Report');
    lines.push('');
    lines.push(`**Generated:** ${this.report.timestamp}`);
    lines.push('');

    // Summary
    lines.push('## 📊 Summary');
    lines.push('');
    lines.push('| Metric | Value |');
    lines.push('|--------|-------|');
    lines.push(`| Total Tests | ${this.report.summary.total} |`);
    lines.push(`| ✅ Passed | ${this.report.summary.passed} |`);
    lines.push(`| ❌ Failed | ${this.report.summary.failed} |`);
    lines.push(`| ⏭️ Skipped | ${this.report.summary.skipped} |`);
    lines.push(`| ⏱️ Duration | ${(this.report.summary.duration / 1000).toFixed(2)}s |`);
    lines.push('');

    // Pass rate
    const passRate = this.report.summary.total > 0
      ? ((this.report.summary.passed / this.report.summary.total) * 100).toFixed(1)
      : '0';
    lines.push(`**Pass Rate:** ${passRate}%`);
    lines.push('');

    // Category breakdown
    lines.push('## 📁 Category Breakdown');
    lines.push('');
    lines.push('| Category | Total | Passed | Failed | Pass Rate |');
    lines.push('|----------|-------|--------|--------|-----------|');

    for (const cat of this.report.categories) {
      const rate = cat.total > 0 ? ((cat.passed / cat.total) * 100).toFixed(0) : '0';
      lines.push(`| ${cat.category} | ${cat.total} | ${cat.passed} | ${cat.failed} | ${rate}% |`);
    }
    lines.push('');

    // Errors
    if (this.report.errors.length > 0) {
      lines.push('## ❌ Errors');
      lines.push('');
      for (const error of this.report.errors) {
        lines.push(`- ${error}`);
      }
      lines.push('');
    }

    // Warnings
    if (this.report.warnings.length > 0) {
      lines.push('## ⚠️ Warnings');
      lines.push('');
      for (const warning of this.report.warnings) {
        lines.push(`- ${warning}`);
      }
      lines.push('');
    }

    // Performance
    if (Object.keys(this.report.performance.pageLoadTimes).length > 0) {
      lines.push('## ⚡ Performance Metrics');
      lines.push('');
      lines.push('### Page Load Times');
      lines.push('');
      lines.push('| Page | Load Time |');
      lines.push('|------|-----------|');
      for (const [page, time] of Object.entries(this.report.performance.pageLoadTimes)) {
        lines.push(`| ${page} | ${time}ms |`);
      }
      lines.push('');
    }

    // Recommendations
    lines.push('## 💡 Recommendations');
    lines.push('');

    if (this.report.summary.failed > 0) {
      lines.push('### Immediate Actions Required');
      lines.push('');
      lines.push('1. Review and fix all failed tests');
      lines.push('2. Check console errors in browser dev tools');
      lines.push('3. Verify API endpoints are responding correctly');
      lines.push('4. Ensure no hydration mismatches in React components');
      lines.push('');
    }

    lines.push('### Next Steps');
    lines.push('');
    lines.push('1. Run tests locally before pushing: `npm run test`');
    lines.push('2. Review visual regression diffs in `test-results/`');
    lines.push('3. Check performance metrics against thresholds');
    lines.push('4. Verify mode isolation between Personal and Family dashboards');
    lines.push('');

    // Footer
    lines.push('---');
    lines.push('');
    lines.push('*Generated by ClariFin_OS Playwright Test Suite*');

    return lines.join('\n');
  }

  /**
   * Generate JSON report
   */
  generateJSON(): string {
    return JSON.stringify(this.report, null, 2);
  }

  /**
   * Get report data
   */
  getReport(): ReportData {
    return this.report;
  }
}

// ============================================================================
// Export
// ============================================================================

export { ReportGenerator };
export type { ReportData, TestSummary, CategoryResult };