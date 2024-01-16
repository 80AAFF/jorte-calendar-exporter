import os
import logging
import logging.config
from datetime import datetime
from itertools import groupby
from icalendar import vRecur
import utils
import settings
from jorte_api import JorteApi


logging.basicConfig()
logging.config.fileConfig(
    fname='./logging.ini',
    disable_existing_loggers=False)
logger = logging.getLogger(__name__)


logger.info('Starting app')

# Check if user can authenticate with JorteApi
api = JorteApi(
    username=settings.USERNAME,
    password=settings.PASSWORD)
api.pre_auth()

# Get calendars for user from jorte
jorte_calendars = api.get_calendars()

for jorte_cal in jorte_calendars:
    if not jorte_cal.owner:
        jorte_calendars.pop(jorte_cal)

logger.info(f"Received {len(jorte_calendars)} calendars")
logger.debug(f"Calendars: {jorte_calendars}")

# Get events for calendars from jorte

start_date = datetime(year=settings.EXPORT_START_YEAR,
                      month=settings.EXPORT_START_MONTH,
                      day=1)
end_date = datetime(year=settings.EXPORT_END_YEAR,
                    month=settings.EXPORT_END_MONTH,
                    day=1)
current_date = start_date

jorte_events = []

while current_date <= end_date:
    year = current_date.year
    month = current_date.month
    new_events = api.get_events_for_month(calendards=jorte_calendars,
                                          year=year,
                                          month=month)

    logger.info(f"Received {len(new_events)} events for {year}-{month}")
    jorte_events += new_events
    logger.info(f"Loaded {len(jorte_events)} total events")

    if current_date.month == 12:
        current_date = datetime(year=current_date.year + 1,
                                month=1,
                                day=1)
    else:
        current_date = datetime(year=current_date.year,
                                month=current_date.month + 1,
                                day=1)

# Remove duplicate events
seen = set()
unique_jorte_events = []

for event in jorte_events:
    identifier = (event.id, event.title, event.date_from, event.date_to)
    if identifier not in seen:
        seen.add(identifier)
        unique_jorte_events.append(event)

m = "{cnt} events remain after sorting out duplicates.".format(
    cnt=len(unique_jorte_events))
logger.info(m)

# Group event sequences based on event id
unique_jorte_events.sort(key=lambda x: x.id if x.id is not None else "")
grouped_unique_jorte_events = {
    title: list(group) for title, group in groupby(
        unique_jorte_events,
        key=lambda x: x.id if x.id is not None else "")
    }
dict_grouped_unique_jorte_events = dict(grouped_unique_jorte_events)

m = "{cnt} events and sequences remain after grouping sequences.".format(
    cnt=len(dict_grouped_unique_jorte_events))
logger.info(m)

# Create ical calendars for exported calendars
calendars = {}
for jorte_cal in jorte_calendars:
    new_cal = utils.calendar_from_jorte_calendar(jorte_cal=jorte_cal)
    calendars[jorte_cal.id] = new_cal

# Create ical events from jorte_events and add to ical calendar
for id, jorte_events in dict_grouped_unique_jorte_events.items():
    is_sequence = (len(jorte_events) > 1)

    if not is_sequence:
        # create ical event for single jorte_event
        jorte_event = jorte_events[0]
        logger.info(f'Processing individual event: "{jorte_event.title}"')
        logger.debug(jorte_event)
        new_event = utils.event_from_jorte_event(jorte_event=jorte_event)
        calendars[jorte_event.calendar_id].add_component(new_event)

    if is_sequence:
        # create ical events for jorte_event sequence
        logger.info(f'Processing sequence for "{jorte_events[0].title}"')
        logger.debug(jorte_events)

        try:
            sequence_is_ongoing, freq = utils.get_freq_from_sequence(
                sequence=jorte_events)
        except ValueError:
            m = f'Treating sequence "{jorte_events[0].title}" as terminated.'
            logger.error(m)
            sequence_is_ongoing = False

        last_jorte_event = jorte_events[-1]
        for jorte_event in jorte_events:
            new_event = utils.event_from_jorte_event(jorte_event=jorte_event,
                                                     is_from_sequence=True)

            if jorte_event == last_jorte_event and sequence_is_ongoing:
                recurrence_rule = vRecur({'FREQ': freq})
                new_event.add('rrule', recurrence_rule)

            calendars[jorte_event.calendar_id].add_component(new_event)

# Export calendars to file
for id, cal in calendars.items():
    logger.info(f"Exporting calendar with id {id}")
    # print(cal.to_ical().decode("utf-8"))

    f_name = f'{id}.ics'
    f = open(os.path.join(f_name), 'wb')
    f.write(cal.to_ical())
    f.close()
