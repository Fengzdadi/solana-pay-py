# Solana Pay Specification Reference

This document provides references to the official Solana Pay specifications and related documentation that guide this Python implementation.

## Official Specifications

### Solana Pay Specification
- **URL**: https://github.com/solana-foundation/solana-pay/blob/master/SPEC.md
- **Version**: 1.1
- **Description**: The official Solana Pay specification defining URL formats, transaction request protocols, and validation requirements.

### Key Specification Points

#### Transfer URLs (solana: scheme)
- Format: `solana:<recipient>?<params>`
- Required: `recipient` (base58 public key)
- Optional: `amount`, `spl-token`, `reference`, `label`, `message`, `memo`
- Reference ordering must be preserved
- Amount must use decimal format (no scientific notation)

#### Transaction Request URLs (https: scheme)
- Format: `https://<domain>/path?<params>`
- Used for dynamic transaction generation
- GET `/tx` returns metadata (`label`, `icon`)
- POST `/tx` with `account` returns serialized transaction

#### Reference Accounts
- Used for transaction identification and validation
- Must be included as additional signers in transactions
- Order is significant and must be preserved
- Typically used for payment tracking and reconciliation

## Message Signing Specification

### Solana Wallet Message Signing
- **URL**: https://github.com/solana-foundation/wallet-adapter/blob/master/packages/core/base/src/signer.ts
- **Description**: Specification for wallet message signing used in transaction requests

## Related Documentation

### Solana Cookbook
- **URL**: https://solanacookbook.com/
- **Relevant Sections**:
  - [Sending SOL](https://solanacookbook.com/references/basic-transactions.html#how-to-send-sol)
  - [Sending SPL Tokens](https://solanacookbook.com/references/token.html#how-to-transfer-tokens)
  - [Adding Memos](https://solanacookbook.com/references/basic-transactions.html#how-to-add-a-memo-to-a-transaction)
  - [Getting Transaction Details](https://solanacookbook.com/references/basic-transactions.html#how-to-get-transaction-details)

### Solana Python SDK Documentation
- **URL**: https://michaelhly.com/solana-py/
- **Key Components**:
  - AsyncClient for RPC operations
  - Transaction building and signing
  - Account and public key handling

## Implementation Guidelines

### SPEC Compliance Requirements

1. **URL Format Compliance**
   - Use exact field names as specified (`spl-token`, not `spl_token`)
   - Preserve reference parameter ordering
   - Use proper URL encoding for special characters
   - Support both `solana:` and `https:` schemes

2. **Transaction Building**
   - Use versioned transactions (v0) for better compatibility
   - Include reference accounts as additional signers
   - Handle Associated Token Account creation automatically
   - Support memo instructions for payment tracking

3. **Validation Requirements**
   - Verify recipient matches expected value
   - Validate amount precision and token mint
   - Check reference accounts are correctly included
   - Confirm memo content matches expected value

4. **Error Handling**
   - Provide descriptive error messages for validation failures
   - Distinguish between network, RPC, and validation errors
   - Handle edge cases gracefully (missing ATAs, insufficient funds)

### Interoperability Considerations

1. **JavaScript Ecosystem Compatibility**
   - Field naming must match JavaScript implementation
   - URL encoding behavior must be identical
   - Transaction format must be compatible with JS wallets

2. **Wallet Compatibility**
   - Support major wallets (Phantom, Solflare, Backpack)
   - Follow wallet-adapter patterns for transaction requests
   - Handle wallet-specific quirks and requirements

3. **Network Considerations**
   - Support all Solana clusters (devnet, testnet, mainnet)
   - Handle RPC rate limiting and connection pooling
   - Implement proper retry logic for network failures

## Version History

- **v1.0**: Initial Solana Pay specification
- **v1.1**: Added support for multiple references and enhanced validation

## Testing Against Specification

### Test Vectors
The implementation should be tested against official test vectors and real-world scenarios:

1. **URL Encoding/Parsing**: Test with various parameter combinations
2. **Transaction Building**: Verify against known good transactions
3. **Wallet Integration**: Test with actual wallet applications
4. **Edge Cases**: Handle malformed inputs and network errors

### Compliance Checklist
- [ ] URL format matches specification exactly
- [ ] Reference ordering is preserved
- [ ] Amount formatting uses decimal notation
- [ ] Transaction structure is compatible with wallets
- [ ] Error messages are descriptive and actionable
- [ ] All optional parameters are handled correctly