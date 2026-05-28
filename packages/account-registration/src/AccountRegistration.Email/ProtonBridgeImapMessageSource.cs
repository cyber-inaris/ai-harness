using MailKit;
using MailKit.Net.Imap;
using MailKit.Search;
using MailKit.Security;
using MimeKit;

namespace AccountRegistration.Email;

public sealed class ProtonBridgeImapMessageSource(ProtonBridgeImapOptions options) : IEmailMessageSource
{
    public async Task<IReadOnlyList<EmailMessageCandidate>> GetRecentMessagesAsync(
        EmailCodeRequest request,
        DateTimeOffset since,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        options.Validate();

        using var client = new ImapClient();
        if (options.AllowInvalidServerCertificate)
        {
            client.ServerCertificateValidationCallback = (_, _, _, _) => true;
        }

        await client.ConnectAsync(
            options.Host,
            options.Port,
            GetSecureSocketOptions(options),
            cancellationToken);

        await client.AuthenticateAsync(options.UserName, options.Password, cancellationToken);

        var inbox = client.Inbox;
        await inbox.OpenAsync(FolderAccess.ReadOnly, cancellationToken);

        SearchQuery query = SearchQuery.DeliveredAfter(since.UtcDateTime);
        if (!string.IsNullOrWhiteSpace(request.SubjectContains))
        {
            query = query.And(SearchQuery.SubjectContains(request.SubjectContains));
        }

        var uids = await inbox.SearchAsync(query, cancellationToken);
        var messages = new List<EmailMessageCandidate>(uids.Count);

        foreach (var uid in uids)
        {
            var message = await inbox.GetMessageAsync(uid, cancellationToken);
            messages.Add(ToCandidate(message, request.Recipient));
        }

        await client.DisconnectAsync(true, cancellationToken);
        return messages;
    }

    private static SecureSocketOptions GetSecureSocketOptions(ProtonBridgeImapOptions options)
    {
        if (options.UseSsl)
        {
            return SecureSocketOptions.SslOnConnect;
        }

        return options.UseStartTlsWhenAvailable
            ? SecureSocketOptions.StartTlsWhenAvailable
            : SecureSocketOptions.None;
    }

    private static EmailMessageCandidate ToCandidate(MimeMessage message, string recipient)
        => new(
            Subject: message.Subject ?? string.Empty,
            To: PickRecipient(message, recipient),
            ReceivedAt: message.Date,
            BodyText: message.TextBody ?? message.HtmlBody ?? string.Empty);

    private static string PickRecipient(MimeMessage message, string requestedRecipient)
    {
        var mailbox = message.To.Mailboxes.FirstOrDefault(mailbox =>
            mailbox.Address.Equals(requestedRecipient, StringComparison.OrdinalIgnoreCase));

        return mailbox?.Address ?? requestedRecipient;
    }
}
