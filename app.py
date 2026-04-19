from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import json, random

app = Flask(__name__)
app.secret_key = "ommp_final_system"

DATA_FILE = "users.json"

# ---------------- DATA ----------------
def load_users():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)

# ---------------- INDEX ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    users = load_users()

    username = request.form.get("username")
    password = request.form.get("password")

    if username == "admin" and password == "sousse123":
        session["user"] = "admin"
        session["role"] = "admin"
        return redirect("/admin")

    if username == "manager" and password == "OMMP123":
        session["user"] = "manager"
        session["role"] = "manager"
        return redirect("/manager")

    if username in users and users[username]["password"] == password:

    # ❌ user موش مقبول
     if users[username].get("status") != "approved":
        return "Account not validated by manager yet"

    session["user"] = username
    session["role"] = "user"
    return redirect("/reservation")

    return redirect("/")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    users = load_users()

    if request.method == "POST":
        u = request.form.get("username")

        users[u] = {
    "password": request.form.get("password"),
    "marque": request.form.get("marque"),
    "matricule": request.form.get("matricule"),
    "status": "pending",   # 👈 مهم: en attente validation
    "camion_status": [],
    "reservations": [],
    "reclamations": []
}

        save_users(users)
        return redirect("/")

    return render_template("register.html")

# ---------------- USER RESERVATION ----------------
@app.route("/reservation", methods=["GET", "POST"])
def reservation():

    if session.get("role") != "user":
        return redirect("/")

    users = load_users()
    user = session["user"]

    if request.method == "POST":
        users[user]["reservations"].append({
    "date": request.form.get("date"),
    "heure": request.form.get("heure"),
    "type": request.form.get("type"),
    "zone": request.form.get("zone"),
    "marchandise": request.form.get("marchandise"),  # 👈 زيدها هنا
    "code": None,
    "manager_reply": ""
})
        save_users(users)

    return render_template("reservation.html", user=user, users=users)

# ---------------- RECLAMATION ----------------
@app.route("/reclamation", methods=["POST"])
def reclamation():

    if session.get("role") != "user":
        return redirect("/")

    users = load_users()
    user = session["user"]

    message = request.form.get("message")

    if user in users:
        if "reclamations" not in users[user]:
            users[user]["reclamations"] = []

        users[user]["reclamations"].append({
            "message": message,
            "manager_reply": ""
        })

        save_users(users)

    return redirect("/reservation")

from collections import Counter
from flask import render_template, redirect, session

@app.route("/manager")
def manager():

    if session.get("role") != "manager":
        return redirect("/")

    users = load_users()

    # ================= KPIs =================
    total_users = len(users)

    total_reservations = 0
    confirmed_reservations = 0

    total_reclamations = 0
    pending_reclamations = 0
    answered_reclamations = 0

    camions_inside = 0

    # ================= MARCHANDISE (CONFIRMED ONLY) =================
    marchandise_confirmed = Counter()

    # ================= LOOP =================
    for u, data in users.items():

        for r in data.get("reservations", []):

            total_reservations += 1

            if r.get("code"):  # confirmed only
                confirmed_reservations += 1

                m = r.get("marchandise", "Unknown")
                marchandise_confirmed[m] += 1

        for rec in data.get("reclamations", []):
            total_reclamations += 1

            if rec.get("manager_reply"):
                answered_reclamations += 1
            else:
                pending_reclamations += 1

        for log in data.get("camion_logs", []):
            if log.get("event") == "E":
                camions_inside += 1
            elif log.get("event") == "S":
                camions_inside = max(0, camions_inside - 1)

    # ================= MARCHANDISE FINAL =================
    marchandise_stats = {}

    for m, count in marchandise_confirmed.items():
        marchandise_stats[m] = count  # ONLY confirmed count

    # ================= RATES =================
    confirmation_rate = round(
        (confirmed_reservations / total_reservations * 100)
        if total_reservations > 0 else 0,
        2
    )

    reclamation_rate = round(
        (total_reclamations / total_reservations * 100)
        if total_reservations > 0 else 0,
        2
    )

    # ================= RETURN =================
    return render_template(
        "manager.html",
        users=users,

        total_users=total_users,
        total_reservations=total_reservations,
        confirmed_reservations=confirmed_reservations,

        total_reclamations=total_reclamations,
        pending_reclamations=pending_reclamations,
        answered_reclamations=answered_reclamations,

        camions_inside=camions_inside,

        confirmation_rate=confirmation_rate,
        reclamation_rate=reclamation_rate,

        marchandise_stats=marchandise_stats
    )
# ---------------- MANAGER REPLY ----------------
@app.route("/manager_reply/<u>/<int:i>", methods=["POST"])
def manager_reply(u, i):

    if session.get("role") != "manager":
        return redirect("/")

    users = load_users()

    if u in users and i < len(users[u].get("reclamations", [])):
        users[u]["reclamations"][i]["manager_reply"] = request.form.get("reply", "")

        save_users(users)

    return redirect("/manager")

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")
    return render_template("admin.html", users=load_users())
#------------------camion status----------------
@app.route("/camion_status")
def camion_status():

    if session.get("role") != "admin":
        return redirect("/")

    users = load_users()
    return render_template("camion_status.html", users=users)

# ---------------- CONFIRM RESERVATION ----------------
@app.route("/confirm/<u>/<int:i>")
def confirm(u, i):

    if session.get("role") != "admin":
        return redirect("/")

    users = load_users()

    if u in users and i < len(users[u]["reservations"]):
        users[u]["reservations"][i]["code"] = str(random.randint(1000, 9999))
        save_users(users)

    return redirect("/admin")
#-----------------APPROVE USER----------------
@app.route("/approve/<u>")
def approve_user(u):
    if session.get("role") != "manager":
        return redirect("/")

    users = load_users()

    if u in users:
        users[u]["status"] = "approved"
        save_users(users)

    return redirect("/manager")
#-----------------REJECT USER----------------
@app.route("/reject/<u>")
def reject_user(u):
    if session.get("role") != "manager":
        return redirect("/")

    users = load_users()

    if u in users:
        users[u]["status"] = "rejected"
        save_users(users)

    return redirect("/manager")
#-----------------ENTREE CAMION----------------
@app.route("/camion_entree/<u>")
def camion_entree(u):

    if session.get("role") != "admin":
        return redirect("/")

    users = load_users()

    if u in users:
        users[u].setdefault("camion_status", []).append({
            "type": "E",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        save_users(users)

    return redirect("/camion_status")
#-----------------sortie camion----------------
@app.route("/camion_sortie/<u>")
def camion_sortie(u):

    if session.get("role") != "admin":
        return redirect("/")

    users = load_users()

    if u in users:
        users[u].setdefault("camion_status", []).append({
            "type": "S",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        save_users(users)

    return redirect("/camion_status")

#------------------delete stuiation de camion----------------
@app.route("/delete_camion_log/<user>/<int:index>")
def delete_camion_log(user, index):
    users = load_users()

    if user in users and "camion_logs" in users[user]:
        if index < len(users[user]["camion_logs"]):
            users[user]["camion_logs"].pop(index)

    save_users(users)
    return redirect("/admin")
#------------------camion situation----------------
@app.route("/camion_situation")
def camion_situation():

    if session.get("role") != "admin":
        return redirect("/")

    users = load_users()
    return render_template("camion_status.html", users=users)
# 
from datetime import datetime

@app.route("/camion_event/<u>/<event>")
def camion_event(u, event):

    if session.get("role") != "admin":
        return redirect("/")

    users = load_users()

    if u in users:
        users[u].setdefault("camion_logs", [])

        users[u]["camion_logs"].append({
            "event": event,  # E or S
            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

        save_users(users)

    return redirect("/camion_status")
# ---------------- EDIT RESERVATION ----------------
@app.route("/edit_res/<u>/<int:i>", methods=["GET", "POST"])
def edit_res(u, i):

    if session.get("role") != "admin":
        return redirect("/")

    users = load_users()

    if request.method == "POST":
        users[u]["reservations"][i]["date"] = request.form.get("date")
        users[u]["reservations"][i]["heure"] = request.form.get("heure")
        users[u]["reservations"][i]["type"] = request.form.get("type")
        users[u]["reservations"][i]["zone"] = request.form.get("zone")
        users[u]["reservations"][i]["marchandise"] = request.form.get("marchandise")

        save_users(users)
        return redirect("/admin")

    return render_template("edit_res.html", r=users[u]["reservations"][i], u=u, i=i)

# ---------------- EDIT USER ----------------
@app.route("/edit_user/<u>", methods=["GET", "POST"])
def edit_user(u):

    if session.get("role") != "admin":
        return redirect("/")

    users = load_users()

    if request.method == "POST":
        users[u]["marque"] = request.form.get("marque")
        users[u]["matricule"] = request.form.get("matricule")

        save_users(users)
        return redirect("/admin")

    return render_template("edit_user.html", user=u, data=users[u])

# ---------------- DELETE USER ----------------
@app.route("/delete/<u>")
def delete_user(u):

    if session.get("role") != "admin":
        return redirect("/")

    users = load_users()
    users.pop(u, None)
    save_users(users)

    return redirect("/admin")

# ---------------- DELETE RES ----------------
@app.route("/delete_res/<u>/<int:i>")
def delete_res(u, i):

    if session.get("role") != "admin":
        return redirect("/")

    users = load_users()

    if u in users and i < len(users[u]["reservations"]):
        users[u]["reservations"].pop(i)
        save_users(users)

    return redirect("/admin")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True, port=8000)