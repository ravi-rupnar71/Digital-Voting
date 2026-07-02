

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import re
import math
import random
import smtplib
from functools import wraps
from datetime import datetime, timedelta
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change_this_to_any_random_secret_text"  # change before submitting your project

DB_FILE = "database.db"
OTP_EXPIRY_SECONDS = 120  


SEND_REAL_EMAILS = True

EMAIL_ADDRESS = "ravirupnar771@gmail.com"     
EMAIL_PASSWORD = ""        

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email):
    return bool(EMAIL_REGEX.match(email or ""))


def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def send_email(to_email, subject, body):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        flash(f"Email sent to {to_email}.")
    except Exception as e:
        flash(f"Note: could not send email to {to_email} ({e}).")


# ================= LOGIN-REQUIRED DECORATORS


def voter_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'voter':
            flash("Please login as a voter to continue.")
            return redirect(url_for('voter_login'))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Please login as admin to access this page.")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapper


# ================= HOME PAGE =================
@app.route('/')
def home():
    return render_template('home.html')


# ================= VOTER LOGIN (Step 1: password) =================
@app.route('/voter/login', methods=['GET', 'POST'])
def voter_login():
    if request.method == 'POST':
        voter_id = request.form['voter_id'].strip()
        password = request.form['password']

        conn = db()
        voter = conn.execute(
            "SELECT * FROM voters WHERE voter_id = ?", (voter_id,)
        ).fetchone()
        conn.close()

        if voter is None or not check_password_hash(voter['password'], password):
            flash("Invalid Voter ID or password.")
            return redirect(url_for('voter_login'))
    
        otp = f"{random.randint(0, 999999):06d}"
        session.clear()
        session['pending_voter_id'] = voter['voter_id']
        session['pending_voter_name'] = voter['name']
        session['otp'] = otp
        session['otp_time'] = datetime.now().isoformat()

        send_email(
            voter['email'],
            "Your OTP for Digital Voting System",
            f"Hello {voter['name']},\n\n"
            f"Your OTP is: {otp}\n"
            f"It is valid for {OTP_EXPIRY_SECONDS // 60} minutes.\n\n"
            f"Enter this code to continue to voting."
        )
        return redirect(url_for('voter_otp'))

    return render_template('voter_login.html')



# ================= VOTER LOGIN (Step 2: OTP) =================
@app.route('/voter/otp', methods=['GET', 'POST'])
def voter_otp():
    # Must have completed step 1 (password check) first
    if 'pending_voter_id' not in session or 'otp' not in session:
        return redirect(url_for('voter_login'))

    expiry_time = datetime.fromisoformat(session['otp_time']) + timedelta(seconds=OTP_EXPIRY_SECONDS)
    if datetime.now() > expiry_time:
        session.clear()
        flash("OTP expired. Please login again.")
        return redirect(url_for('voter_login'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()

        if entered_otp == session['otp']:
            # OTP correct -> NOW the voter is actually logged in.
            voter_id = session['pending_voter_id']
            voter_name = session['pending_voter_name']
            session.clear()
            session['role'] = 'voter'
            session['voter_id'] = voter_id
            session['voter_name'] = voter_name
            return redirect(url_for('vote'))

        flash("Incorrect OTP. Please try again.")

    return render_template('voter_otp.html')



# ================= ADMIN LOGIN =================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = db()
        admin_user = conn.execute(
            "SELECT * FROM admin WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if admin_user is None or not check_password_hash(admin_user['password'], password):
            flash("Invalid admin username or password.")
            return redirect(url_for('admin_login'))

        session.clear()
        session['role'] = 'admin'
        session['admin_username'] = admin_user['username']
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_login.html')



# ================= VOTING =================
@app.route('/vote', methods=['GET', 'POST'])
@voter_required
def vote():
    conn = db()
    voter = conn.execute(
        "SELECT * FROM voters WHERE voter_id = ?", (session['voter_id'],)
    ).fetchone()

    if voter['has_voted'] == 1:
        conn.close()
        return redirect(url_for('already_voted'))

    if request.method == 'POST':
        candidate_id = request.form.get('candidate')

        if not candidate_id:
            flash("Please select a candidate before submitting.")
            conn.close()
            return redirect(url_for('vote'))

        try:
            conn.execute(
                "INSERT INTO votes (voter_id, candidate_id) VALUES (?, ?)",
                (voter['voter_id'], candidate_id)
            )
            conn.execute(
                "UPDATE candidates SET votes = votes + 1 WHERE id = ?", (candidate_id,)
            )
            conn.execute(
                "UPDATE voters SET has_voted = 1 WHERE voter_id = ?", (voter['voter_id'],)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # The UNIQUE constraint on votes.voter_id caught a duplicate vote
            conn.close()
            flash("Our records show you have already voted.")
            return redirect(url_for('already_voted'))

        conn.close()

        send_email(
            voter['email'],
            "Your vote has been recorded",
            f"Hello {voter['name']},\n\n"
            f"This confirms your vote in the Digital Voting System has been "
            f"recorded successfully.\n\nThank you for participating!"
        )
        return redirect(url_for('already_voted'))

    candidates = conn.execute("SELECT * FROM candidates").fetchall()
    conn.close()
    return render_template('vote.html', candidates=candidates, voter_name=voter['name'])


@app.route('/already_voted')
@voter_required
def already_voted():
    return render_template('already_voted.html')


# ================= RESULTS (public) =================
PIE_COLORS = ["#b8862e", "#1e2a38", "#9b2c2c", "#2f6f4e", "#6b5b95", "#3a7d7a"]


def build_pie_slices(candidates):
   
    total = sum(c['votes'] for c in candidates)
    slices = []
    if total == 0:
        return slices, total

    cx, cy, r = 100, 100, 90
    start_angle = -90  # start at 12 o'clock

    for i, c in enumerate(candidates):
        fraction = c['votes'] / total
        angle = fraction * 360
        end_angle = start_angle + angle
        color = PIE_COLORS[i % len(PIE_COLORS)]

        full_circle = round(fraction, 6) >= 1.0
        path = None
        if not full_circle and angle > 0:
            start_rad = math.radians(start_angle)
            end_rad = math.radians(end_angle)
            x1 = cx + r * math.cos(start_rad)
            y1 = cy + r * math.sin(start_rad)
            x2 = cx + r * math.cos(end_rad)
            y2 = cy + r * math.sin(end_rad)
            large_arc = 1 if angle > 180 else 0
            path = f"M{cx},{cy} L{x1:.2f},{y1:.2f} A{r},{r} 0 {large_arc} 1 {x2:.2f},{y2:.2f} Z"

        slices.append({
            "name": c['name'], "votes": c['votes'],
            "percent": round(fraction * 100, 1), "color": color,
            "path": path, "full_circle": full_circle,
        })
        start_angle = end_angle

    return slices, total


@app.route('/results')
def results():
    conn = db()
    candidates = conn.execute(
        "SELECT * FROM candidates ORDER BY votes DESC"
    ).fetchall()
    conn.close()

    slices, total = build_pie_slices(candidates)
    return render_template('results.html', candidates=candidates, slices=slices, total=total)



# ================= ADMIN DASHBOARD =================
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = db()
    candidates = conn.execute("SELECT * FROM candidates ORDER BY id").fetchall()
    voters = conn.execute("SELECT * FROM voters ORDER BY id").fetchall()
    conn.close()
    return render_template('admin_dashboard.html', candidates=candidates, voters=voters)


# ================= ADD CANDIDATE (admin only) =================
@app.route('/admin/add_candidate', methods=['GET', 'POST'])
@admin_required
def add_candidate():
    if request.method == 'POST':
        name = request.form['name'].strip()
        party = request.form['party'].strip()
        email = request.form['email'].strip()

        if not name or not party or not email:
            flash("All fields are required.")
            return redirect(url_for('add_candidate'))

        if not is_valid_email(email):
            flash("Please enter a valid email address for the candidate.")
            return redirect(url_for('add_candidate'))

        conn = db()
        try:
            conn.execute(
                "INSERT INTO candidates (name, party, email) VALUES (?, ?, ?)",
                (name, party, email)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("A candidate with this email already exists.")
            conn.close()
            return redirect(url_for('add_candidate'))
        conn.close()

        send_email(
            email,
            "You have been added as a candidate",
            f"Hello {name},\n\n"
            f"You have been registered as a candidate for '{party}' in the "
            f"Digital Voting System election.\n\nGood luck!"
        )
        flash(f"Candidate '{name}' added successfully.")
        return redirect(url_for('admin_dashboard'))

    return render_template('add_candidate.html')


# ================= ADD VOTER (admin only) =================
@app.route('/admin/add_voter', methods=['GET', 'POST'])
@admin_required
def add_voter():
    if request.method == 'POST':
        voter_id = request.form['voter_id'].strip().upper()
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        if not voter_id or not name or not email or not password:
            flash("All fields are required.")
            return redirect(url_for('add_voter'))

        if not is_valid_email(email):
            flash("Please enter a valid email address for the voter.")
            return redirect(url_for('add_voter'))

        conn = db()
        try:
            conn.execute(
                "INSERT INTO voters (voter_id, name, email, password) VALUES (?, ?, ?, ?)",
                (voter_id, name, email, generate_password_hash(password))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("A voter with this Voter ID or email already exists.")
            conn.close()
            return redirect(url_for('add_voter'))
        conn.close()

        send_email(
            email,
            "Your Digital Voting System account",
            f"Hello {name},\n\n"
            f"You have been registered to vote.\n\n"
            f"Voter ID: {voter_id}\nPassword: {password}\n\n"
            f"Please keep these details confidential."
        )
        flash(f"Voter '{name}' added successfully.")
        return redirect(url_for('admin_dashboard'))

    return render_template('add_voter.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('home'))


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
