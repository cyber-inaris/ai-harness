namespace AccountRegistration.Email;

public sealed record EmailCodeResult(
    bool Found,
    string? Code,
    string? SourceSubject,
    DateTimeOffset? ReceivedAt)
{
    public static EmailCodeResult NotFound { get; } = new(false, null, null, null);

    public static EmailCodeResult FromCode(string code, string? sourceSubject = null, DateTimeOffset? receivedAt = null)
        => new(true, code, sourceSubject, receivedAt);
}
