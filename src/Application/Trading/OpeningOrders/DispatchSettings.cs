namespace TseExcel.Application.Trading.OpeningOrders;

public sealed record DispatchSettings
{
    public static TimeOnly DefaultStart => new(8, 44, 58);
    public const decimal DefaultDurationSeconds = 5m;
    public const int DefaultIntervalMicroseconds = 350;
    public DateTimeOffset Start { get; }
    public TimeSpan Duration { get; }
    public TimeSpan Interval { get; }
    public long EstimatedAttempts => checked((long)decimal.Ceiling((decimal)Duration.Ticks / Interval.Ticks));

    public DispatchSettings(DateTimeOffset start, decimal durationSeconds, int intervalMicroseconds)
    {
        decimal ticks = durationSeconds * TimeSpan.TicksPerSecond;
        if (ticks <= 0 || ticks > TimeSpan.MaxValue.Ticks || ticks != decimal.Truncate(ticks) || intervalMicroseconds <= 0)
            throw new ArgumentOutOfRangeException(nameof(durationSeconds), "Positive, representable dispatch timing is required.");
        Start = start;
        Duration = TimeSpan.FromTicks((long)ticks);
        Interval = TimeSpan.FromTicks(checked((long)intervalMicroseconds * 10));
        _ = start + Duration;
        _ = EstimatedAttempts;
    }

    public static DateTimeOffset TodayLocal(TimeOnly time, DateTimeOffset now)
    {
        DateTime local = now.LocalDateTime.Date + time.ToTimeSpan();
        if (TimeZoneInfo.Local.IsInvalidTime(local) || TimeZoneInfo.Local.IsAmbiguousTime(local))
            throw new ArgumentException("The selected local time is ambiguous or invalid.");
        var target = new DateTimeOffset(local, TimeZoneInfo.Local.GetUtcOffset(local));
        if (target <= now) throw new ArgumentException("Today's requested start time has passed.");
        return target;
    }
}
