#!/isr/bin/env python

import argparse
import csv
import datetime
import httplib2
import ihm_db
import ihm_slack
import json
import os
import pdb
import random
import sys
import textwrap
import time
import webbrowser

from apiclient import discovery
from datetime import time
from datetime import timedelta
from flask import Flask
from flask import render_template
from model.calendar_connection import CalendarConnection
from model.meeting import Meeting
from model.report import Report
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


help = textwrap.dedent("""
    """)

app = Flask(__name__)


def get_meeting_report():

    cc = CalendarConnection()
    meetings = cc.meetings
    #  _print_calendar_results_as_json(meetings)

    rep = Report(meetings)

    data = rep.printable_data
    rep.write_report_html(data)
    #  ihm_slack.post_report_to_slack(*data)
    #
    meetings_list = rep.meetings_list
    ihm_db._add_row_to_db(meetings_list)
    ihm_db.write_db_to_csv()
    ihm_db.write_csv_to_json()

    generate_charts(data)
    open_charts_in_browser()


def open_charts_in_browser():
    #  webbrowser.open('http://localhost:5000/percent_pie_split_2')
    #  webbrowser.open('http://localhost:5000/percent_pie_split_1')
    percent_pie_path = 'http://localhost:5000/percent_pie'
    when_you_meet_most_path = 'http://localhost:5000/when_you_meet_most'
    report_path = ('/Users/Drew/coding_stuff/i_heart_meetings/'
                   'i_heart_meetings/templates/report.html')
    timer_path = ('/Users/Drew/coding_stuff/i_heart_meetings/'
                  'i_heart_meetings/tools/timer.html')
    hello_path = ('/Users/Drew/coding_stuff/i_heart_meetings/'
                  'i_heart_meetings/templates/hello_py_ohio.html')

    webbrowser.open(percent_pie_path)
    webbrowser.open(when_you_meet_most_path)
    webbrowser.open('file://' + os.path.realpath(timer_path))
    webbrowser.open('file://' + os.path.realpath(report_path))


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
        return render_template(
            'when_you_meet_most_line.html',
            values=values,
            labels=labels, legend=legend
        )

    @app.route('/percent_pie')
    def percent_pie():
        current_costs = 'Current Costs: {0} and {1} yearly'.format(
            data[3], data[2])
        ideal_costs = 'Ideal Meeting Investment: {0} and {1}'.format(
            data[12], data[11])
        savings = 'Potential Savings: {0} and {1}'.format(data[15], data[16])
        remainder = 100 - data[19]
        recovered_costs = data[19] - data[20]
        legend = 'Percentage of Time Spent in Meetings'
        labels = [current_costs, 'Non-Meetings', ideal_costs, savings]
        values = [data[19], remainder, data[20], recovered_costs]
        return render_template(
            'percent_pie.html',
            values=values,
            labels=labels, legend=legend
        )

    @app.route('/percent_pie_split_1')
    def percent_pie_split_1():
        current_costs = 'Current Costs: {0} and {1} yearly'.format(
            data[3], data[2])
        ideal_costs = 'Ideal Meeting Investment: {0} and {1}'.format(
            data[12], data[11])
        savings = 'Potential Savings: {0} and {1}'.format(data[15], data[16])
        remainder = 100 - data[19]
        recovered_costs = data[19] - data[20]
        legend = 'Percentage of Time Spent in Meetings'
        labels = [current_costs, 'Non-Meetings']
        values = [data[19], remainder]
        return render_template(
            'percent_pie_split_1.html',
            values=values,
            labels=labels, legend=legend
        )

    @app.route('/percent_pie_split_2')
    def percent_pie_split_2():
        current_costs = 'Current Costs: {0} and {1} yearly'.format(
            data[3], data[2])
        ideal_costs = 'Ideal Meeting Investment: {0} and {1}'.format(
            data[12], data[11])
        savings = 'Potential Savings: {0} and {1}'.format(data[15], data[16])
        remainder = 100 - data[19]
        recovered_costs = data[19] - data[20]
        legend = 'Percentage of Time Spent in Meetings'
        labels = ['Non-Meetings', ideal_costs, savings]
        values = [remainder, data[20], recovered_costs]
        return render_template(
            'percent_pie_split_2.html',
            values=values,
            labels=labels, legend=legend
        )

    @app.route('/slack_printout_test')
    def slack_printout_test():
        weekly_cost_in_seconds_readable = data[0]
        return render_template(
            'slack_printout_test.html',
            weekly_cost_in_seconds=weekly_cost_in_seconds
        )

    @app.route('/summary')
    def summary():
        weekly_costs = [data[1], data[0]]
        return render_template('summary.html', weekly_costs=weekly_costs)

if __name__ == '__main__':
    get_meeting_report()
    app.run(debug=False)
