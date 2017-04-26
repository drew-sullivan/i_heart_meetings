#!/usr/bin/python

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
        days: str - human readable, printer friendly
        hours: str - human readable, printer friendly
        minutes: str - human readable, printer friendly
        seconds: str - human readable, printer friendly
        percent_time: float - percent of team's time spent in meeting
    """

    def __init__(self, meeting_num, summary, start, end, duration,
                 num_attendees, financial_cost, days, hours, minutes, seconds,
                 percent_time):
        self._meeting_num = meeting_num
        self.summary = summary
        self.start = start
        self.end = end
        self.duration = duration
        self.num_attendees = num_attendees
        self.financial_cost = financial_cost
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.percent_time = percent_time


    @property
    def meeting_num(self):
        return self._meeting_num

    @meeting_num.setter
    def meeting_num(self, meeting_num):
        self._meeting_num = meeting_num


    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, summary):
        self._summary = summary


    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = start


    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end):
        self._end = end


    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, duration):
        self._duration = duration


    @property
    def num_attendees(self):
        return self._num_attendees

    @num_attendees.setter
    def num_attendees(self, num_attendees):
        self._num_attendees = num_attendees

    def print_details(self):
        print("""
        Meeting {0}: {1}
        **************************************************
        Start: {2}
        End: {3}
        Duration: {4}
        Number of Attendees: {5}
        Cost: {6}
        Cost in Time: {7}, {8}, {9}, {10}
        Percentage of time spent in meeting: {11}%
        """.format(self.meeting_num, self.summary, self.start, self.end,
                   self.duration, self.num_attendees, self.financial_cost,
                   self.days, self.hours, self.minutes, self.seconds,
                   self.percent_time))


    def print_types(self):
        print("""
        Meeting-num: {0}
        Summary: {1}
        Start: {2}
        End: {3}
        Duration: {4}
        Number of Attendees: {5}
        Financial-Cost: {6}
        Days: {7} 
        Hours: {8}
        Minutes: {9}
        Seconds: {10}
        Percent time: {11}
        """.format(type(self.meeting_num), type(self.summary),
                   type(self.start), type(self.end), type(self.duration),
                   type(self.num_attendees), type(self.financial_cost),
                   type(self.days), type(self.hours), type(self.minutes),
                   type(self.seconds), type(self.percent_time)))



