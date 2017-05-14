#!/usr/bin/python

from model.report import Report

dc = report()

def _write_summary_html(self, *printable_data):
    f = open('templates/report.html','w')

    message = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="../static/style.css">
</head>
<body>
    <div class='report'>
        <table id="ihmReport">
            <caption>Report</caption>
            <tr> <th>Weekly Costs</th> </tr>
            <tr> <td>{0}</td> </tr>
            <tr> <td>{1}</td> </tr>
            <tr> <th>Averages</th> </tr>
            <tr> <th class='sub-category'>Costs Per Meeting</th> </tr>
            <tr> <td>{2}</td> </tr>
            <tr> <td>{3}</td> </tr>
            <tr> <th class='sub-category'>Meeting Duration</th> </tr>
            <tr> <td>{4}</td> </tr>
            <tr> <th>Projected Yearly Costs</th> </tr>
            <tr> <td>{5}</td> </tr>
            <tr> <td>{6}</td> </tr>
            <tr> <th>Top Meeting Times</th> </tr>
            <tr> <td>{7}</td> </tr>
            <tr> <td>{8}</td> </tr>
            <tr> <td>{9}</td> </tr>
            <tr> <th>Percent Time Spent in Meetings</th> </tr>
            <tr> <td>{10}</td> </tr>
            <tr> <th>Ideal Yearly Costs</th> </tr>
            <tr> <td>{11}</td> </tr>
            <tr> <td>{12}</td> </tr>
            <tr> <th>Potential Savings</th> </tr>
            <tr> <th class='sub-category'>Weekly</th> </tr>
            <tr> <td>{13}</td> </tr>
            <tr> <td>{14}</td> </tr>
            <tr> <th class='sub-category'>Yearly</th> </tr>
            <tr> <td>{15}</td> </tr>
            <tr> <td>{16}</td> </tr>
        </table>
    </div>
</body>
</html>""".format(self.printable_data[1],self.printable_data[0],
                  self.printable_data[5],
                  self.printable_data[4],self.printable_data[6],
                  self.printable_data[3],self.printable_data[2],
                  self.printable_data[7],
                  self.printable_data[8],self.printable_data[9],
                  self.printable_data[10],self.printable_data[12],
                  self.printable_data[11],
                  self.printable_data[13],self.printable_data[14],
                  self.printable_data[15],self.printable_data[16])

    f.write(message)
    f.close()
