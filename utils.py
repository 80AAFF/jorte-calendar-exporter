import logging
from icalendar import Calendar, Event
from datetime import datetime, timedelta, date
import pytz
import uuid
from collections import Counter
from jorte_api_dtos import JorteCalendarDto, JorteEventDto

logger = logging.getLogger(__name__)


def calendar_from_jorte_calendar(jorte_cal: JorteCalendarDto) -> Calendar:
    '''
    Converts a JorteCalendarDto to an icalendar calendar.
    Returns a single icalendar.Calendar.
    '''
    cal = Calendar()
    cal.add('prodid', f'-//git//jorte-to-ical-exporter//{jorte_cal.id}//EN')
    cal.add('version', '2.0')
    cal.add('name', jorte_cal.name)
    cal.add('X-WR-CALNAME', jorte_cal.name)
    cal.add('DESCRIPTION', jorte_cal.description)
    cal.add('X-WR-CALDESC', jorte_cal.description)
    cal.add('TIMEZONE-ID', jorte_cal.timezone)
    cal.add('X-WR-TIMEZONE', jorte_cal.timezone)
    return cal


def event_from_jorte_event(jorte_event: JorteEventDto,
                           is_from_sequence: bool = False) -> Event:
    '''
    Converts a JorteEventDto to an icalendar event. A new uid is generated if
    the event is for a sequence. Returns a single icalendar.Event.
    '''
    event = Event()
    uid = jorte_event.id
    if is_from_sequence:
        uid = uuid.uuid4()
    event.add('uid', uid)
    event.add('summary', jorte_event.title)

    if jorte_event.location:
        event.add('location', jorte_event.location)
    if jorte_event.content:
        event.add('description', jorte_event.content)

    dtstart = jorte_event.date_from
    dtend = jorte_event.date_to

    if jorte_event.start_date_time:
        sdt = jorte_event.start_date_time
        dtstart = dtstart.replace(hour=sdt.hour, minute=sdt.minute)

    if jorte_event.start_hour:
        dtstart = dtstart.replace(hour=jorte_event.start_hour)

    if jorte_event.start_minute:
        dtstart = dtstart.replace(minute=jorte_event.start_minute)

    if jorte_event.end_date_time:
        edt = jorte_event.end_date_time
        dtend = dtend.replace(hour=edt.hour, minute=edt.minute)

    if jorte_event.end_hour:
        dtend = dtend.replace(hour=jorte_event.end_hour)

    if jorte_event.end_minute:
        dtend = dtend.replace(minute=jorte_event.end_minute)

    # check if dtend is after dtstart and set it to dtstart if so
    if dtend < dtstart:
        dtend = dtstart

    # fix whole day events by
    # advancing dtend to midnight next day
    # and setting dtstart to midnight of day
    if (dtend - dtstart) > timedelta(hours=23, minutes=55):
        dtstart = date(year=dtstart.year, month=dtstart.month, day=dtstart.day)
        dtend = dtend + timedelta(days=1)
        dtend = date(year=dtend.year, month=dtend.month, day=dtend.day)

    event.add('dtstart', dtstart)
    event.add('dtend', dtend)

    # single_event_start_end_date_time = (not is_from_sequence
    #                                     and jorte_event.start_date_time
    #                                     and jorte_event.end_date_time)
    # single_event_date_from_to = (not is_from_sequence
    #                              and jorte_event.date_from
    #                              and jorte_event.date_to)
    # sequence_valid_params = (is_from_sequence
    #                          and jorte_event.start_date_time
    #                          and jorte_event.end_date_time
    #                          and jorte_event.date_from)

    # if single_event_start_end_date_time:
    #     event.add('dtstart', jorte_event.start_date_time)
    #     event.add('dtend', jorte_event.end_date_time)
    # elif single_event_date_from_to:
    #     event.add('dtstart', jorte_event.date_from)
    #     event.add('dtend', jorte_event.date_to)
    # elif sequence_valid_params:
    #     sdt = jorte_event.start_date_time
    #     edt = jorte_event.end_date_time
    #     df = jorte_event.date_from

    #     duration = edt - sdt

    #     dtstart = datetime(
    #         year=df.year,
    #         month=df.month,
    #         day=df.day,
    #         hour=sdt.hour,
    #         minute=sdt.minute,
    #         tzinfo=df.tzinfo
    #     )
    #     event.add('dtstart', dtstart)
    #     dtend = dtstart + duration
    #     event.add('dtend', dtend)
    # else:
    #     logger.error('Invalid set of start and end date for {jorte_event}')

    return event


def get_freq_from_sequence(sequence: list[JorteEventDto]) -> (bool, str):
    '''
    Analyzes a sequence of events to identify the common frequency in between
    events. The matching ical frequency is estimated based on the number of
    days of the common frequency between days. Supported frequencies are:
    'DAILY', 'WEEKLY', 'MONTHLY' and 'YEARLY'
    '''
    # sort events by start_date_time
    logger.debug(f"Analyzing sequence for {sequence[0].title}")
    sequence.sort(key=lambda e: e.date_from)

    # calculate intervals
    intervals = []
    for i in range(1, len(sequence)):
        interval = sequence[i].date_from - sequence[i-1].date_from
        intervals.append(interval)

    # identify standard interval
    interval_counts = Counter(intervals)
    standard_interval = interval_counts.most_common(1)[0][0]

    logger.debug(f"Identified sequence interval of: {standard_interval}")

    # log anomalies to interval
    anomalies = []
    for i, interval in enumerate(intervals, 1):
        if interval != standard_interval:
            anomalies.append((i, interval))

    if len(anomalies) > 0:
        m = f"Sequence '{sequence[0].title}' contains anomalies: {anomalies}"
        logger.info(m)

    # find out if sequence has ended
    dt_now = datetime.now(pytz.timezone(sequence[0].timezone))
    is_ongoing = False
    if sequence[-1].date_from + standard_interval > dt_now:
        is_ongoing = True

    return (is_ongoing, days_to_freq(standard_interval.days))


def days_to_freq(days: int) -> str:
    '''
    Estimates a supported frequency based on the amount of days in between
    events. Supports 'DAILY', 'WEEKLY', 'MONTHLY' and 'YEARLY'.
    '''
    if days == 1:
        return 'DAILY'
    elif days == 7:
        return 'WEEKLY'
    elif abs(days - 30) <= 2:  # 2 day margin for month approximation
        return 'MONTHLY'
    elif abs(days - 365) <= 15:  # 15 day margin for year approximation
        return 'YEARLY'
    else:
        m = "Tried to convert unknown days increment to frequency '{days}'"
        logger.exception(m)
        raise ValueError(m)


def timezone_difference(tz1, tz2, date_time=None):
    """
    Calculate the time difference between two timezones in hours and minutes.
    :return: Time difference in hours and minutes as a tuple.
    """
    if date_time is None:
        date_time = datetime.now()

    timezone1 = pytz.timezone(tz1)
    timezone2 = pytz.timezone(tz2)

    dt1 = timezone1.localize(date_time)
    dt2 = timezone2.localize(date_time)

    # Calculate the difference in seconds and then convert to hours and minutes
    difference_in_seconds = (dt1.utcoffset() - dt2.utcoffset()).total_seconds()
    hours = int(difference_in_seconds // 3600)
    minutes = int((difference_in_seconds % 3600) // 60)

    return hours, minutes


def datetime_fix_to_timestamp(tz1: str, tz2: str, timestamp: int) -> datetime:
    '''
    Fix the timestamp received for
    '''
    diff = timezone_difference(tz1, tz2)
    dt = datetime.fromtimestamp(timestamp)
    delta = timedelta(hours=diff[0], minutes=diff[1])
    dt = dt + delta
    tz = pytz.timezone(tz2)
    dt = tz.localize(dt)
    return dt
