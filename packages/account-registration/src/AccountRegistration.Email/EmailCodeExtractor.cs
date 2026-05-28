using System.Text.RegularExpressions;

namespace AccountRegistration.Email;

public static partial class EmailCodeExtractor
{
    public static EmailCodeResult TryExtract(string text, EmailCodeRequest request)
    {
        ArgumentNullException.ThrowIfNull(text);
        ArgumentNullException.ThrowIfNull(request);

        if (!string.IsNullOrWhiteSpace(request.CodePattern))
        {
            var configuredMatch = Regex.Match(text, request.CodePattern, RegexOptions.IgnoreCase, TimeSpan.FromSeconds(1));
            if (configuredMatch.Success)
            {
                var value = configuredMatch.Groups.Count > 1 ? configuredMatch.Groups[1].Value : configuredMatch.Value;
                return EmailCodeResult.FromCode(NormalizeCode(value));
            }
        }

        var match = SixDigitCodeRegex().Match(text);
        return match.Success
            ? EmailCodeResult.FromCode(NormalizeCode(match.Value))
            : EmailCodeResult.NotFound;
    }

    private static string NormalizeCode(string value)
        => NonDigitRegex().Replace(value, string.Empty);

    [GeneratedRegex(@"(?<!\d)(?:\d[\s-]?){6}(?!\d)", RegexOptions.Compiled)]
    private static partial Regex SixDigitCodeRegex();

    [GeneratedRegex(@"\D", RegexOptions.Compiled)]
    private static partial Regex NonDigitRegex();
}
