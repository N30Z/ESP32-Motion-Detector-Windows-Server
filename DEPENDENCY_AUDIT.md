# Dependency Audit Report

**Date:** 2025-12-23
**Repository:** ESP32-Motion-Detector-Windows-Server
**Audit Scope:** Python dependencies (Server, Raspberry Pi Client) and ESP32 platformio dependencies

---

## Executive Summary

The project has **10 security vulnerabilities** across 3 packages that need immediate attention. Several packages are outdated and should be updated for security, performance, and compatibility improvements. The good news is that there is **no bloat** - all dependencies are actively used and necessary.

### Priority Levels
- **🔴 CRITICAL:** Security vulnerabilities requiring immediate updates
- **🟡 RECOMMENDED:** Outdated packages that should be updated
- **🟢 GOOD:** No issues detected

---

## 🔴 CRITICAL: Security Vulnerabilities

### Server Dependencies

| Package | Current | Vulnerabilities | Fix Version | Severity |
|---------|---------|-----------------|-------------|----------|
| **Werkzeug** | 3.0.1 | 4 CVEs | 3.1.4 | HIGH |
| **Pillow** | 10.1.0 | 2 CVEs | 12.0.0 | MEDIUM |

**Werkzeug Vulnerabilities:**
- CVE-2024-34069 - Fixed in 3.0.3
- CVE-2024-49766 - Fixed in 3.0.6
- CVE-2024-49767 - Fixed in 3.0.6
- CVE-2025-66221 - Fixed in 3.1.4

**Pillow Vulnerabilities:**
- CVE-2023-50447 - Fixed in 10.2.0
- CVE-2024-28219 - Fixed in 10.3.0

### Raspberry Pi Client Dependencies

| Package | Current | Vulnerabilities | Fix Version | Severity |
|---------|---------|-----------------|-------------|----------|
| **requests** | 2.31.0 | 2 CVEs | 2.32.5 | MEDIUM |
| **Pillow** | 10.1.0 | 2 CVEs | 12.0.0 | MEDIUM |

**requests Vulnerabilities:**
- CVE-2024-35195 - Fixed in 2.32.0
- CVE-2024-47081 - Fixed in 2.32.4

---

## 🟡 RECOMMENDED: Outdated Packages

### Server (`Server/requirements.txt`)

| Package | Current | Latest | Notes |
|---------|---------|--------|-------|
| Flask | 3.0.0 | 3.1.2 | New features, bug fixes |
| Werkzeug | 3.0.1 | 3.1.4 | ⚠️ Security fixes (see above) |
| opencv-contrib-python | 4.8.1.78 | 4.12.0.88 | Performance improvements, new CV algorithms |
| numpy | 1.24.3 | 2.4.0 | ⚠️ Major version change - test thoroughly |
| Pillow | 10.1.0 | 12.0.0 | ⚠️ Security fixes, performance improvements |
| PyYAML | 6.0.1 | 6.0.2 | Minor updates |

### Raspberry Pi Client (`Raspberry-Pi/Client/requirements.txt`)

| Package | Current | Latest | Notes |
|---------|---------|--------|-------|
| PyYAML | 6.0.1 | 6.0.2 | Minor updates |
| requests | 2.31.0 | 2.32.5 | ⚠️ Security fixes (see above) |
| gpiozero | 2.0 | 2.0.1 | Bug fixes |
| Pillow | 10.1.0 | 12.0.0 | ⚠️ Security fixes |

### Windows-Specific (`Server/requirements-windows.txt`)

| Package | Current | Latest | Notes |
|---------|---------|--------|-------|
| winotify | 1.1.0 | 1.1.0 | ✅ Up to date |

---

## 🟢 GOOD: No Unnecessary Dependencies

All dependencies are actively used in the codebase:

### Server Dependencies Usage
- ✅ **Flask** - Web framework (app.py)
- ✅ **Werkzeug** - Flask dependency
- ✅ **PyYAML** - Configuration files (config.yaml, rules.yaml)
- ✅ **opencv-contrib-python** - Face recognition (YuNet/SFace models)
- ✅ **numpy** - Image processing, face embeddings
- ✅ **Pillow** - Image manipulation

### Raspberry Pi Client Usage
- ✅ **PyYAML** - Configuration (config.yaml)
- ✅ **requests** - HTTP client for server communication
- ✅ **gpiozero** - PIR sensor GPIO control
- ✅ **Pillow** - Image processing

### ESP32 Client
- ✅ **No external libraries** - Uses only built-in ESP32 camera and WiFi libraries
- This is excellent for minimizing firmware size and dependencies!

---

## 📋 Recommended Actions

### Immediate (Security Fixes)

1. **Update Server dependencies:**
   ```bash
   cd Server
   # Edit requirements.txt
   # Werkzeug==3.0.1 → Werkzeug==3.1.4
   # Pillow==10.1.0 → Pillow==12.0.0
   pip install -r requirements.txt --upgrade
   ```

2. **Update Raspberry Pi Client dependencies:**
   ```bash
   cd Raspberry-Pi/Client
   # Edit requirements.txt
   # requests==2.31.0 → requests==2.32.5
   # Pillow==10.1.0 → Pillow==12.0.0
   pip install -r requirements.txt --upgrade
   ```

3. **Test thoroughly after updates:**
   - Test face recognition pipeline
   - Test notifications (Windows Toast, Linux notify)
   - Test image capture and processing
   - Test Raspberry Pi camera client

### Short-term (Performance & Features)

4. **Update Flask and related packages:**
   ```bash
   Flask==3.0.0 → Flask==3.1.2
   ```

5. **Update OpenCV:**
   ```bash
   opencv-contrib-python==4.8.1.78 → opencv-contrib-python==4.12.0.88
   ```
   - Test face recognition models (YuNet/SFace) compatibility
   - Verify detection/embedding performance

6. **Consider numpy update (with caution):**
   ```bash
   numpy==1.24.3 → numpy==2.4.0
   ```
   - ⚠️ **Major version change** - may have breaking changes
   - Test extensively with opencv and face recognition
   - Consider staying on numpy 1.26.x (LTS) if issues arise

### Long-term (Maintenance)

7. **Implement dependency scanning in CI/CD:**
   - Add `pip-audit` to GitHub Actions
   - Run weekly security scans
   - Example workflow:
     ```yaml
     - name: Security Audit
       run: |
         pip install pip-audit
         pip-audit -r requirements.txt
     ```

8. **Pin all dependencies with hash verification:**
   ```bash
   pip freeze > requirements.lock
   pip install -r requirements.lock --require-hashes
   ```

9. **Consider using dependency management tools:**
   - Poetry - For better dependency resolution
   - Dependabot - Automated PR for dependency updates

---

## 🔍 Detailed Analysis

### numpy 1.24.3 → 2.4.0 Considerations

**Breaking Changes:**
- NumPy 2.0 introduced significant API changes
- Some OpenCV operations may be affected
- Face embedding calculations might need testing

**Recommendation:**
- Test in a development environment first
- Alternative: Update to numpy 1.26.4 (last 1.x version) for stability
- Monitor OpenCV compatibility notes

### Pillow 10.1.0 → 12.0.0 Considerations

**Security Fixes:**
- CVE-2023-50447: Arbitrary code execution via crafted image
- CVE-2024-28219: Buffer overflow in image processing

**Breaking Changes:**
- Pillow 11.x and 12.x have some API changes
- Most image operations remain backward compatible

**Recommendation:**
- Update immediately for security
- Test JPEG encoding/decoding used in motion detection
- Test thumbnail generation in person management

### opencv-contrib-python Compatibility

**Current:** 4.8.1.78
**Latest:** 4.12.0.88

**Benefits:**
- Performance improvements in DNN module (used for YuNet/SFace)
- Better ONNX runtime support
- Bug fixes in face detection

**Risks:**
- ONNX model compatibility (test YuNet/SFace)
- API changes in cv2.FaceDetectorYN or cv2.FaceRecognizerSF

**Recommendation:**
- Update and test face recognition pipeline
- Keep current ONNX models (likely compatible)
- Monitor inference times for performance regressions

---

## 📊 Dependency Tree Health

### Server Total Dependencies: 6 core + 1 platform-specific
- Direct dependencies: Well-maintained
- Transitive dependencies: Managed by pip
- Unused dependencies: **0** ✅

### Raspberry Pi Client Total Dependencies: 4 core
- Direct dependencies: Minimal and necessary
- GPIO dependencies: Platform-specific (gpiozero)
- Unused dependencies: **0** ✅

### ESP32 Client Dependencies: 0 external
- Firmware size: Minimal ✅
- Update mechanism: PlatformIO platform updates

---

## 🎯 Priority Update Plan

### Phase 1: Security (This Week)
1. Update Werkzeug to 3.1.4
2. Update Pillow to 12.0.0
3. Update requests to 2.32.5
4. Run full test suite

### Phase 2: Stability (Next Week)
1. Update Flask to 3.1.2
2. Update gpiozero to 2.0.1
3. Test all features

### Phase 3: Performance (Following Week)
1. Update opencv-contrib-python to 4.12.0.88
2. Benchmark face recognition performance
3. Consider numpy 2.x (or stay on 1.26.x)

---

## 📝 Testing Checklist

After updating dependencies, verify:

- [ ] Server starts without errors
- [ ] Face recognition works (detection + embedding)
- [ ] Person management UI functional
- [ ] Auto-learning still works
- [ ] Windows Toast notifications (if on Windows)
- [ ] Linux desktop notifications (if on Linux)
- [ ] Raspberry Pi camera capture works
- [ ] PIR sensor detection works
- [ ] ESP32 client can upload images
- [ ] MJPEG streaming works
- [ ] Database operations (SQLite) work
- [ ] Configuration loading works

---

## 🔒 Security Best Practices

### Already Implemented ✅
- Token-based authentication
- No hardcoded secrets (secrets.h.example)
- Input validation
- Local-only deployment (no cloud dependencies)

### Additional Recommendations
1. **Regular dependency audits:**
   ```bash
   pip-audit -r requirements.txt
   ```

2. **Use virtual environments:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux
   venv\Scripts\activate     # Windows
   ```

3. **Lock dependency versions:**
   - Current approach (pinned versions) is good
   - Consider using requirements.lock for hash verification

4. **Monitor security advisories:**
   - GitHub Security Advisories
   - PyPI security notifications
   - OpenCV security bulletins

---

## 📈 Conclusion

The project has a **lean dependency footprint** with no unnecessary bloat, which is excellent. However, **immediate action is required** to address the 10 security vulnerabilities across Werkzeug, Pillow, and requests.

**Summary:**
- 🔴 10 security vulnerabilities (HIGH priority)
- 🟡 6 outdated packages (MEDIUM priority)
- 🟢 0 unnecessary dependencies (excellent!)
- 🟢 ESP32 has no external deps (excellent!)

**Estimated Update Time:**
- Security fixes: 1-2 hours (including testing)
- Performance updates: 2-3 hours (including benchmarking)
- CI/CD integration: 1-2 hours

**Next Steps:**
1. Create a backup/branch before updates
2. Update requirements.txt files
3. Test in development environment
4. Deploy to production after validation
5. Set up automated dependency scanning

---

**Audit completed by:** Claude Code
**Contact:** See GitHub issues for questions
