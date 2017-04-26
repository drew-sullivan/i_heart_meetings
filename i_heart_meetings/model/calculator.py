#!/usr/bin/python

from model.meeting import Meeting 

class Calculator:
    """Calculates the costs of a meetings pull when passed a list of meetings
    objects

    Attributes:
        meetings_objs: list - meeting objects
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


    def __init__(self, meetings):
        self.meetings = meetings


    @property
    def meeting_objs:
        return self.meeting_objs


    def calculate_meeting_costs(meetings):
        for meeting_number, meeting in enumerate(meetings, 1):
            meetings.append(Meeting(meeting_number, summary, start, end,
                meeting_duration, num_attendees, financial_cost_single_meeting,
                days, hours, minutes, seconds, percent_time_meeting_single))

