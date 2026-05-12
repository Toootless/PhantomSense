# Security Policy

## WiFi Credentials Protection

⚠️ **CRITICAL:** WiFi credentials must never be committed to GitHub.

### What's Protected

```
main/app_config.c  ← GITIGNORED - Contains WiFi password
.env               ← GITIGNORED - Environment variables
```

These files are **automatically excluded** by `.gitignore` and will not be committed even if you try.

### How to Configure

1. **Copy the example:**
   ```bash
   cp main/app_config.c.example main/app_config.c
   ```

2. **Edit with your credentials:**
   ```bash
   code main/app_config.c
   ```
   ```c
   .wifi_ssid = "YOUR_SSID",
   .wifi_password = "YOUR_PASSWORD",
   .hub_url = "http://YOUR_HUB_IP:5000",
   ```

3. **Git will ignore this file:**
   ```bash
   git status
   # On branch main
   # nothing to commit, working tree clean
   ```

## DO's ✅

- ✅ **DO** copy `app_config.c.example` to `app_config.c`
- ✅ **DO** edit your local copy with real credentials
- ✅ **DO** commit `app_config.c.example` (template)
- ✅ **DO** add new template entries to `app_config.c.example`
- ✅ **DO** verify gitignore before pushing:
  ```bash
  git status main/
  # Should show nothing if credentials are ignored
  ```
- ✅ **DO** update documentation when configuration changes

## DON'Ts ❌

- ❌ **DON'T** commit `main/app_config.c` (will be rejected by .gitignore)
- ❌ **DON'T** manually `git add main/app_config.c` (forced add)
- ❌ **DON'T** commit WiFi credentials in any form
- ❌ **DON'T** push `.env` files with real values
- ❌ **DON'T** paste credentials into commit messages
- ❌ **DON'T** leave credentials in old git history (use `git filter-branch`)
- ❌ **DON'T** share `app_config.c` between team members

## If Credentials Are Exposed

**If you accidentally commit credentials:**

1. **IMMEDIATELY revoke credentials** (change WiFi password)
2. **Remove from git history:**
   ```bash
   git filter-branch --tree-filter 'rm -f main/app_config.c' HEAD
   git push origin --force
   ```
3. **Force push to all branches:**
   ```bash
   git push --all --force
   ```
4. **Update .gitignore if needed**
5. **Notify team members**

⚠️ **This cannot fully remove data from GitHub's history - always assume exposed credentials are compromised.**

## Configuration Structure

### main/app_config.c (UNTRACKED)
```c
// 🔐 SENSITIVE - Your actual WiFi credentials
.wifi_ssid = "DrWho",
.wifi_password = "Mollymay2212",
.hub_url = "http://10.0.0.84:5000",
```

### main/app_config.c.example (TRACKED)
```c
// 📄 TEMPLATE - Safe to commit
.wifi_ssid = "YOUR_SSID_HERE",
.wifi_password = "YOUR_PASSWORD_HERE",
.hub_url = "http://10.0.0.84:5000",
```

### main/app_config.h (TRACKED)
```c
// 📋 TYPE DEFINITIONS - No sensitive data
typedef struct {
    uint8_t unit_id;
    const char* unit_name;
    const char* wifi_ssid;
    const char* wifi_password;
    ...
} app_config_t;
```

## Git Verification

### Before pushing, check:

```bash
# See what would be committed
git status

# Ensure no config files appear
git diff --cached main/app_config.c

# Show ignored files
git check-ignore main/app_config.c
# Output: main/app_config.c (should show "ignored")
```

### View .gitignore rules:

```bash
cat .gitignore
# Should include:
# main/app_config.c
# .env
# .env.local
```

## Team Collaboration

### For New Team Members

1. Clone repository
2. Copy example: `cp main/app_config.c.example main/app_config.c`
3. Edit with their network credentials
4. Build and deploy
5. **Their credentials are never tracked or shared**

### For Maintainers

When updating configuration structure:
1. Update `main/app_config.c.example` with new fields
2. Include clear placeholder comments
3. Commit the example (safe)
4. **DO NOT** commit actual configs
5. Update `SETUP.md` with instructions

## Environment Variables

Future support for `.env` files:

```bash
# .env.example (TRACKED)
WIFI_SSID=YOUR_NETWORK
WIFI_PASSWORD=YOUR_PASSWORD
HUB_IP=192.168.1.100

# .env (UNTRACKED - local only)
WIFI_SSID=MyNetwork
WIFI_PASSWORD=MyActualPassword
HUB_IP=192.168.1.42
```

## Planned Improvements

- [ ] Migrate to ESP-IDF menuconfig (interactive config)
- [ ] Use NVS storage for runtime configuration
- [ ] Add OTA WiFi provisioning
- [ ] Support encrypted NVS partition
- [ ] Implement secure credential rotation

## Related Files

- `.gitignore` - File exclusion rules
- `main/app_config.c.example` - Configuration template
- `SETUP.md` - Onboarding guide
- `README.md` - Main documentation

## Security Contacts

Report security issues through:
- GitHub Security Advisory (Private)
- Email: [maintainer@example.com] (configure this)

## References

- [GitHub - Removing Sensitive Data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [OWASP - Credential Storage](https://owasp.org/www-community/vulnerabilities/Storing_Secrets_in_Source_Code)
- [ESP-IDF - NVS Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/storage/nvs_flash.html)
