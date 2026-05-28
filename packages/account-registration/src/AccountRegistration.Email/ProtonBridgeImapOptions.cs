namespace AccountRegistration.Email;

public sealed record ProtonBridgeImapOptions
{
    public required string Host { get; init; }

    public required int Port { get; init; }

    public required string UserName { get; init; }

    public required string Password { get; init; }

    public bool UseSsl { get; init; }

    public bool UseStartTlsWhenAvailable { get; init; } = true;

    public bool AllowInvalidServerCertificate { get; init; } = true;

    public static ProtonBridgeImapOptions DefaultLocal(string userName, string password)
        => new()
        {
            Host = "127.0.0.1",
            Port = 1143,
            UserName = userName,
            Password = password,
            UseSsl = false,
            UseStartTlsWhenAvailable = true,
            AllowInvalidServerCertificate = true
        };

    public void Validate()
    {
        if (string.IsNullOrWhiteSpace(Host))
        {
            throw new ArgumentException("Host is required.", nameof(Host));
        }

        if (Port is < 1 or > 65535)
        {
            throw new ArgumentOutOfRangeException(nameof(Port), "Port must be between 1 and 65535.");
        }

        if (string.IsNullOrWhiteSpace(UserName))
        {
            throw new ArgumentException("UserName is required.", nameof(UserName));
        }

        if (string.IsNullOrWhiteSpace(Password))
        {
            throw new ArgumentException("Password is required.", nameof(Password));
        }
    }
}
