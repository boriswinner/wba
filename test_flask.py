import fdb
from flask import Flask
from flask import render_template
from flask import request
app = Flask(__name__)

@app.route("/", methods = ['GET'])
def mainpage():
    SEARCHFORM = """<h1>Search For Student Name</h1> 
    <form> 
        <input name = 'name' type = 'text'> 
        <input type = 'submit'> 
    </form>"""
    GETTABLES = """SELECT a.RDB$RELATION_NAME
    FROM RDB$RELATIONS a
    WHERE RDB$SYSTEM_FLAG = 0 AND RDB$RELATION_TYPE = 0
        """

    con = fdb.connect(dsn='BASE.FDB', user='sysdba', password='masterkey', charset='UTF8')
    searchname = request.args.get('name','')
    cur = con.cursor()
    query = "select * from teachers"
    if len(searchname) != 0:
        query += " WHERE name like \'%" + searchname + "%\'"
    cur.execute(query)
    f = cur.fetchall()
    s = ""
    for i in f:
        s += str(i) + '\r\n'
    cur.execute(GETTABLES)
    f1 = cur.fetchall()
    f1_list = []
    for i in f1:
        f1_list.append(str(i)[2:-4])
    return render_template("picker.html",
                           tables=f1_list) + str(f1) + SEARCHFORM + '<pre>' + str(searchname) + '\n' + s + '</pre>'

@app.route("/view_table", methods=['GET', 'POST'])
def viewTable():
    select = request.args.get("tablespicker")
    con = fdb.connect(dsn='BASE.FDB', user='sysdba', password='masterkey', charset='UTF8')
    cur = con.cursor()
    query = "select * from " + select
    cur.execute(query)
    f = cur.fetchall()
    s = ""
    for i in f:
        s += str(i) + '\r\n'
    return '<pre>' + s + '</pre>'
