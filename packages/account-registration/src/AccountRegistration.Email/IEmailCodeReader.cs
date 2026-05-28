namespace AccountRegistration.Email;

public interface IEmailCodeReader
{
    Task<EmailCodeResult> WaitForCodeAsync(
        EmailCodeRequest request,
        CancellationToken cancellationToken);
}
