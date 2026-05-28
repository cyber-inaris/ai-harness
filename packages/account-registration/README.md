# Account Registration

C# automation modules for owned-account registration flows.

The first module is `AccountRegistration.Email`, which reads verification codes
from IMAP sources. Proton Mail Bridge remains supported as a fallback for paid
Proton accounts, but free Proton accounts should use browser automation.

## Proton Bridge IMAP

Status: fallback only.

Proton Bridge is available only to Proton Mail users with a paid plan. The
server login check for `ss.magic.admin@proton.me` returned:

```text
Please upgrade to a paid plan to use this client
```

Do not build the default verification path around Bridge while the mailbox is on
a free Proton plan.

Proton Bridge must be running locally. In the Bridge app, copy the mailbox
username and mailbox password shown for the account. Do not use the normal
Proton account password.

Default Bridge ports:

- IMAP: `127.0.0.1:1143`
- SMTP: `127.0.0.1:1025`

Minimal usage:

```csharp
using AccountRegistration.Email;

var options = ProtonBridgeImapOptions.DefaultLocal(
    userName: "<bridge-mailbox-username>",
    password: "<bridge-mailbox-password>");

var source = new ProtonBridgeImapMessageSource(options);
var reader = new EmailCodeReader(source, new SystemClock());

var result = await reader.WaitForCodeAsync(
    new EmailCodeRequest(
        Provider: "freemodel",
        Recipient: "relay@example.com",
        SubjectContains: "FreeModel",
        CodePattern: null,
        Lookback: TimeSpan.FromMinutes(30)),
    cancellationToken);

if (result.Found)
{
    Console.WriteLine($"Code: {result.Code}");
}
```

For provider-specific email formats, set `CodePattern` and put the code in the
first capture group:

```csharp
CodePattern: @"FM-(\d{4})"
```

## Verification: Email / Proton Bridge

Use this checklist when wiring account-registration automation to Proton relay
mailboxes through Bridge. Run it only after confirming that the Proton account
has a paid plan.

### 1. Proton Bridge is running

Bridge is a local IMAP/SMTP service, so it must run on the same machine as the
reader process.

```bash
ss -ltnp | grep -E ':(1143|1025)\b'
```

Expected result:

```text
127.0.0.1:1143  IMAP
127.0.0.1:1025  SMTP
```

If the ports are missing, start Proton Mail Bridge under the same desktop/user
session that owns the Proton login.

### 2. Bridge credentials are configured

Copy the mailbox username and mailbox password from Proton Bridge. Do not use
the normal Proton account password.

Recommended local secret file:

```bash
/opt/ai-harness/secrets/proton-bridge.env
```

Expected variables:

```bash
PROTON_BRIDGE_HOST=127.0.0.1
PROTON_BRIDGE_IMAP_PORT=1143
PROTON_BRIDGE_USER=<bridge-mailbox-username>
PROTON_BRIDGE_PASSWORD=<bridge-mailbox-password>
```

Keep this file mode `600` and never commit it.

### 3. A test verification email exists

Trigger a real registration or resend-code action to a relay address that
forwards into the Proton mailbox.

Record:

```text
recipient: relay address used during registration
subject hint: stable word from the provider email, for example FreeModel
lookback: 15-30 minutes
code pattern: optional provider regex, for example FM-(\d{4})
```

### 4. Reader smoke test

Until a dedicated CLI is added, use the C# module from a small harness or the
registration worker:

```csharp
var options = new ProtonBridgeImapOptions
{
    Host = Environment.GetEnvironmentVariable("PROTON_BRIDGE_HOST") ?? "127.0.0.1",
    Port = int.Parse(Environment.GetEnvironmentVariable("PROTON_BRIDGE_IMAP_PORT") ?? "1143"),
    UserName = Environment.GetEnvironmentVariable("PROTON_BRIDGE_USER")
        ?? throw new InvalidOperationException("PROTON_BRIDGE_USER is required."),
    Password = Environment.GetEnvironmentVariable("PROTON_BRIDGE_PASSWORD")
        ?? throw new InvalidOperationException("PROTON_BRIDGE_PASSWORD is required.")
};

var reader = new EmailCodeReader(
    new ProtonBridgeImapMessageSource(options),
    new SystemClock());

var result = await reader.WaitForCodeAsync(
    new EmailCodeRequest(
        Provider: "freemodel",
        Recipient: "relay@example.com",
        SubjectContains: "FreeModel",
        CodePattern: null,
        Lookback: TimeSpan.FromMinutes(30)),
    cancellationToken);

Console.WriteLine(result.Found ? result.Code : "not found");
```

Expected pass condition:

```text
Found=true
Code=<verification code from the newest matching email>
SourceSubject=<provider email subject>
ReceivedAt=<recent timestamp>
```

Failure checks:

- `Please upgrade to a paid plan to use this client`: the Proton account is on a
  free plan; switch to browser automation or upgrade the account.
- `Authentication failed`: credentials are not the Bridge mailbox credentials.
- `Connection refused`: Bridge is not running or not listening on the expected
  host/port.
- `not found`: recipient, subject hint, lookback, or provider regex does not
  match the actual email.

## Verification: Email / Proton Browser

Use browser automation for free Proton accounts. The browser path logs into
Proton Web, searches the mailbox, opens the newest matching verification email,
and extracts the code from the rendered message.

Recommended agent browser:

```text
Camofox Browser: https://github.com/jo-inc/camofox-browser
```

Why this path:

- Works with Proton Web instead of IMAP/SMTP Bridge.
- Can reuse browser cookies/session storage after a manual login.
- Supports proxy and isolated sessions for account-registration workers.
- Gives agents compact accessibility snapshots and stable element references.

Smoke-test flow:

```text
1. Start the Camofox browser service on localhost.
2. Open https://mail.proton.me/u/0/inbox.
3. Log in once through the interactive browser/VNC path.
4. Persist cookies/session storage for the Proton mailbox.
5. Trigger a test verification email to the relay address.
6. Search Proton Web for the provider subject hint, for example FreeModel.
7. Open the newest matching email.
8. Extract a 6-digit code or the provider-specific regex.
```

Expected pass condition:

```text
Found=true
Code=<verification code from newest matching rendered email>
Source=proton-web
```

Failure checks:

- Login page appears again: browser session storage was not persisted or expired.
- Search returns no messages: relay address, subject hint, or lookback window is
  wrong.
- Provider page blocks automation: use the Camofox session with proxy/cookies
  instead of standard headless Playwright.

## Tests

```bash
dotnet test packages/account-registration/AccountRegistration.sln
```
