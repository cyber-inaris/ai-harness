namespace AccountRegistration.Email;

public sealed class EmailCodeReader(IEmailMessageSource messageSource, ISystemClock clock) : IEmailCodeReader
{
    public async Task<EmailCodeResult> WaitForCodeAsync(
        EmailCodeRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);

        var since = clock.UtcNow.Subtract(request.Lookback);
        var messages = await messageSource.GetRecentMessagesAsync(request, since, cancellationToken);

        foreach (var message in messages
                     .Where(message => IsCandidate(message, request, since))
                     .OrderByDescending(message => message.ReceivedAt))
        {
            var result = EmailCodeExtractor.TryExtract(message.BodyText, request);
            if (result.Found)
            {
                return result with
                {
                    SourceSubject = message.Subject,
                    ReceivedAt = message.ReceivedAt
                };
            }
        }

        return EmailCodeResult.NotFound;
    }

    private static bool IsCandidate(EmailMessageCandidate message, EmailCodeRequest request, DateTimeOffset since)
    {
        if (message.ReceivedAt < since)
        {
            return false;
        }

        if (!message.To.Equals(request.Recipient, StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        return string.IsNullOrWhiteSpace(request.SubjectContains) ||
               message.Subject.Contains(request.SubjectContains, StringComparison.OrdinalIgnoreCase);
    }
}
