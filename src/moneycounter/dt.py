import datetime
import pytz

time_zone = 'America/New_York'


def get_time_zone():
    return time_zone


def our_now():
    # This results in a time that can be compared values in our database
    # even if saved by a human entering wall clock time into an admin field.
    # This is in the time zone specified in settings, for us it is 'America/New_York'.
    return datetime.datetime.now(tz=pytz.timezone(time_zone))


def our_localize(t):
    # Given datetime(2021, 10, 21, 0, 0, 0, 0) this will return the
    # datetime when it is 0, 0, 0, 0 in the local time, say NY.
    utc = pytz.timezone('UTC')
    tz = pytz.timezone(time_zone)
    return tz.localize(t).astimezone(utc)


def to_date(d):
    if type(d) == str:
        if '-' in d:
            d = datetime.date.fromisoformat(d)
        else:
            d = datetime.datetime.strptime(d, '%Y%m%d').date()
    elif d is None:
        d = datetime.date.today()

    return d


def day_start(d):
    # Return start of day in local time zone
    t = datetime.datetime(d.year, d.month, d.day)
    return our_localize(t)


def day_start_next_day(d):
    # Return start of next day in local time zone
    # Good for finding all trades where dt is less than this for a given date.
    t = datetime.datetime(d.year, d.month, d.day)
    t += datetime.timedelta(days=1)
    return our_localize(t)


def set_tz(dt):
    # useful for output
    tz = pytz.timezone(time_zone)
    if dt.tzinfo is not None:
        return dt.astimezone(tz)
    return tz.localize(dt)


def yyyymmdd2dt(d):
    if (type(d) == datetime.datetime) or (type(d) == datetime.date):
        return d
    d = datetime.datetime.strptime(str(d), '%Y%m%d')
    d = set_tz(d)
    return d


def dt2dt(dt):
    tz = pytz.timezone(time_zone)
    dt = datetime.datetime.fromisoformat(dt)
    return tz.localize(dt)


def y1_to_y4(y):
    y = 2020 + int(y)
    yr = our_now().year
    if y > yr:
        while y - yr > 10:
            y -= 1
    else:
        while yr - y > 10:
            y += 1
    return y


def is_week_end(d):
    return d.weekday() > 4


# Butcher's algorithm http://code.activestate.com/recipes/576517-calculate-easter-western-given-a-year/
def easter(year):
    #  Returns Easter as a date object.
    a = year % 19
    b = year // 100
    c = year % 100
    d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
    e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
    f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
    month = f // 31
    day = f % 31 + 1
    return datetime.date(year, month, day)


def good_friday(year):
    d = easter(year)
    return d - datetime.timedelta(days=2)


def which_holiday(dte, weekend_f=True):
    "d = 0 is Monday"
    y, m, d, wd = dte.year, dte.month, dte.day, dte.weekday()

    if weekend_f and wd > 4:
        return 'Weekend'

    if 1 == m:
        if 1 == d:
            return 'New Years Day'
        elif (2 == d) and (0 == wd):
            # It is Monday the 2nd so the first was a Sunday.
            return 'New Years Day observed'
        elif (0 == wd) and (d > 14) and (d < 22) and (y > 1985):
            return 'MLK Day'
    elif 2 == m:
        # Presidents day - third Monday of February
        if (0 == wd) and (d > 14) and (d < 22):
            return 'Presidents Day'
    elif 5 == m:
        # Memorial day is the last Monday in May
        if (0 == wd) and (d > 24):
            return 'Memorial Day'
    elif 6 == m and y > 2021:
        # Started celebrating Juneteenth in 2022
        if 19 == d:
            return "Juneteenth"
        elif (0 == wd) and (d == 20 or d == 21):
            # It is Monday but the 19th was on the weekend.
            return "Juneteenth Observed"
    elif 7 == m:
        # Independence day
        if 4 == d:
            return 'Independence Day'
        elif (3 == d) and (4 == wd):
            # It is the 3rd of the month and a Friday so the 4th is Saturday
            # This happens in 2020.
            return 'Independence Day Observed'
        elif (5 == d) and (0 == wd):
            # It is the 5th of the month and a Monday so the 4th is Sunday.
            return 'Independence Day Observed'
    elif 9 == m:
        # Labor day
        if (0 == wd) and (d < 8):
            return 'Labor Day'
    elif 11 == m:
        # Thanksgiving - fourth Thursday of November
        if (3 == wd) and (d > 21) and (d < 29):
            return 'Thanksgiving Day'
    elif 12 == m:
        if 25 == d:
            # Christmas
            return 'Christmas'
        elif (24 == d) and (4 == wd):
            # It is Friday the 24th so Christmas is on Saturday
            return 'Christmas observed'
        elif (26 == d) and (0 == wd):
            # It is Monday the 26th so Christmas is on Sunday
            return 'Christmas observed'
        elif (31 == d) and (4 == wd):
            # It is Friday the 31st so Saturday is New Years.
            return 'New Years Day observed'

    gf = good_friday(y)
    if dte == good_friday(y):
        return 'Good Friday'

    return None


def is_holiday_observed(dte, weekend_f=True):
    return which_holiday(dte, weekend_f=weekend_f) is not None


def most_recent_business_day(d):
    d = to_date(d)
    while is_holiday_observed(d):
        d -= datetime.timedelta(days=1)
    return d


def prior_business_day(d=None):
    if d is None:
        d = our_now()
    d -= datetime.timedelta(days=1)
    return most_recent_business_day(d)


def next_business_day(d):
    d += datetime.timedelta(days=1)
    while is_holiday_observed(d):
        d += datetime.timedelta(days=1)
    return d


def lbd_of_month(d):
    y = d.year
    m = d.month
    if m == 12:
        d = datetime.date(y + 1, 1, 1)
    else:
        d = datetime.date(y, m + 1, 1)

    return prior_business_day(d)


def is_lbd_of_month(d):
    return d == lbd_of_month(d)


def lbd_prior_month(d):
    d = datetime.date(d.year, d.month, 1)
    d -= datetime.timedelta(days=1)
    return lbd_of_month(d)


def lbd_next_month(d):
    y = d.year
    m = d.month
    if m == 12:
        m = 1
        y += 1
    else:
        m += 1
    d = datetime.date(y, m, 1)
    d = lbd_of_month(d)
    return d
