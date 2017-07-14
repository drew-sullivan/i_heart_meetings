#!/isr/bin/env python

import argparse
import datetime
import httplib2
import json
import os
import pdb
import sys
import textwrap
import time
import webbrowser

from apiclient import discovery
from datetime import time
from datetime import timedelta
from model.calendar_connection import CalendarConnection
from model.meeting import Meeting
from model.report import Report
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


help = textwrap.dedent("""
    """ )

from flask import Flask
from flask import render_template
app = Flask(__name__)


def get_meeting_report():

    cc = CalendarConnection()
    meetings = cc.meetings
    #  _print_calendar_results_as_json(meetings)

    rep = Report(meetings)

    data = rep.printable_data
    rep.write_report_html(data)

    rep.post_report_to_slack()
    #
    #  rep.write_db_to_csv()
    #  rep.write_csv_to_json()
    #
    generate_charts(data)
    open_charts_in_browser()


def open_charts_in_browser():
    webbrowser.open('http://localhost:5000/percent_pie')
    #  webbrowser.open('http://localhost:5000/percent_pie_split_2')
    #  webbrowser.open('http://localhost:5000/percent_pie_split_1')
    webbrowser.open('http://localhost:5000/when_you_meet_most')
    webbrowser.open('file:///Users/drew-sullivan/codingStuff/i_heart_meetings/i_heart_meetings/templates/report.html')
    webbrowser.open('file:///Users/drew-sullivan/codingStuff/i_heart_meetings/i_heart_meetings/tools/timer.html')


def _print_calendar_results_as_json(meetings):
    print(json.dumps(meetings, indent=4, sort_keys=True))


def generate_charts(data):

    @app.route("/when_you_meet_most")
    def chart():
        legend = 'test'
        # X axis - list
        labels = data[17]
        # Y axis - list
        values = list(data[18].values())
        return render_template('when_you_meet_most_line.html', values=values, labels=labels, legend=legend)

    @app.route('/percent_pie')
    def percent_pie():
        current_costs = 'Current Costs: {0} and {1} yearly'.format(
            data[3], data[2])
        ideal_costs = 'Ideal Meeting Investment: {0} and {1}'.format(
            data[12], data[11])
        savings = 'Potential Savings: {0} and {1}'.format(data[15],
            data[16])
        remainder = 100 - data[19]
        recovered_costs = data[19] - data[20]
        legend = 'Percentage of Time Spent in Meetings'
        labels = [current_costs, 'Non-Meetings', ideal_costs, savings]
        values = [data[19], remainder, data[20], recovered_costs]
        return render_template('percent_pie.html', values=values, labels=labels, legend=legend)

    @app.route('/percent_pie_split_1')
    def percent_pie_split_1():
        current_costs = 'Current Costs: {0} and {1} yearly'.format(
            data[3], data[2])
        ideal_costs = 'Ideal Meeting Investment: {0} and {1}'.format(
            data[12], data[11])
        savings = 'Potential Savings: {0} and {1}'.format(data[15],
            data[16])
        remainder = 100 - data[19]
        recovered_costs = data[19] - data[20]
        legend = 'Percentage of Time Spent in Meetings'
        labels = [current_costs, 'Non-Meetings']
        values = [data[19], remainder]
        return render_template('percent_pie_split_1.html', values=values, labels=labels, legend=legend)

    @app.route('/percent_pie_split_2')
    def percent_pie_split_2():
        current_costs = 'Current Costs: {0} and {1} yearly'.format(
            data[3], data[2])
        ideal_costs = 'Ideal Meeting Investment: {0} and {1}'.format(
            data[12], data[11])
        savings = 'Potential Savings: {0} and {1}'.format(data[15],
            data[16])
        remainder = 100 - data[19]
        recovered_costs = data[19] - data[20]
        legend = 'Percentage of Time Spent in Meetings'
        labels = ['Non-Meetings', ideal_costs, savings]
        values = [remainder, data[20], recovered_costs]
        return render_template('percent_pie_split_2.html', values=values, labels=labels, legend=legend)

    @app.route('/slack_printout_test')
    def slack_printout_test():
        weekly_cost_in_seconds_readable = data[0]
        return render_template('slack_printout_test.html', weekly_cost_in_seconds=weekly_cost_in_seconds)

    @app.route('/summary')
    def summary():
        weekly_costs = [data[1], data[0]]
        return render_template('summary.html', weekly_costs=weekly_costs)

if __name__ == '__main__':
    get_meeting_report()
    app.run(debug=False)
