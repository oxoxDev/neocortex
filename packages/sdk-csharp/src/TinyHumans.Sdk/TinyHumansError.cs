namespace TinyHumans.Sdk;

public class TinyHumansError : Exception
{
    public int Status { get; }
    public string Body { get; }

    public TinyHumansError(string message, int status, string body)
        : base(message)
    {
        Status = status;
        Body = body;
    }
}
