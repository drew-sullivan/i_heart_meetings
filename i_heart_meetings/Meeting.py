#!/usr/bin/python

class Meeting:
    """A meeting extracted from the Google Calendar API
    """

    def __init__(self, meeting_num, summary, start, end, duration,
                 num_attendees, financial_cost, days, hours, minutes, seconds,
                 percent_time):
        self.meeting_num = meeting_num
        self.summary = summary
        self.start = start
        self.end = end
        self.duration = duration
        self.num_attendees
        self.financial_cost
        self.days
        self.hours
        self.minutes
        self.seconds
        self.percent_time


    def display_meeting_info(self):
        print("""
        Meeting {0}: {1}
        ==========================================================
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
