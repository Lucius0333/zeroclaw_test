# GitHub Activity Tracker

A Python-based tool to track GitHub repository activity and generate cryptocurrency wallet addresses.

## Features
- Repository information tracking
- Activity report generation
- **Wallet Address Generator** - Generate multiple cryptocurrency wallet addresses
  - Ethereum-style addresses
  - Bitcoin testnet addresses
  - Solana testnet addresses
  - Batch generation
  - Secure private key generation (256-bit)
  - JSON-based storage with public address export
  - Statistics and reporting

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GitHub token
```

## Usage

### GitHub Tracker
```bash
python main.py
```

### Wallet Generator
```bash
# Generate 5 Ethereum wallets
python -m src.wallet_generator --count 5 --chain ethereum

# Generate 3 wallets for each supported chain
python -m src.wallet_generator --count 3 --multi-chain

# View statistics
python -m src.wallet_generator --stats

# Export public addresses only
python -m src.wallet_generator --export
```

## Testing
```bash
python -m pytest tests/
```

## Project Structure
```
├── src/
│   ├── __init__.py
│   ├── github_tracker.py
│   └── wallet_generator.py
├── tests/
│   ├── __init__.py
│   ├── test_tracker.py
│   └── test_wallet_generator.py
├── main.py
├── requirements.txt
└── README.md
```

## Wallet Generation Algorithm

1. **Private Key Generation**: Uses `secrets.token_hex(32)` for cryptographically secure 256-bit keys
2. **Address Derivation**:
   - **Ethereum**: SHA-256 hash → last 20 bytes → `0x` prefix
   - **Bitcoin Testnet**: SHA-256 hash → hex encoding → `m`/`n` prefix
   - **Solana Testnet**: SHA-256 hash → hex encoding → `So1` prefix
3. **Storage**: All wallets stored in `data/wallets/generated_wallets.json`
4. **Export**: Public addresses can be exported separately (no private keys)

## Security Notes
- Private keys are stored locally in JSON format
- Use `--export` to get public addresses only for sharing
- In production, consider encrypted storage or hardware security modules
