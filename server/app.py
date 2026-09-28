from flask import (
    Flask,
    Response,
    jsonify,
    request,
    render_template,
    session,
    redirect,
    send_file,
    send_from_directory
)

from flask_cors import CORS

from datetime import datetime

import pytz

import sqlite3

import csv

import io

import os

import threading

import time


# =====================================
# FLASK APP
# =====================================

app = Flask(__name__)

CORS(app)

app.secret_key = "smartparking_secret_key_123"


# =====================================
# ADMIN LOGIN
# =====================================

ADMIN_USERNAME = "admin"

ADMIN_PASSWORD = "1234"


# =====================================
# DATABASE LOCATION
# =====================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


DATABASE = os.path.join(
    BASE_DIR,
    "parking.db"
)


# =====================================
# RASPBERRY PI CAMERA
# =====================================

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "captures"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


latest_frame = None

latest_frame_time = 0.0

latest_capture_url = None


frame_lock = threading.Lock()


CAMERA_OFFLINE_SECONDS = 5.0


# =====================================
# CREATE DATABASE
# =====================================

def create_database():

    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    # ===============================
    # PARKING HISTORY
    # ===============================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_history
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        time TEXT,

        slot1 TEXT,

        slot2 TEXT,

        inside INTEGER,

        entries INTEGER,

        exit INTEGER,

        event TEXT,

        image_path TEXT
    )
    """)


    # ===============================
    # MIGRATE OLD DATABASE
    # ===============================

    history_columns = [
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(parking_history)"
        ).fetchall()
    ]


    if "image_path" not in history_columns:

        cursor.execute(
            """
            ALTER TABLE parking_history
            ADD COLUMN image_path TEXT
            """
        )


    # ===============================
    # LIVE PARKING STATUS
    # ===============================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_status
    (
        id INTEGER PRIMARY KEY,

        slot1 TEXT,

        slot2 TEXT,

        distance1 REAL,

        distance2 REAL,

        available INTEGER,

        inside INTEGER,

        entries INTEGER,

        exit INTEGER,

        event TEXT,

        last_update TEXT
    )
    """)


    # ===============================
    # RESERVATION SYSTEM
    # ===============================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservations
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        phone TEXT,

        slot TEXT,

        date TEXT,

        time TEXT,

        status TEXT
    )
    """)


    # ===============================
    # DEFAULT PARKING DATA
    # ===============================

    cursor.execute("""
    INSERT OR IGNORE INTO parking_status
    VALUES
    (
        1,

        'EMPTY',

        'EMPTY',

        0,

        0,

        2,

        0,

        0,

        0,

        'NONE',

        '--:--:--'
    )
    """)


    conn.commit()

    conn.close()


create_database()


# =====================================
# LIVE PARKING DATA
# =====================================

parking_data = {

    "slot1":
    "EMPTY",

    "slot2":
    "EMPTY",

    "distance1":
    0,

    "distance2":
    0,

    "available":
    2,

    "inside":
    0,

    "entries":
    0,

    "exit":
    0,

    "event":
    "NONE",

    "gate":
    "CLOSED",

    "buzzer":
    "OFF",

    "last_update":
    "--:--:--"

}


# =====================================
# EVENT MEMORY
# =====================================

last_event_key = None


# =====================================
# TIME FUNCTION
# =====================================

def get_bd_time():

    tz = pytz.timezone(
        "Asia/Dhaka"
    )

    return datetime.now(tz).strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )


# =====================================
# CAMERA STATUS
# =====================================

def camera_is_online():

    return (
        latest_frame is not None
        and
        (time.time() - latest_frame_time)
        <= CAMERA_OFFLINE_SECONDS
    )


# =====================================
# LOAD DATABASE DATA
# =====================================

def load_database():

    global last_event_key


    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            slot1,
            slot2,
            distance1,
            distance2,
            available,
            inside,
            entries,
            exit,
            event,
            last_update
        FROM parking_status
        WHERE id=1
        """
    )


    row = cursor.fetchone()


    conn.close()


    if row:

        parking_data["slot1"] = row[0]

        parking_data["slot2"] = row[1]

        parking_data["distance1"] = row[2]

        parking_data["distance2"] = row[3]

        parking_data["available"] = row[4]

        parking_data["inside"] = row[5]

        parking_data["entries"] = row[6]

        parking_data["exit"] = row[7]

        parking_data["event"] = row[8]

        parking_data["last_update"] = row[9]


        if row[8] in ["ENTRY", "EXIT"]:

            last_event_key = (
                row[8],
                row[6],
                row[7]
            )

        else:

            last_event_key = None


load_database()


# =====================================
# SAVE CURRENT STATUS
# =====================================

def update_status_database():

    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE parking_status
        SET
            slot1=?,
            slot2=?,
            distance1=?,
            distance2=?,
            available=?,
            inside=?,
            entries=?,
            exit=?,
            event=?,
            last_update=?
        WHERE id=1
        """,

        (
            parking_data["slot1"],
            parking_data["slot2"],
            parking_data["distance1"],
            parking_data["distance2"],
            parking_data["available"],
            parking_data["inside"],
            parking_data["entries"],
            parking_data["exit"],
            parking_data["event"],
            parking_data["last_update"]
        )
    )


    conn.commit()

    conn.close()


# =====================================
# SAVE LATEST CAMERA FRAME
# =====================================

def save_latest_frame_capture(event):

    global latest_capture_url


    if event not in ["ENTRY", "EXIT"]:

        return None


    with frame_lock:

        frame = latest_frame


    if frame is None:

        return None


    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )


    filename = (
        f"{event.lower()}_{timestamp}.jpg"
    )


    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )


    try:

        with open(
            filepath,
            "wb"
        ) as file:

            file.write(frame)


        latest_capture_url = (
            f"/captures/{filename}"
        )


        return filename


    except OSError as error:

        print(
            "Could not save camera capture:",
            error
        )

        return None


# =====================================
# FIND EVENT HISTORY RECORD
# =====================================

def get_latest_history_event_id(
    event,
    entries_value,
    exit_value
):

    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT id
        FROM parking_history
        WHERE event=?
        AND entries=?
        AND exit=?
        ORDER BY id DESC
        LIMIT 1
        """,

        (
            event,
            entries_value,
            exit_value
        )
    )


    row = cursor.fetchone()


    conn.close()


    if row:

        return row[0]


    return None


# =====================================
# SAVE ENTRY / EXIT HISTORY
# =====================================

def save_history_event(
    image_path=None
):

    global last_event_key


    event = parking_data["event"]


    if event not in ["ENTRY", "EXIT"]:

        return None


    event_key = (
        event,
        parking_data["entries"],
        parking_data["exit"]
    )


    if event_key == last_event_key:

        return None


    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO parking_history
        (
            time,
            slot1,
            slot2,
            inside,
            entries,
            exit,
            event,
            image_path
        )
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """,

        (
            parking_data["last_update"],

            parking_data["slot1"],

            parking_data["slot2"],

            parking_data["inside"],

            parking_data["entries"],

            parking_data["exit"],

            event,

            image_path
        )
    )


    row_id = cursor.lastrowid


    conn.commit()

    conn.close()


    last_event_key = event_key


    return row_id

# =====================================
# ESP32 UPDATE API
# =====================================

@app.route(
    "/update",
    methods=["POST"]
)
def update():

    global parking_data


    # ===============================
    # RECEIVE ESP32 DATA
    # ===============================

    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify(
            {
                "error": "No data received"
            }
        ), 400


    # ===============================
    # SLOT STATUS
    # ===============================

    parking_data["slot1"] = data.get(
        "slot1",
        parking_data["slot1"]
    )


    parking_data["slot2"] = data.get(
        "slot2",
        parking_data["slot2"]
    )


    # ===============================
    # DISTANCE
    # ===============================

    try:

        parking_data["distance1"] = float(
            data.get(
                "distance1",
                parking_data["distance1"]
            )
        )

    except (
        TypeError,
        ValueError
    ):

        parking_data["distance1"] = 0


    try:

        parking_data["distance2"] = float(
            data.get(
                "distance2",
                parking_data["distance2"]
            )
        )

    except (
        TypeError,
        ValueError
    ):

        parking_data["distance2"] = 0


    # ===============================
    # PARKING COUNTS
    # ===============================

    try:

        parking_data["available"] = int(
            data.get(
                "available",
                parking_data["available"]
            )
        )

    except (
        TypeError,
        ValueError
    ):

        parking_data["available"] = 0


    try:

        parking_data["inside"] = int(
            data.get(
                "inside",
                parking_data["inside"]
            )
        )

    except (
        TypeError,
        ValueError
    ):

        parking_data["inside"] = 0


    try:

        parking_data["entries"] = int(
            data.get(
                "entries",
                parking_data["entries"]
            )
        )

    except (
        TypeError,
        ValueError
    ):

        parking_data["entries"] = 0


    try:

        parking_data["exit"] = int(
            data.get(
                "exit",
                parking_data["exit"]
            )
        )

    except (
        TypeError,
        ValueError
    ):

        parking_data["exit"] = 0


    # ===============================
    # EVENT
    # ===============================

    parking_data["event"] = str(
        data.get(
            "event",
            "NONE"
        )
    ).upper()


    # ===============================
    # GATE
    # ===============================

    parking_data["gate"] = data.get(
        "gate",
        parking_data["gate"]
    )


    # ===============================
    # BUZZER
    # ===============================

    parking_data["buzzer"] = data.get(
        "buzzer",
        parking_data["buzzer"]
    )


    # ===============================
    # TIME
    # ===============================

    parking_data["last_update"] = get_bd_time()


    # ===============================
    # SAVE CURRENT STATUS
    # ===============================

    update_status_database()


    # ===============================
    # ENTRY / EXIT EVENT
    # ===============================

    capture_filename = None

    history_id = None


    if parking_data["event"] in [
        "ENTRY",
        "EXIT"
    ]:

        # Save the latest live Raspberry Pi
        # frame immediately.

        capture_filename = (
            save_latest_frame_capture(
                parking_data["event"]
            )
        )


        # Save event history and attach
        # the current frame if available.

        history_id = save_history_event(
            capture_filename
        )


    # ===============================
    # RESPONSE
    # ===============================

    return jsonify(
        {
            "status": "updated",

            "data": parking_data,

            "capture":
                (
                    f"/captures/{capture_filename}"
                    if capture_filename
                    else None
                ),

            "history_id":
                history_id
        }
    ), 200


# =====================================
# RASPBERRY PI LIVE FRAME UPLOAD
# =====================================

@app.route(
    "/api/upload-frame",
    methods=["POST"]
)
def upload_frame():

    global latest_frame

    global latest_frame_time


    # ===============================
    # CHECK IMAGE
    # ===============================

    if "image" not in request.files:

        return jsonify(
            {
                "error":
                "No frame received"
            }
        ), 400


    image_file = request.files["image"]


    # ===============================
    # READ IMAGE
    # ===============================

    frame = image_file.read()


    if not frame:

        return jsonify(
            {
                "error":
                "Empty frame"
            }
        ), 400


    # ===============================
    # STORE LATEST FRAME
    # ===============================

    with frame_lock:

        latest_frame = frame

        latest_frame_time = time.time()


    return jsonify(
        {
            "status":
            "frame received"
        }
    ), 200


# =====================================
# GENERATE LIVE VIDEO STREAM
# =====================================

def gen_frames():

    while True:

        with frame_lock:

            frame = latest_frame


        if frame is None:

            time.sleep(0.1)

            continue


        yield (

            b"--frame\r\n"

            b"Content-Type: image/jpeg\r\n\r\n"

            + frame

            + b"\r\n"
        )


        # Prevent unnecessary CPU usage.

        time.sleep(0.03)


# =====================================
# VIDEO FEED
# =====================================

@app.route(
    "/video_feed"
)
def video_feed():

    return Response(
        gen_frames(),

        mimetype=
        "multipart/x-mixed-replace; boundary=frame"
    )


# =====================================
# RASPBERRY PI HIGH QUALITY PHOTO
# =====================================

@app.route(
    "/api/upload-photo",
    methods=["POST"]
)
def upload_photo():

    global latest_capture_url


    # ===============================
    # CHECK PHOTO
    # ===============================

    if "photo" not in request.files:

        return jsonify(
            {
                "error":
                "No photo file"
            }
        ), 400


    photo = request.files["photo"]


    # ===============================
    # EVENT
    # ===============================

    event = str(
        request.form.get(
            "event",
            ""
        )
    ).strip().upper()


    # ===============================
    # COUNTERS
    # ===============================

    try:

        entries_value = int(
            request.form.get(
                "entries",
                parking_data["entries"]
            )
        )

        exit_value = int(
            request.form.get(
                "exit",
                parking_data["exit"]
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify(
            {
                "error":
                "Invalid entries or exit value"
            }
        ), 400


    # ===============================
    # VALID EVENT
    # ===============================

    if event not in [
        "ENTRY",
        "EXIT"
    ]:

        return jsonify(
            {
                "error":
                "event must be ENTRY or EXIT"
            }
        ), 400


    # ===============================
    # CREATE FILENAME
    # ===============================

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )


    filename = (
        f"{event.lower()}_high_{timestamp}.jpg"
    )


    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )


    # ===============================
    # SAVE PHOTO
    # ===============================

    try:

        photo.save(filepath)

    except OSError as error:

        return jsonify(
            {
                "error":
                f"Could not save photo: {error}"
            }
        ), 500


    # ===============================
    # FIND MATCHING HISTORY
    # ===============================

    event_id = get_latest_history_event_id(
        event,
        entries_value,
        exit_value
    )


    # ===============================
    # UPDATE HISTORY PHOTO
    # ===============================

    if event_id is not None:

        conn = sqlite3.connect(
            DATABASE
        )

        cursor = conn.cursor()


        cursor.execute(
            """
            UPDATE parking_history

            SET image_path=?

            WHERE id=?
            """,

            (
                filename,
                event_id
            )
        )


        conn.commit()

        conn.close()


    else:

        # Fallback:
        # If the Pi photo arrives before
        # the normal history row exists.

        conn = sqlite3.connect(
            DATABASE
        )

        cursor = conn.cursor()


        cursor.execute(
            """
            INSERT INTO parking_history
            (
                time,
                slot1,
                slot2,
                inside,
                entries,
                exit,
                event,
                image_path
            )

            VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,

            (
                get_bd_time(),

                parking_data["slot1"],

                parking_data["slot2"],

                parking_data["inside"],

                entries_value,

                exit_value,

                event,

                filename
            )
        )


        event_id = cursor.lastrowid


        conn.commit()

        conn.close()


    # ===============================
    # SAVE LATEST PHOTO URL
    # ===============================

    latest_capture_url = (
        f"/captures/{filename}"
    )


    return jsonify(
        {
            "status":
            "success",

            "filename":
            filename,

            "url":
            latest_capture_url,

            "history_id":
            event_id
        }
    ), 200


# =====================================
# SERVE SAVED CAPTURE
# =====================================

@app.route(
    "/captures/<path:filename>"
)
def get_capture(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# =====================================
# LIVE STATUS
# =====================================

@app.route(
    "/status"
)
def status():

    response = dict(
        parking_data
    )


    # Raspberry Pi camera state

    response["camera_online"] = (
        camera_is_online()
    )


    # Latest saved photo

    response["latest_capture"] = (
        latest_capture_url
    )


    return jsonify(
        response
    )


# =====================================
# SLOT UPDATE API
# =====================================

@app.route(
    "/api/update-slot",
    methods=["POST"]
)
def api_update_slot():

    global parking_data


    data = request.get_json(
        silent=True
    ) or {}


    slot_id = str(
        data.get(
            "slot_id",
            ""
        )
    ).lower()


    status_value = str(
        data.get(
            "status",
            ""
        )
    ).upper()


    # ===============================
    # SLOT 1
    # ===============================

    if slot_id in [
        "slot1",
        "1",
        "a1"
    ]:

        parking_data["slot1"] = (
            status_value
        )


    # ===============================
    # SLOT 2
    # ===============================

    elif slot_id in [
        "slot2",
        "2",
        "a2"
    ]:

        parking_data["slot2"] = (
            status_value
        )


    else:

        return jsonify(
            {
                "error":
                "Invalid slot_id"
            }
        ), 400


    # ===============================
    # RECALCULATE AVAILABLE
    # ===============================

    available = 0


    if parking_data["slot1"] in [
        "EMPTY",
        "AVAILABLE"
    ]:

        available += 1


    if parking_data["slot2"] in [
        "EMPTY",
        "AVAILABLE"
    ]:

        available += 1


    parking_data["available"] = (
        available
    )


    parking_data["last_update"] = (
        get_bd_time()
    )


    update_status_database()


    return jsonify(
        {
            "status":
            "success",

            "data":
            parking_data
        }
    ), 200


# =====================================
# DASHBOARD PAGE
# =====================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =====================================
# HISTORY PAGE
# =====================================

@app.route("/history")
def history():

    return render_template(
        "history.html"
    )
# =====================================
# HISTORY DATA API
# =====================================

@app.route(
    "/history-data"
)
def history_data():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            id,
            time,
            slot1,
            slot2,
            inside,
            entries,
            exit,
            event,
            image_path
        FROM parking_history
        ORDER BY id DESC
        LIMIT 100
        """
    )


    rows = cursor.fetchall()

    conn.close()


    result = []


    for row in rows:

        result.append(
            {
                "id":
                    row["id"],

                "time":
                    row["time"],

                "slot1":
                    row["slot1"],

                "slot2":
                    row["slot2"],

                "cars_inside":
                    row["inside"],

                "total_entries":
                    row["entries"],

                "total_exit":
                    row["exit"],

                "event":
                    row["event"],

                "image_path":
                    row["image_path"]
            }
        )


    return jsonify(
        result
    )


# =====================================
# RESERVATION PAGE
# =====================================

@app.route(
    "/reservation"
)
def reservation():

    return render_template(
        "reservation.html"
    )


# =====================================
# CREATE RESERVATION
# =====================================

@app.route(
    "/reserve-slot",
    methods=["POST"]
)
def reserve_slot():

    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify(
            {
                "status":
                    "error",

                "message":
                    "No data received"
            }
        ), 400


    name = data.get(
        "name",
        ""
    )


    phone = data.get(
        "phone",
        ""
    )


    slot = data.get(
        "slot",
        ""
    )


    date = data.get(
        "date",
        ""
    )


    time_value = data.get(
        "time",
        ""
    )


    # ===============================
    # VALIDATE SLOT
    # ===============================

    if slot not in [
        "Slot 1",
        "Slot 2"
    ]:

        return jsonify(
            {
                "status":
                    "error",

                "message":
                    "Invalid Slot"
            }
        ), 400


    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    # ===============================
    # CHECK EXISTING BOOKING
    # ===============================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM reservations
        WHERE slot=?
        AND status='BOOKED'
        """,
        (
            slot,
        )
    )


    booked = cursor.fetchone()[0]


    if booked > 0:

        conn.close()

        return jsonify(
            {
                "status":
                    "error",

                "message":
                    "Slot already reserved"
            }
        ), 400


    # ===============================
    # SAVE RESERVATION
    # ===============================

    cursor.execute(
        """
        INSERT INTO reservations
        (
            name,
            phone,
            slot,
            date,
            time,
            status
        )
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            name,
            phone,
            slot,
            date,
            time_value,
            "BOOKED"
        )
    )


    conn.commit()

    conn.close()


    return jsonify(
        {
            "status":
                "success",

            "message":
                "Slot Reserved Successfully"
        }
    )


# =====================================
# RESERVATION DATA
# ADMIN
# =====================================

@app.route(
    "/reservation-data"
)
def reservation_data():

    if not session.get(
        "admin"
    ):

        return jsonify(
            {
                "error":
                    "Unauthorized"
            }
        )


    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            id,
            name,
            phone,
            slot,
            date,
            time,
            status
        FROM reservations
        ORDER BY id DESC
        """
    )


    rows = cursor.fetchall()

    conn.close()


    result = []


    for row in rows:

        result.append(
            {
                "id":
                    row["id"],

                "name":
                    row["name"],

                "phone":
                    row["phone"],

                "slot":
                    row["slot"],

                "date":
                    row["date"],

                "time":
                    row["time"],

                "status":
                    row["status"]
            }
        )


    return jsonify(
        result
    )


# =====================================
# DELETE RESERVATION
# ADMIN
# =====================================

@app.route(
    "/delete-reservation",
    methods=["POST"]
)
def delete_reservation():

    if not session.get(
        "admin"
    ):

        return jsonify(
            {
                "error":
                    "Unauthorized"
            }
        )


    data = request.get_json(
        silent=True
    ) or {}


    reservation_id = data.get(
        "id"
    )


    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        DELETE FROM reservations
        WHERE id=?
        """,
        (
            reservation_id,
        )
    )


    conn.commit()

    conn.close()


    return jsonify(
        {
            "status":
                "Reservation deleted"
        }
    )


# =====================================
# ADMIN LOGIN
# =====================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    error = None


    if request.method == "POST":

        username = request.form.get(
            "username"
        )


        password = request.form.get(
            "password"
        )


        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session["admin"] = True

            return redirect(
                "/admin"
            )


        else:

            error = (
                "Invalid Username or Password"
            )


    return render_template(
        "admin_login.html",
        error=error
    )


# =====================================
# ADMIN PAGE
# =====================================

@app.route(
    "/admin"
)
def admin():

    if not session.get(
        "admin"
    ):

        return redirect(
            "/login"
        )


    return render_template(
        "admin.html"
    )


# =====================================
# ADMIN DATA
# =====================================

@app.route(
    "/admin-data"
)
def admin_data():

    if not session.get(
        "admin"
    ):

        return jsonify(
            {
                "error":
                    "Unauthorized"
            }
        )


    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT COUNT(*)
        FROM parking_history
        """
    )


    total_records = (
        cursor.fetchone()[0]
    )


    conn.close()


    return jsonify(
        {
            "inside":
                parking_data["inside"],

            "entries":
                parking_data["entries"],

            "exit":
                parking_data["exit"],

            "total_records":
                total_records,

            "camera_online":
                camera_is_online(),

            "latest_capture":
                latest_capture_url
        }
    )  


# =====================================
# STATISTICS
# =====================================

@app.route(
    "/statistics"
)
def statistics():

    if not session.get(
        "admin"
    ):

        return jsonify(
            {
                "error":
                    "Unauthorized"
            }
        )


    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    # ===============================
    # TOTAL EVENTS
    # ===============================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM parking_history
        """
    )


    today_events = (
        cursor.fetchone()[0]
    )


    # ===============================
    # TOTAL ENTRY
    # ===============================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM parking_history
        WHERE event='ENTRY'
        """
    )


    total_entry = (
        cursor.fetchone()[0]
    )


    # ===============================
    # TOTAL EXIT
    # ===============================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM parking_history
        WHERE event='EXIT'
        """
    )


    total_exit = (
        cursor.fetchone()[0]
    )


    conn.close()


    return jsonify(
        {
            "today_events":
                today_events,

            "total_entry":
                total_entry,

            "total_exit":
                total_exit
        }
    )


# =====================================
# CHART DATA
# =====================================

@app.route(
    "/chart-data"
)
def chart_data():

    if not session.get(
        "admin"
    ):

        return jsonify(
            {
                "error":
                    "Unauthorized"
            }
        )


    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            time,
            entries,
            exit
        FROM parking_history
        ORDER BY id ASC
        LIMIT 50
        """
    )


    rows = cursor.fetchall()


    conn.close()


    labels = []

    entries = []

    exits = []


    for row in rows:

        labels.append(
            row[0]
        )

        entries.append(
            row[1]
        )

        exits.append(
            row[2]
        )


    return jsonify(
        {
            "labels":
                labels,

            "entries":
                entries,

            "exits":
                exits
        }
    )


# =====================================
# CLEAR HISTORY
# =====================================

@app.route(
    "/clear-history",
    methods=["POST"]
)
def clear_history():

    if not session.get(
        "admin"
    ):

        return jsonify(
            {
                "error":
                    "Unauthorized"
            }
        )


    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        "DELETE FROM parking_history"
    )


    conn.commit()

    conn.close()


    # Reset event memory so the next
    # ENTRY / EXIT is recorded normally.

    global last_event_key

    last_event_key = None


    return jsonify(
        {
            "status":
                "History cleared"
        }
    )


# =====================================
# RESET COUNTER
# =====================================

@app.route(
    "/reset-counter",
    methods=["POST"]
)
def reset_counter():

    if not session.get(
        "admin"
    ):

        return jsonify(
            {
                "error":
                    "Unauthorized"
            }
        )


    parking_data["inside"] = 0

    parking_data["entries"] = 0

    parking_data["exit"] = 0

    parking_data["event"] = "NONE"


    global last_event_key

    last_event_key = None


    update_status_database()


    return jsonify(
        {
            "status":
                "Counter reset"
        }
    )


# =====================================
# EXPORT CSV
# =====================================

@app.route(
    "/export"
)
def export_csv():

    if not session.get(
        "admin"
    ):

        return redirect(
            "/login"
        )


    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            id,
            time,
            slot1,
            slot2,
            inside,
            entries,
            exit,
            event,
            image_path
        FROM parking_history
        ORDER BY id DESC
        """
    )


    rows = cursor.fetchall()


    conn.close()


    output = io.StringIO()

    writer = csv.writer(
        output
    )


    writer.writerow(
        [
            "ID",
            "Time",
            "Slot1",
            "Slot2",
            "Inside",
            "Entry",
            "Exit",
            "Event",
            "Image Path"
        ]
    )


    writer.writerows(
        rows
    )


    output.seek(0)


    return send_file(
        io.BytesIO(
            output.getvalue().encode()
        ),

        mimetype="text/csv",

        as_attachment=True,

        download_name=
            "parking_history.csv"
    )


# =====================================
# LOGOUT
# =====================================

@app.route(
    "/logout"
)
def logout():

    session.clear()


    return redirect(
        "/"
    )


# =====================================
# START SERVER
# =====================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",

        port=5000,

        debug=True
    )