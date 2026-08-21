# ClariFin OS — Product Support Contract

## **Browser Support Contract**

### **Supported Browsers**
ClariFin OS is **officially supported** on the following browser configurations:

1. **Chrome Desktop**
   - **Profile**: `chromium` (Playwright project)
   - **Viewport**: 1280x720
   - **Interaction**: Mouse/keyboard

2. **Chrome Touch (Mobile)**
   - **Profile**: `mobile-chrome` (Playwright project)
   - **Device**: Pixel 5 (emulated)
   - **Viewport**: 393x851
   - **Interaction**: Touch gestures

### **Unsupported Browsers**
The following browsers are **not supported** and are excluded from verification:

- Firefox
- WebKit/Safari (Desktop)
- Mobile Safari
- Tablet (iPad, non-Chrome touch profiles)

### **Rationale**
- **Enterprise-Grade Verification**: The product is optimized for Chrome/Chromium, including touch interactions on mobile devices.
- **CI Efficiency**: Reducing the browser matrix to supported configurations ensures deterministic, enterprise-grade verification.
- **Historical Evidence**: Snapshots for unsupported browsers are preserved as untracked artifacts for reference but are not maintained.

### **Playwright Configuration**
- **Projects**: Only `chromium` and `mobile-chrome` are executed in CI.
- **Snapshots**: Visual snapshots are generated exclusively for supported profiles.
- **Lifecycle**: Backend and frontend lifecycles are deterministic and health-checked.

### **Verification**
- **CI Gate**: The Playwright workflow (`runtime/verify.py playwright`) enforces the supported browser contract.
- **Evidence**: Snapshots and test results are archived for supported browsers only.

---
**Note**: This contract is authoritative and aligns with the repository's verification architecture. Do not modify production behavior or weaken tests to accommodate unsupported browsers.