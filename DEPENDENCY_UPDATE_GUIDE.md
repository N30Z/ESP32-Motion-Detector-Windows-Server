# Dependency Update Guide

This guide helps you update dependencies to fix security vulnerabilities and improve performance.

---

## ⚠️ Before You Start

1. **Backup your data:**
   ```bash
   # Backup database and images
   cp -r Server/data Server/data.backup
   cp -r Server/storage Server/storage.backup
   ```

2. **Create a git branch:**
   ```bash
   git checkout -b dependency-updates
   ```

3. **Test in development first** - Don't update production directly!

---

## 🔴 Security Updates (REQUIRED)

### Option A: Quick Update (Recommended Files)

We've created `.recommended` files with safe, tested versions:

**Server:**
```bash
cd Server
mv requirements.txt requirements.txt.old
mv requirements.txt.recommended requirements.txt
pip install -r requirements.txt --upgrade
```

**Raspberry Pi Client:**
```bash
cd Raspberry-Pi/Client
mv requirements.txt requirements.txt.old
mv requirements.txt.recommended requirements.txt
pip install -r requirements.txt --upgrade
```

### Option B: Manual Update (Current Files)

Edit the files directly:

**Server/requirements.txt:**
```diff
-Flask==3.0.0
+Flask==3.1.2
-Werkzeug==3.0.1
+Werkzeug==3.1.4
-opencv-contrib-python==4.8.1.78
+opencv-contrib-python==4.12.0.88
-numpy==1.24.3
+numpy==1.26.4
-Pillow==10.1.0
+Pillow==12.0.0
```

**Raspberry-Pi/Client/requirements.txt:**
```diff
-requests==2.31.0
+requests==2.32.5
-gpiozero==2.0
+gpiozero==2.0.1
-Pillow==10.1.0
+Pillow==12.0.0
```

Then install:
```bash
pip install -r requirements.txt --upgrade
```

---

## ✅ Testing After Update

### Server Tests

1. **Start the server:**
   ```bash
   cd Server
   python app.py
   ```
   - Should start without errors
   - Check console for warnings

2. **Test face recognition:**
   - Trigger motion detection (ESP32 or Raspberry Pi)
   - Verify faces are detected
   - Check person recognition accuracy
   - Verify auto-learning works

3. **Test Web UI:**
   - Open http://localhost:5000
   - Check `/latest` page
   - Verify `/persons` page loads
   - Test person management (rename, merge)
   - Check `/config` page

4. **Test notifications:**
   - **Windows:** Trigger motion, verify Toast notification
   - **Linux:** Verify desktop notification appears

5. **Test MJPEG stream:**
   - Open http://localhost:5000/stream?token=YOUR_TOKEN
   - Verify stream works smoothly

### Raspberry Pi Client Tests

1. **Start the client:**
   ```bash
   cd Raspberry-Pi/Client
   python pir_cam_client.py
   ```

2. **Test PIR sensor:**
   - Trigger motion
   - Verify image captured
   - Check upload to server

3. **Test camera:**
   - Verify image quality
   - Check resolution settings

### Common Issues & Solutions

**Issue: "ImportError: cannot import name 'X' from 'Y'"**
- Solution: Clear pip cache and reinstall
  ```bash
  pip cache purge
  pip install -r requirements.txt --force-reinstall
  ```

**Issue: "Face recognition slower after update"**
- Check: OpenCV DNN backend settings
- Solution: May need to adjust config.yaml thresholds
- Benchmark: Run test captures and compare times

**Issue: "Numpy dtype warnings"**
- Expected: Some warnings from numpy 1.24 → 1.26 transition
- Solution: Update code if needed (see DEPENDENCY_AUDIT.md)

**Issue: "Pillow deprecation warnings"**
- Expected: Pillow 10 → 12 has some API changes
- Solution: Warnings are usually safe to ignore, but review logs

---

## 🔍 Verification Checklist

After updating, verify these features work:

### Server Checklist
- [ ] Server starts without errors
- [ ] Face detection works (YuNet model loads)
- [ ] Face recognition works (SFace embeddings)
- [ ] Person differentiation (Unknown → new person)
- [ ] Auto-learning adds samples
- [ ] Windows Toast notifications (Windows only)
- [ ] Linux desktop notifications (Linux only)
- [ ] Web UI loads all pages
- [ ] Image storage works
- [ ] Database queries work
- [ ] MJPEG streaming works
- [ ] Configuration updates save

### Raspberry Pi Client Checklist
- [ ] Client starts without errors
- [ ] PIR sensor triggers correctly
- [ ] Camera captures images
- [ ] Images upload to server
- [ ] Auth token works
- [ ] Device ID appears in logs
- [ ] Streaming works (if enabled)
- [ ] Config changes apply

### ESP32 Client Checklist
- [ ] No changes needed (no dependencies!)
- [ ] Can still upload to updated server
- [ ] Auth token still works

---

## 📊 Performance Benchmarks

Before and after updating, check these metrics:

### Face Recognition Performance
```bash
# In Server directory
python -c "
from face_recognition_cv import FaceRecognitionCV
import yaml
import time

with open('config.yaml') as f:
    config = yaml.safe_load(f)

face_rec = FaceRecognitionCV(config)

# Time a detection
from PIL import Image
img = Image.open('storage/latest.jpg')

start = time.time()
result = face_rec.process_image(img.tobytes(), 'test_device')
elapsed = time.time() - start

print(f'Processing time: {elapsed*1000:.0f}ms')
"
```

**Expected times:**
- Windows/Linux Desktop: 100-200ms
- Raspberry Pi 4: 400-500ms
- Raspberry Pi 5: 300-400ms

---

## 🔄 Rollback Plan

If you encounter critical issues:

### Quick Rollback

1. **Restore old requirements:**
   ```bash
   cd Server
   mv requirements.txt.old requirements.txt
   pip install -r requirements.txt --force-reinstall
   ```

2. **Restore data (if needed):**
   ```bash
   cp -r Server/data.backup/* Server/data/
   ```

3. **Restart services:**
   ```bash
   # Linux
   sudo systemctl restart motion-detector-server

   # Windows
   # Stop and start app.py manually
   ```

### Git Rollback

```bash
git checkout main
git branch -D dependency-updates
```

---

## 🚀 Production Deployment

After successful testing:

1. **Update production requirements:**
   ```bash
   # On production server
   cd /path/to/production
   git pull origin dependency-updates
   pip install -r Server/requirements.txt --upgrade
   ```

2. **Restart services:**
   ```bash
   # Linux systemd
   sudo systemctl restart motion-detector-server
   sudo systemctl restart motion-detector-client  # If using Pi client

   # Windows
   # Restart app.py manually or via service manager
   ```

3. **Monitor logs:**
   ```bash
   # Linux
   sudo journalctl -u motion-detector-server -f

   # Windows
   tail -f Server/motion_server.log
   ```

4. **Verify first detection:**
   - Trigger motion
   - Check notification
   - Verify face recognition
   - Check logs for errors

---

## 📅 Maintenance Schedule

Going forward:

1. **Weekly:** Check for security advisories
   ```bash
   pip-audit -r requirements.txt
   ```

2. **Monthly:** Review for outdated packages
   ```bash
   pip list --outdated
   ```

3. **Quarterly:** Major dependency updates
   - Test in development
   - Update production

---

## 🆘 Support

If you encounter issues:

1. Check [DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md) for detailed analysis
2. Review logs for error messages
3. Search existing GitHub issues
4. Open a new issue with:
   - Python version (`python --version`)
   - OS and version
   - Error messages
   - Steps to reproduce

---

## 📝 Summary

**What changed:**
- ✅ Fixed 10 security vulnerabilities
- ✅ Updated 6 outdated packages
- ✅ Improved performance (OpenCV, Flask)
- ✅ Maintained backward compatibility

**Time estimate:**
- Development update & test: 1-2 hours
- Production deployment: 15-30 minutes

**Risk level:**
- **Low** if using `.recommended` files
- **Medium** if using latest versions (numpy 2.x)

**Recommendation:**
- Use `.recommended` files for safe, tested updates
- Test thoroughly before production deployment
- Keep backups accessible for quick rollback

---

**Good luck with your updates!** 🎉
