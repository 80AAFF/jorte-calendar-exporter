from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class JorteCalendarDto():
    '''
    Data transfer object containing a subset of available properties for a
    calendar that are used during export.
    '''
    # id of the calendar in jorte
    id: str

    # user provided calendar name
    name: str

    # user provided description
    description: str

    # string of the default timezone of the calendar,
    # e.g. 'Europe/Berlin'
    timezone: str

    # if the calender is owned by current user
    owner: bool

    # required to request events for the calendar
    old_object_id: str

    # total count of events in the calendar
    event_count: int


@dataclass(frozen=True)
class JorteEventDto():
    '''
    Data transfer object containing a subset of available properties for an
    event that are used during export to construct an iCal event.
    '''
    # id of the event in jorte
    id: str

    # user provided title of the event
    title: str

    # user provided notes to the event
    content: str

    # user specified location as string for the event
    location: str

    # true if the event is an all day event
    is_all_day: bool

    # true if the event is recurring
    # (recurring events have multiple events for each occurrence)
    is_recurrence: bool

    # string of the timezone if the event, e.g. 'Europe/Berlin'
    timezone: str

    # datetime of the starting date of the event. If neither start_date_time or
    # (start_hour and start_minute) are set indicates a whole day event for
    # that day.
    date_from: datetime

    # datetime of the exact time when the event starts. For sequences, this
    # is the datetime when the first event started.
    start_date_time: datetime

    # hour when the event starts on the day set by date_from. There is no
    # apparent link to start_date_time. It can be set or not set if start_hour
    # and start_minute are set.
    start_hour: int

    # minutes of the hour when the event starts on the day set by date_from.
    # There is no apparent link to start_date_time. It can be set or not set
    # if start_hour and start_minute are set.
    start_minute: int

    # datetime of the ending date of the event. For whole day events, this is
    # midnight of the starting day or the last day that the event occurs.
    date_to: datetime

    # datetime of the exact time when the event ends. For sequences, this
    # is the datetime when the first event ended.
    end_date_time: datetime

    # hour when the event ends on the day set by date_from. There is no
    # apparent link to start_date_time. It can be set or not set if start_hour
    # and start_minute are set.
    end_hour: int

    # minutes of the hour when the event ends on the day set by date_from.
    # There is no apparent link to start_date_time. It can be set or not set
    # if start_hour and start_minute are set.
    end_minute: int

    # id of the calendar that the event links to,
    # corresponds with CalendarDto.id
    calendar_id: str

    # id of an icon displayed for the event in jorte
    # (not used for iCal events)
    image_id: str
