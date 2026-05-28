namespace AccountRegistration.Email.Tests;

using AccountRegistration.Email;

public sealed class ProtonBridgeImapOptionsTests
{
    [Fact]
    public void DefaultLocal_UsesProtonBridgeDefaults()
    {
        var options = ProtonBridgeImapOptions.DefaultLocal("bridge-user", "bridge-password");

        Assert.Equal("127.0.0.1", options.Host);
        Assert.Equal(1143, options.Port);
        Assert.Equal("bridge-user", options.UserName);
        Assert.Equal("bridge-password", options.Password);
        Assert.False(options.UseSsl);
        Assert.True(options.UseStartTlsWhenAvailable);
        Assert.True(options.AllowInvalidServerCertificate);
    }

    [Theory]
    [InlineData("")]
    [InlineData(" ")]
    public void Validate_RejectsMissingHost(string host)
    {
        var options = ProtonBridgeImapOptions.DefaultLocal("user", "password") with { Host = host };

        var error = Assert.Throws<ArgumentException>(options.Validate);

        Assert.Contains("Host", error.Message);
    }

    [Theory]
    [InlineData(0)]
    [InlineData(65536)]
    public void Validate_RejectsInvalidPort(int port)
    {
        var options = ProtonBridgeImapOptions.DefaultLocal("user", "password") with { Port = port };

        var error = Assert.Throws<ArgumentOutOfRangeException>(options.Validate);

        Assert.Contains("Port", error.Message);
    }
}
