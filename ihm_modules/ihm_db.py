import csv
import datetime
import json
import sqlite3

DB_IHM_SQLITE = '/Users/drew-sullivan/coding_stuff/i_heart_meetings/i_heart_meetings/db_ihm.sqlite'
CSV_FILE = '/Users/drew-sullivan/coding_stuff/i_heart_meetings/i_heart_meetings/meetings_ihm.csv'
JSON_FIELDS = ('id', 'num', 'summary', 'start', 'end', 'duration', 'num_attendees')
JSON_FILE = '/Users/drew-sullivan/coding_stuff/i_heart_meetings/i_heart_meetings/meetings_ihm.json'

def write_csv_to_json():
    csv_file = open(CSV_FILE, 'r')
    json_file = open(JSON_FILE, 'w')
    field_names = JSON_FIELDS
    reader = csv.DictReader(csv_file, field_names)
    for row in reader:
        json.dump(row, json_file, sort_keys=True, indent=4, separators=(',', ': '))
        json_file.write('\n')

def write_db_to_csv():
    with sqlite3.connect(DB_IHM_SQLITE) as conn:
        csvWriter = csv.writer(open(CSV_FILE, 'w'))
        c = conn.cursor()
        c.execute('SELECT * from meetings')
        rows = c.fetchall()
        csvWriter.writerows(rows)

def _add_row_to_db(meetings_list):
    for meeting in meetings_list:
        id = str(datetime.datetime.now())
        start = str(meeting.start)
        end = str(meeting.end)
        duration = str(meeting.duration)
        conn = sqlite3.connect(DB_IHM_SQLITE)
        c = conn.cursor()
        c.execute('INSERT INTO meetings VALUES(?,?,?,?,?,?,?)',
                  (id, meeting.num, meeting.summary,
                   start, end, duration,
                   meeting.num_attendees))
        conn.commit()
    conn.close()
