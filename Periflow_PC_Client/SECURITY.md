# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in Periflow, please email [security@example.com](mailto:security@example.com) instead of using the public issue tracker.

**Please do not publicly disclose security vulnerabilities until we have had a chance to address them.**

Include the following information:
- Type of vulnerability (e.g., authentication bypass, code injection)
- Detailed description with proof-of-concept
- Affected version(s)
- Steps to reproduce
- Potential impact
- Any suggested fixes or mitigations

## Security Considerations

### Design Scope

Periflow is **designed for trusted local networks only**:
- ✅ **Safe:** Home Wi-Fi, office networks where devices are managed
- ❌ **Unsafe:** Public Wi-Fi, internet-exposed ports, untrusted networks

### Current Security Model

**Authentication:**
- Simple token-based handshake (`PERIFLOW_CONNECT`)
- Assumes all network devices are trusted
- No user/password authentication

**Transport:**
- TCP for control messages (unencrypted, LAN-only)
- UDP for audio streaming (unencrypted, LAN-only)
- Relies on network isolation (no internet exposure)

**Access Control:**
- Single active client per server
- Connection from any LAN device accepted
- No device pairing or whitelist

### Known Limitations

1. **No Authentication** - Any device on LAN can connect
2. **No Encryption** - Messages sent in plaintext (LAN isolation assumed)
3. **No Rate Limiting** - No throttling on input events
4. **No Message Signing** - No verification of message authenticity
5. **Single Client** - No multi-user support

### Recommended Usage

1. **Private Networks Only:**
   - Use only on Wi-Fi networks you control and trust
   - Disable Periflow on public/shared networks
   - Use a separate guest network if available

2. **Local Network Isolation:**
   - Ensure Windows Firewall is enabled
   - Do not port forward 5000 or 5001 to the internet
   - Consider additional network segmentation

3. **Physical Security:**
   - Don't leave device unattended with active Periflow session
   - Keep phone physically secured
   - Use device lock screen when not in use

4. **Monitoring:**
   - Check Periflow logs for unexpected connections
   - Monitor network for suspicious devices
   - Verify only expected devices are connecting

### Security Roadmap

We are planning the following security enhancements:

- [ ] **PIN-based Pairing** - PIN code confirmation for new devices
- [ ] **Device Fingerprinting** - Remember trusted devices
- [ ] **Message Signing** - HMAC for message verification
- [ ] **Rate Limiting** - Throttle input events
- [ ] **Connection Timeout** - Auto-disconnect on inactivity
- [ ] **TLS Encryption** - Optional encryption for LAN
- [ ] **User Authentication** - Basic username/password (for future)
- [ ] **Audit Logging** - Detailed connection/access logs

## Best Practices

### For Users

1. **Verify Your Network:**
   - Only connect on private, trusted networks
   - Ask your network admin if unsure

2. **Monitor Activity:**
   - Check Periflow client endpoint regularly
   - Watch for unexpected IP addresses
   - Review server logs for anomalies

3. **Disable When Not Needed:**
   - Stop the server when not using remote control
   - Close Periflow when leaving your desk

4. **Keep Updated:**
   - Update to the latest version promptly
   - Review changelog for security fixes

### For Developers

1. **Input Validation:**
   - Validate all message metadata
   - Sanitize mouse coordinates
   - Limit text input length

2. **Resource Management:**
   - Prevent memory leaks in long-running services
   - Clean up connections properly
   - Implement timeouts for all operations

3. **Error Handling:**
   - Don't expose sensitive info in error messages
   - Log security-relevant events
   - Handle malformed input gracefully

4. **Testing:**
   - Test with invalid/malicious input
   - Test resource exhaustion scenarios
   - Verify firewall integration works

## Version Support

| Version | Supported | EOL Date |
|---------|-----------|----------|
| 1.0.x   | ✅        | TBD      |

## Compliance

This project follows responsible disclosure practices. We aim to:
1. Acknowledge vulnerability reports within 48 hours
2. Provide updates on our investigation
3. Release patches for confirmed vulnerabilities
4. Credit researchers (if desired)

## References

- [OWASP](https://owasp.org/)
- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)
- [Windows Security Best Practices](https://docs.microsoft.com/en-us/windows/)

---

**Thank you for helping keep Periflow secure!**
