from flask import Flask, jsonify, request, render_template
import sqlite3
import csv
from datetime import datetime
import os
import re

app = Flask(__name__)
DB_PATH = "festival_muhurat.db"

def format_date(date_str):
    if not date_str or str(date_str).lower().strip() in ["date", ""]:
        return None

    date_str = str(date_str).strip()
    # Fixes Mundan/Business comma issues (e.g. "January 16,2027" -> "January 16, 2027")
    date_str = re.sub(r',(\d)', r', \1', date_str)
    date_str = re.sub(r'\s+,', ',', date_str)

    formats = [
        '%B %d, %Y', '%d %B, %Y', '%d %B %Y', 
        '%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d %b %Y'
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS festivals")
    cursor.execute("DROP TABLE IF EXISTS muhurat")
    cursor.execute("CREATE TABLE festivals (id INTEGER PRIMARY KEY AUTOINCREMENT, festival_name TEXT, year TEXT, date TEXT, day TEXT, hindu_month TEXT, tithi TEXT, description TEXT)")
    cursor.execute("CREATE TABLE muhurat (id INTEGER PRIMARY KEY AUTOINCREMENT, muhurat_name TEXT, year TEXT, date TEXT, timming TEXT, nakshtra TEXT, duration_in_minutes TEXT, yoga_1 TEXT, yoga_2 TEXT)")

    if os.path.exists("Festival_final.csv"):
        with open("Festival_final.csv", "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if len(row) >= 7 and row[0].strip() and "festival_name" not in row[0]:
                    cursor.execute("INSERT INTO festivals (festival_name,year,date,day,hindu_month,tithi,description) VALUES (?,?,?,?,?,?,?)", [c.strip() for c in row[:7]])

    if os.path.exists("Muhurat_Master_final_file.csv"):
        with open("Muhurat_Master_final_file.csv", "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if not row or len(row) < 5 or "Muhurat Name" in row[0] or not row[0].strip():
                    continue
                cursor.execute("INSERT INTO muhurat (muhurat_name,year,date,timming,nakshtra,duration_in_minutes,yoga_1,yoga_2) VALUES (?,?,?,?,?,?,?,?)", [c.strip() for c in row[:8]])
    conn.commit()
    conn.close()

@app.route('/')
def home(): return render_template('index.html')

@app.route('/api/muhurat')
def get_muhurat():
    year = request.args.get('year')
    category = request.args.get('category', '')
    # Map Naming to CSV keyword
    search_term = "Naam" if category == "Naming" else category
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM muhurat WHERE year = ? AND muhurat_name LIKE ?", (year, f"%{search_term}%"))
    data = {format_date(r[3]): {"timing":r[4],"nakshatra":r[5],"duration":r[6],"yoga1":r[7],"yoga2":r[8]} for r in cursor.fetchall() if format_date(r[3])}
    conn.close()
    return jsonify(data)

@app.route('/api/festivals')
def get_festivals():
    year = request.args.get('year')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM festivals WHERE year = ?", (year,))
    data = {format_date(r[3]): {"name":r[1],"tithi":r[6],"info":r[7]} for r in cursor.fetchall() if format_date(r[3])}
    conn.close()
    return jsonify(data)

if __name__ == '__main__':
    init_db()
    # REVERTED TO PREVIOUS FORMAT (Localhost only)
    app.run(debug=True)