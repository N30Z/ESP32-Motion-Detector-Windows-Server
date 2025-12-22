# ⚠️ DIRECTORY MOVED

**This directory has been moved in repository restructure v2.0.0**

## New Location

**👉 [../../Raspberry-Pi/Client/](../../Raspberry-Pi/Client/)**

All Raspberry Pi client code has been moved to `Raspberry-Pi/Client/`.

## What Changed?

The repository was restructured by platform:
- `clients/raspi/` → `Raspberry-Pi/Client/`
- New platform structure with multiple modes:
  - `Raspberry-Pi/Client/` - Camera client
  - `Raspberry-Pi/Server/` - Server on Pi
  - `Raspberry-Pi/Standalone/` - All-in-one setup (NEW!)

## Migration

**Update your commands:**
```bash
# OLD
cd clients/raspi

# NEW
cd Raspberry-Pi/Client
```

**Update systemd service paths** (if installed):
```bash
sudo nano /etc/systemd/system/motion-detector-client.service
# Update WorkingDirectory to new path
```

## More Information

- **Changelog:** [../../CHANGELOG.md](../../CHANGELOG.md)
- **Raspberry Pi Guide:** [../../Raspberry-Pi/Raspberry.md](../../Raspberry-Pi/Raspberry.md)
- **Client Documentation:** [../../Raspberry-Pi/Client/README.md](../../Raspberry-Pi/Client/README.md)
- **Standalone Mode:** [../../Raspberry-Pi/Standalone/README.md](../../Raspberry-Pi/Standalone/README.md) (NEW!)

---

**Last Updated:** 2025-12-22
