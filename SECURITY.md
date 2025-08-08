# Security Guide for Dual Asset Bot

## ⚠️ API Key Security

### NEVER commit API keys to GitHub!

This project uses environment variables to store sensitive information. Follow these guidelines to keep your API keys safe:

## 1. Environment Configuration

### File Structure
- `.env` - Your actual configuration (NEVER commit this!)
- `.env.example` - Example configuration (safe to commit)
- `.gitignore` - Ensures .env is not tracked by git

### Setting Up Your Environment

1. **Copy the example file**:
```bash
cp .env.example .env
```

2. **Edit .env with your actual keys**:
```bash
# Edit .env file (this file is gitignored)
nano .env
```

## 2. API Key Types

### Testnet Keys (Safe for Testing)
- Used for testing without real money
- Get from: https://testnet.binance.vision/
- No real funds at risk
- Configure in `.env`:
```
BINANCE_TESTNET_API_KEY=your_testnet_key
BINANCE_TESTNET_API_SECRET=your_testnet_secret
```

### Production Keys (Handle with Care!)
- Used for real trading with real money
- Get from: https://www.binance.com/en/my/settings/api-management
- **Start with READ-ONLY permissions**
- Configure in `.env`:
```
BINANCE_PRODUCTION_API_KEY=your_production_key
BINANCE_PRODUCTION_API_SECRET=your_production_secret
```

## 3. Safety Features

### Demo Mode (Default)
```env
DEMO_MODE=True  # Simulates all trades
```

### Trade Limits
```env
MAX_TRADE_AMOUNT=10.0  # Maximum USDT per trade
TRADING_ENABLED=False  # Master switch for trading
```

### Environment Selection
```env
BINANCE_USE_TESTNET=True  # True for testnet, False for production
```

## 4. Best Practices

### API Key Permissions
1. **Start with READ-ONLY**: Test the system first
2. **Enable SPOT trading only**: Don't enable futures/margin
3. **Set IP restrictions**: Whitelist your server IP
4. **Enable 2FA**: On your Binance account

### Git Security
1. **Check before commit**:
```bash
git status  # Ensure .env is not listed
git diff    # Review changes before committing
```

2. **If you accidentally commit keys**:
```bash
# Remove from history immediately
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (coordinate with team)
git push --force --all
git push --force --tags

# IMMEDIATELY revoke the exposed keys in Binance!
```

## 5. Production Deployment

### Using Environment Variables
Instead of .env file, use system environment variables:

```bash
# Linux/Mac
export BINANCE_PRODUCTION_API_KEY="your_key"
export BINANCE_PRODUCTION_API_SECRET="your_secret"

# Or use a secrets manager like:
# - AWS Secrets Manager
# - HashiCorp Vault
# - Docker Secrets
# - Kubernetes Secrets
```

### Docker Deployment
```dockerfile
# Never add keys to Dockerfile!
# Pass them at runtime:
docker run -e BINANCE_PRODUCTION_API_KEY=$KEY -e BINANCE_PRODUCTION_API_SECRET=$SECRET your-image
```

## 6. Security Checklist

Before going to production:

- [ ] API keys are in .env (not in code)
- [ ] .env is in .gitignore
- [ ] No keys in git history
- [ ] Using separate keys for testnet/production
- [ ] Demo mode enabled for testing
- [ ] Trade limits configured
- [ ] API permissions minimized
- [ ] IP whitelist enabled
- [ ] 2FA enabled on Binance account
- [ ] Regular key rotation planned

## 7. Monitoring

### Log Security
- API keys are never logged
- Sensitive data is masked in logs
- Monitor for unauthorized access

### Alerts
Set up alerts for:
- Large trades
- Multiple failed API calls
- Unusual trading patterns

## Emergency Procedures

If keys are compromised:
1. **Immediately revoke keys** in Binance settings
2. Generate new keys
3. Update .env with new keys
4. Review account for unauthorized trades
5. Enable additional security measures

## Support

For security concerns, please:
- DO NOT post keys in issues
- DO NOT share keys via email
- Use secure channels for sensitive discussions

Remember: **Your API keys are like passwords - keep them secret!**