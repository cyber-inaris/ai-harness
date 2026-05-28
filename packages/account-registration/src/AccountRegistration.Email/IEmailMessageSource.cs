namespace AccountRegistration.Email;

public interface IEmailMessageSource
{
    Task<IReadOnlyList<EmailMessageCandidate>> GetRecentMessagesAsync(
        EmailCodeRequest request,
        DateTimeOffset since,
        CancellationToken cancellationToken);
}
