#!/usr/bin/python

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
