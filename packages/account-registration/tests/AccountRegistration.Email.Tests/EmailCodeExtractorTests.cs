namespace AccountRegistration.Email.Tests;

using AccountRegistration.Email;

public sealed class EmailCodeExtractorTests
{
    [Theory]
    [InlineData("Your FreeModel verification code is 123456.", "123456")]
    [InlineData("Use code: 847 219 to continue.", "847219")]
    [InlineData("Код подтверждения: 004-912. Никому его не сообщайте.", "004912")]
    public void TryExtract_ReturnsSixDigitCode_WhenBodyContainsVerificationCode(string body, string expected)
    {
        var request = new EmailCodeRequest(
            Provider: "freemodel",
            Recipient: "relay@example.com",
            SubjectContains: "verification",
            CodePattern: null,
            Lookback: TimeSpan.FromMinutes(30));

        var result = EmailCodeExtractor.TryExtract(body, request);

        Assert.True(result.Found);
        Assert.Equal(expected, result.Code);
    }

    [Fact]
    public void TryExtract_UsesProviderSpecificPattern_WhenPatternIsConfigured()
    {
        var request = new EmailCodeRequest(
            Provider: "freemodel",
            Recipient: "relay@example.com",
            SubjectContains: "FreeModel",
            CodePattern: @"FM-(\d{4})",
            Lookback: TimeSpan.FromMinutes(30));

        var result = EmailCodeExtractor.TryExtract("FreeModel login token: FM-7319", request);

        Assert.True(result.Found);
        Assert.Equal("7319", result.Code);
    }

    [Fact]
    public void TryExtract_ReturnsNotFound_WhenNoCodeExists()
    {
        var request = new EmailCodeRequest(
            Provider: "freemodel",
            Recipient: "relay@example.com",
            SubjectContains: null,
            CodePattern: null,
            Lookback: TimeSpan.FromMinutes(30));

        var result = EmailCodeExtractor.TryExtract("Welcome to FreeModel.", request);

        Assert.False(result.Found);
        Assert.Null(result.Code);
    }
}
