namespace AccountRegistration.Email;

public sealed record EmailMessageCandidate(
    string Subject,
    string To,
    DateTimeOffset ReceivedAt,
    string BodyText);
