namespace AccountRegistration.Email.Tests;

using AccountRegistration.Email;

public sealed class EmailCodeReaderTests
{
    [Fact]
    public async Task WaitForCodeAsync_ReturnsNewestMatchingCode_FromMessageSource()
    {
        var now = new DateTimeOffset(2026, 5, 27, 12, 0, 0, TimeSpan.Zero);
        var source = new StubEmailMessageSource(
        [
            new EmailMessageCandidate(
                Subject: "FreeModel verification",
                To: "relay@example.com",
                ReceivedAt: now.AddMinutes(-10),
                BodyText: "Old code 111111"),
            new EmailMessageCandidate(
                Subject: "FreeModel verification",
                To: "relay@example.com",
                ReceivedAt: now.AddMinutes(-1),
                BodyText: "New code 222222"),
            new EmailMessageCandidate(
                Subject: "Other verification",
                To: "relay@example.com",
                ReceivedAt: now,
                BodyText: "Wrong subject 333333")
        ]);

        var reader = new EmailCodeReader(source, new FakeClock(now));
        var request = new EmailCodeRequest(
            Provider: "freemodel",
            Recipient: "relay@example.com",
            SubjectContains: "FreeModel",
            CodePattern: null,
            Lookback: TimeSpan.FromMinutes(30));

        var result = await reader.WaitForCodeAsync(request, CancellationToken.None);

        Assert.True(result.Found);
        Assert.Equal("222222", result.Code);
        Assert.Equal("FreeModel verification", result.SourceSubject);
        Assert.Equal(now.AddMinutes(-1), result.ReceivedAt);
    }

    [Fact]
    public async Task WaitForCodeAsync_ReturnsNotFound_WhenMessagesAreOlderThanLookback()
    {
        var now = new DateTimeOffset(2026, 5, 27, 12, 0, 0, TimeSpan.Zero);
        var source = new StubEmailMessageSource(
        [
            new EmailMessageCandidate(
                Subject: "FreeModel verification",
                To: "relay@example.com",
                ReceivedAt: now.AddHours(-2),
                BodyText: "Code 123456")
        ]);

        var reader = new EmailCodeReader(source, new FakeClock(now));
        var request = new EmailCodeRequest(
            Provider: "freemodel",
            Recipient: "relay@example.com",
            SubjectContains: "FreeModel",
            CodePattern: null,
            Lookback: TimeSpan.FromMinutes(30));

        var result = await reader.WaitForCodeAsync(request, CancellationToken.None);

        Assert.False(result.Found);
    }

    private sealed class StubEmailMessageSource(IReadOnlyList<EmailMessageCandidate> messages) : IEmailMessageSource
    {
        public Task<IReadOnlyList<EmailMessageCandidate>> GetRecentMessagesAsync(
            EmailCodeRequest request,
            DateTimeOffset since,
            CancellationToken cancellationToken)
        {
            return Task.FromResult(messages);
        }
    }

    private sealed class FakeClock(DateTimeOffset utcNow) : ISystemClock
    {
        public DateTimeOffset UtcNow => utcNow;
    }
}
