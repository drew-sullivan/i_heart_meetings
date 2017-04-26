#!/usr/bin/python

from model.meeting import Meeting 

class Calculator:
    """Calculates the costs of a meetings pull when passed a list of meetings
    objects

    Attributes:
        meetings: list - meeting objects
        time_cost_weekly_in_seconds:
        financial_cost_weekly:
        percent_time_weekly:
        numbers: list - meeting nums
        durations: list - durations of meetings
        summaries: list - summaries of meetings
        num_meetings: int - number of meetings in pull
        avg_meeting_duration: int - total seconds from all meetings in pull
        meeting_frequency = dict - k: meeting start, v: num_attendees
    """

    WORK_HOURS_PER_YEAR = 2000
    WORK_HOURS_PER_DAY = 8
    WORK_DAYS_PER_WEEK = 5
    WORK_HOURS_PER_WEEK = WORK_HOURS_PER_DAY * WORK_DAYS_PER_WEEK
    WORK_SECONDS_PER_WEEK = WORK_HOURS_PER_WEEK * 3600
    WORK_WEEKS_PER_YEAR = WORK_HOURS_PER_YEAR / (WORK_HOURS_PER_DAY * WORK_DAYS_PER_WEEK)
    WORK_DAYS_PER_YEAR = WORK_WEEKS_PER_YEAR * WORK_DAYS_PER_WEEK
    WORK_SECONDS_PER_YEAR = WORK_HOURS_PER_YEAR * 3600

    IDEAL_PERCENT_TIME_IN_MEETINGS = 5
    IDEAL_PERCENT_TIME_IN_MEETINGS_DECIMAL = float(IDEAL_PERCENT_TIME_IN_MEETINGS / 100)

    YEARLY_SALARY_USD = 75000
    COST_PER_SECOND = float(YEARLY_SALARY_USD) / WORK_SECONDS_PER_YEAR
    CURRENCY = 'USD'
    CURRENCY_FORMAT = 'en_US'

    TEAM_SIZE = 10

    PERSON_SECONDS_PER_WEEK = TEAM_SIZE * WORK_SECONDS_PER_WEEK
    PERSON_SECONDS_PER_YEAR = TEAM_SIZE * WORK_SECONDS_PER_YEAR

    ROUND_TO_THIS_MANY_PLACES = 2
    FORMAT_DATETIME_OBJ_TO_STR = '%Y-%m-%d %H:%M:%S'
    FORMAT_STR_TO_DATETIME_OBJ = '%A, %b %d, %Y - %I:%M'

    NUM_TOP_MEETING_TIMES = 3


    def __init__(self, meetings):
        self.meetings = meetings


    @property
    def meetings(self):
        return self.meeting_objs

    @meetings.setter(self, meetings):
        self._meetings = meetings


    def calculate_meeting_costs(meetings):
        for meeting_number, meeting in enumerate(meetings, 1):
            m = Meeting(
                m.meeting_number = meeting_number
                m.summary = _get_summary(meeting)
                m.start = parse(meeting['start'].get('dateTime', meeting['start'].get('date')))
                m.end = parse(meeting['end'].get('dateTime', meeting['end'].get('date')))
                m.duration = _get_duration(m.start, m.end)
                m.num_attendees = _get_num_attendees(meeting.get('attendees'))

                seconds_in_meeting = _convert_time_obj_to_seconds(m.duration)

                m.financial_cost = _get_financial_cost_single_meeting(seconds_in_meeting, m.num_attendees)
                m.time_cost_single_meeting = _get_time_cost_single_meeting(seconds_in_meeting, m.num_attendees)

                days, hours, minutes, seconds = _translate_seconds(m.time_cost_single_meeting)

                m.days = days
                m.hours = hours
                m.minutes = minutes
                m.seconds = seconds
                m.percent_time = _calculate_percentage_time_in_meeting_single(seconds_in_meeting)
            )


    def _calculate_percentage_time_in_meeting_single(seconds_in_meeting):
        hours_in_meeting = seconds_in_meeting / 3600
        percent_time_in_meeting = (float(hours_in_meeting) / WORK_HOURS_PER_DAY) * 100
        percent_time_in_meeting = round(percent_time_in_meeting, ROUND_TO_THIS_MANY_PLACES)
        return percent_time_in_meeting


    def _get_time_cost_single_meeting(seconds_in_meeting, num_attendees):
        time_cost_single_meeting = num_attendees * seconds_in_meeting
        return time_cost_single_meeting


    def _translate_seconds(total_seconds):
        # divmod returns quotient and remainder
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        work_days, hours = divmod(hours, WORK_HOURS_PER_DAY)
        return (int(work_days), int(hours), int(minutes), int(seconds))
        def _get_time_cost_single_meeting(seconds_in_meeting, num_attendees):
            time_cost_single_meeting = num_attendees * seconds_in_meeting
            return time_cost_single_meeting


    def _get_financial_cost_single_meeting(seconds_in_meeting, num_attendees):
        financial_cost_single_meeting = seconds_in_meeting * COST_PER_SECOND * num_attendees
        financial_cost_single_meeting = Money(financial_cost_single_meeting,
                CURRENCY).format(CURRENCY_FORMAT)
        financial_cost_single_meeting = str(financial_cost_single_meeting)
        return financial_cost_single_meeting


    def _convert_time_obj_to_hours(duration):
        seconds = duration.total_seconds()
        hours = float(seconds) / 3600
        if hours > 8 and hours < 24:
            hours = WORK_HOURS_PER_DAY
        if hours >= 24:
            days, hours = divmod(hours, 24)
            if hours <= 8:
                hours += days * WORK_HOURS_PER_DAY
        return hours


    def _convert_time_obj_to_seconds(duration):
        seconds = duration.total_seconds()
        hours = float(seconds) / 3600
        if hours > WORK_HOURS_PER_DAY and hours < 24:
            hours = WORK_HOURS_PER_DAY
        if hours >= 24:
            days, hours = divmod(hours, 24)
            if hours <= WORK_HOURS_PER_DAY:
                hours += days * WORK_HOURS_PER_DAY
        seconds = hours * 3600
        return seconds


    def _get_num_attendees(num_attendees):
        if num_attendees == None:
            num_attendees = 1
        # if sharing multiple calendars, uncomment below
        #num_attendees = 1
        else:
            num_attendees = len(num_attendees)
        return num_attendees


    def _get_duration(start, end)
        return end - start


    def _get_summary(meeting):
        summary = meeting.get('summary', 'No summary given')
        return summary



            meetings.append(Meeting(meeting_number, summary, start, end,
                meeting_duration, num_attendees, financial_cost_single_meeting,
                days, hours, minutes, seconds, percent_time_meeting_single))
        for meeting

