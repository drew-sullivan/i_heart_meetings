import sqlite3

sqlite_file = '/Users/drew-sullivan/codingStuff/i_heart_meetings/db.sqlite'
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

c.execute('insert into meetings values(3, \'3rd string\')')

conn.commit()
conn.close()
