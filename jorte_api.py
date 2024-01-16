from requests import Session
import logging
import json
import pytz
from datetime import datetime
from jorte_api_dtos import JorteCalendarDto, JorteEventDto
import utils
from urllib.error import HTTPError

logger = logging.getLogger(__name__)


class JorteApi:
    '''
    Class to interact with the Jorte API to extract events.
    '''
    def __init__(self, username: str, password: str) -> None:
        self._base_url = 'https://jorte.net'
        self.session = Session()
        self._auth(username=username, password=password)

    def _auth(self, username: str, password: str) -> None:
        '''
        Initialise session with Jorte server using login endpoint.
        Required cookies to perform queries to other endpoints are set:
            - JSESSIONID, AWSALB, AWSALBCORS
        '''
        url = "/login"
        url = self._base_url + url

        params = {
            'account': str(username),
            'password': str(password),
            'SAStruts.method': 'doLogin'
        }

        response = self.session.get(url='https://jorte.net/login/',
                                    params=params)
        response.raise_for_status()

        logger.debug(f'Configured cookies: {self.session.cookies}')

    def pre_auth(self) -> None:
        '''
        Endpoint that can be used to validate if received session tokens
        are valid and accepted by the Jorte server.
        '''
        url = '/login/preAuth'
        url = self._base_url + url

        response = self.session.post(url=url)

        if 'unauthorized' in response.text:
            m = "API returned status unauthorized"
            logger.exception(m)
            raise HTTPError(url=url,
                            code=401,
                            msg=response.text,
                            hdrs=m,
                            fp=None)

    def get_calendars(self) -> list[JorteCalendarDto]:
        '''
        Endpoint to receive a list of available calendars to an account.
        Retrieved information is returned as list of JorteCalendarDto.
        '''
        url = '/schedule/scheduleCalendar/jsonMyCalendar'
        url = self._base_url + url

        response = self.session.post(url=url)
        response.raise_for_status()

        r_json = response.json()
        if not isinstance(r_json, list):
            m = f"Received json is not a list of objects: {json.dumps(r_json)}"
            logger.exception(m)
            raise ValueError(m)

        calendars = []
        for r_obj in r_json:
            calendars.append(
                JorteCalendarDto(
                    name=r_obj.get('name'),
                    description=r_obj.get('description'),
                    timezone=r_obj.get('timezone'),
                    event_count=int(r_obj.get('eventCount')),
                    owner=r_obj.get('owner'),
                    id=r_obj.get('id'),
                    old_object_id=r_obj.get('oldObjectId')
                )
            )

        return calendars

    def set_search_date(self, calendars: list[JorteCalendarDto], year: int, month: int) -> None:  # noqa E501
        '''
        Endpoint to set the year and month for which to search events.
        Required fo be used before 'get_events' to set the time for which to
        retrieve events. Response is discarded as if does not contain relevant
        information for export.
        '''
        url = '/schedule/scheduleCalendar/jsonSearch'
        url = self._base_url + url

        form_data = []

        form_data.append(('year', str(year)))
        form_data.append(('month', str(month)))
        form_data.append(('isShowTask', 'false'))

        for cal in calendars:
            form_data.append(('calendarIds', cal.id))
            form_data.append(('oldCalendarIds', cal.old_object_id))

        response = self.session.post(url=url, data=form_data)
        response.raise_for_status()

    def get_events(self) -> list[JorteEventDto]:
        '''
        Endpoint to retrieve a list of Events for the calendars and range
        specified in 'set_search_date'. Returns a list of JorteEventDto
        objects.
        '''
        url = '/schedule/scheduleCalendar/jsonSearchEvent'
        url = self._base_url + url

        response = self.session.post(url=url)
        response.raise_for_status()

        r_json = response.json()
        if not isinstance(r_json, list):
            m = f"Received json is not a list of objects: {json.dumps(r_json)}"
            logger.exception(m)
            raise ValueError(m)

        events = []
        for r_obj in r_json:
            target_tz = pytz.timezone(zone=r_obj.get('timezoneId'))

            date_from = None
            if r_obj.get('dateFrom') is not None:
                date_from = utils.datetime_fix_to_timestamp(
                    'Asia/Tokyo',
                    r_obj.get('timezoneId'),
                    int(r_obj.get('dateFrom')/1000)
                )

            date_to = None
            if r_obj.get('dateTo') is not None:
                date_to = utils.datetime_fix_to_timestamp(
                    'Asia/Tokyo',
                    r_obj.get('timezoneId'),
                    int(r_obj.get('dateTo')/1000)
                )

            start_date_time = None
            if r_obj.get('startDateTime') is not None:
                start_date_time = datetime.fromtimestamp(
                    r_obj.get('startDateTime')/1000,
                    tz=target_tz
                )

            end_date_time = None
            if r_obj.get('endDateTime') is not None:
                end_date_time = datetime.fromtimestamp(
                    r_obj.get('endDateTime')/1000,
                    tz=target_tz
                )

            events.append(
                JorteEventDto(
                    id=r_obj.get('id'),
                    title=r_obj.get('title'),
                    location=r_obj.get('location'),
                    content=r_obj.get('content'),
                    is_all_day=r_obj.get('isAllday'),
                    date_from=date_from,
                    start_hour=r_obj.get('startHour'),
                    start_minute=r_obj.get('startMinute'),
                    date_to=date_to,
                    end_hour=r_obj.get('endHour'),
                    end_minute=r_obj.get('endMinute'),
                    start_date_time=start_date_time,
                    end_date_time=end_date_time,
                    is_recurrence=r_obj.get('isRecurrence'),
                    timezone=r_obj.get('timezoneId'),
                    calendar_id=r_obj.get('calendarId'),
                    image_id=r_obj.get('imageId')
                )
            )

        return events

    def get_events_for_month(self, calendards: JorteCalendarDto, year: int, month: int) -> list[JorteEventDto]:  # noqa E501
        self.set_search_date(calendars=calendards, year=year, month=month)
        return self.get_events()
