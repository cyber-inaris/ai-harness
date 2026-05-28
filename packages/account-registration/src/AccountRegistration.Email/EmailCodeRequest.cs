namespace AccountRegistration.Email;

public sealed record EmailCodeRequest(
    string Provider,
    string Recipient,
    string? SubjectContains,
    string? CodePattern,
    TimeSpan Lookback);
