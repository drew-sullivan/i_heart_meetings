import argparse

def get_meeting_report(slack=False):

    #  gc = Google_Connection()
    #  meetings = gc.meetings
    #
    #  rep = Report(meetings)

    if slack:
        #  rep.post_report_to_slack()
        print('posted to slack')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--slack', help='post to slack',
        action='store_true')
    args = parser.parse_args()
    args = vars(args)
    get_meeting_report(**args)
