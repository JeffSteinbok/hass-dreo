# Login Issue Investigation Summary

## Issue
Users reported login failures with error messages:
- "No response from API"
- "Error logging in with username and password"

Suspected issue: Special characters in passwords might cause authentication failures.

## Investigation Results

### Password Handling
✅ **VERIFIED WORKING**: Password hashing with special characters works correctly:
- Passwords are MD5-hashed before being sent to the API
- The `hash_password()` function in `helpers.py` correctly handles:
  - Special characters (@, !, &, =, ?, #, +, %, /)
  - Quotes (single and double)
  - Backslashes
  - Unicode characters (Cyrillic, Chinese, Japanese, emoji)

### Username (Email) Handling
✅ **VERIFIED WORKING**: Email addresses with special characters are handled correctly:
- Email is inserted directly into JSON body
- The `requests` library's JSON encoding properly escapes all special characters
- Tested with: +, ., -, quotes, Unicode characters

### Tests Added
Added comprehensive tests in `tests/pydreo/test_helpers.py`:
- `test_hash_password_simple` - Basic password hashing
- `test_hash_password_with_special_characters` - Common special chars
- `test_hash_password_with_quotes_and_backslashes` - JSON-problematic chars
- `test_hash_password_with_unicode` - International characters
- `test_hash_password_empty_string` - Edge case
- `test_hash_password_consistency` - Reproducibility

All tests pass successfully.

## Root Cause Analysis

The actual issue is **NOT** special characters in credentials, but rather:

### 1. Poor Error Logging
**Before fix:**
- Network failures only logged at DEBUG level
- Non-200 status codes only logged at DEBUG level
- Generic error messages that don't indicate root cause

**After fix:**
- Network failures logged at ERROR level with exception details
- Non-200 status codes logged at ERROR level with status code
- Login failures now show API error code and message

### 2. Debug Print Statement
- Line 56 in `helpers.py` had `print(body)` which exposed credentials to stdout
- **REMOVED** in this fix

## Changes Made

1. **Improved error logging in `helpers.py`:**
   - RequestException now logs at ERROR level
   - Non-200 responses log at ERROR level with status code

2. **Improved error reporting in `__init__.py` login function:**
   - Check for None response and provide specific error
   - Extract API error code and message from response
   - Provide actionable error messages

3. **Removed debug print statement** that exposed credentials

4. **Added comprehensive tests** for special character handling

## Recommendations for Users

If you're experiencing login issues:

1. **Enable debug logging** as described in the README
2. Check the logs for:
   - Network connectivity issues
   - API status codes (401 = bad credentials, 403 = forbidden, 500 = server error)
   - API error messages with specific error codes
3. Verify you can reach the Dreo API endpoint from your Home Assistant instance
4. Try the `test_basic` script from the repo to test credentials outside of Home Assistant

## Conclusion

Special characters in usernames and passwords are **NOT** the cause of login failures. The authentication code properly handles all special characters through MD5 hashing (for passwords) and JSON encoding (for both username and password).

The improved error logging will help diagnose the actual cause of login failures, which is likely:
- Network connectivity issues
- Wrong credentials
- API server problems
- Regional server misconfiguration
