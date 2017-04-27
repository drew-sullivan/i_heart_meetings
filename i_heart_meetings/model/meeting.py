!/usr/bin/python

class Meeting:
    """A meeting extracted from the Google Calendar API

    Attributes:
        meeting_num: int - 1, 2, 3...
        summary: str - description of meeting
        start: str - human readable start time of meeting
        end: str - human readable end time of meeting
        duration: str - duration of event
        num_attendees: int - number of attendees
        financial_cost: str - human readable, printer friendly Money object
        percent_time: float - percent of team's time spent in meeting
    """
    WORK_HOURS_PER_DAY = 8


    def __init__(self, meeting_num, summary, start, end, duration,
                 num_attendees):
        self._meeting_num = meeting_num
        self._summary = summary
        self._start = start
        self._end = end
        self._duration = duration
        self._num_attendees = num_attendees

    def percent_time(self):
        work_seconds = self._duration._in_seconds()
        work_hours = work_seconds / 3600
        percent_time = (float(work_hours) / WORK_HOURS_PER_DAY) * 100
        percent_time = round(percent_time, ROUND_TO_THIS_MANY_PLACES)
        return percent_time


    def time_cost(self):
        work_seconds = self._duration._in_seconds()
        time_cost = self._num_attendees * work_seconds
        return time_cost


    def financial_cost(self):
        work_seconds = self._duration._in_seconds()
        financial_cost = work_seconds * COST_PER_SECOND * self.num_attendees
        financial_cost = Money(financial_cost, CURRENCY).format(CURRENCY_FORMAT)
        financial_cost = str(financial_cost)
        return financial_cost


    def _in_seconds(self):
        seconds = __get_duration_in_seconds(self._duration)
        seconds = __convert_seconds_to_work_seconds(seconds)
        return seconds


    def __get_duration_in_seconds(self):
        seconds = self.duration.total_seconds()
        return seconds


    def __convert_seconds_to_work_seconds(seconds)
        hours = float(seconds) / 3600
        if hours > WORK_HOURS_PER_DAY and hours < 24:
            hours = WORK_HOURS_PER_DAY
        if hours >= 24:
            days, hours = divmod(hours, 24)
            if hours <= WORK_HOURS_PER_DAY:
                hours += days * WORK_HOURS_PER_DAY
        seconds = hours * 3600
        return seconds

