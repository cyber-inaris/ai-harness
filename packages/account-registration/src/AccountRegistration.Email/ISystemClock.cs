namespace AccountRegistration.Email;

public interface ISystemClock
{
    DateTimeOffset UtcNow { get; }
}
