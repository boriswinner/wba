import fdb
from flask import Flask
from flask import request
app = Flask(__name__)

@app.route("/", methods = ['GET'])
def mainpage():
    SEARCHFORM = """<h1>Search For Student Name</h1> 
    <form> 
        <input name = 'name' type = 'text'> 
        <input type = 'submit'> 
    </form>"""

    con = fdb.connect(dsn='BASE.FDB', user='sysdba', password='masterkey')
    searchname = request.args.get('name','')
    cur = con.cursor()
    query = "select * from students"
    if len(searchname) != 0:
        query += " WHERE name like \'%" + searchname + "%\'"
    cur.execute(query)
    f = cur.fetchall()
    s = ""
    for i in f:
        s += str(i) + '\r\n'
    return SEARCHFORM + '<pre>' + str(searchname) + '\n' + s + '</pre>'