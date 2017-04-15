from flask import Flask
from flask import render_template
from datetime import time


app = Flask(__name__)


@app.route("/simple_chart")
def chart():
    legend = 'Monthly Data'
    labels = ["January", "February", "March", "April", "May", "June", "July", "August"]
    values = [10, 9, 8, 7, 6, 4, 7, 8]
    return render_template('chart.html', values=values, labels=labels, legend=legend)


if __name__ == "__main__":
    app.run(debug=False)
