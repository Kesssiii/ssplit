import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from .database import get_db


SESSION_DAYS = 7
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def _hash_password(password, salt):
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
    ).hex()


def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _user_response(user):
    return {"id": user["id"], "email": user["email"]}

def _bill_response(bill):
    return {"id": bill["id"], "description": bill["description"], "amount": bill["amount"], "paid_by": bill["paid_by"], "due_date": bill["due_date"]}

def _scheduled_bill_response(scheduled_bills):
    return{"id:": scheduled_bills["id"], "description": scheduled_bills["description"], "amount": scheduled_bills["amount"], "due_date": scheduled_bills["due_date"], "frequency": scheduled_bills["frequency"]}


def register_user(email, password):
    normalized_email = email.strip().lower()
    salt = secrets.token_bytes(16)
    password_hash = _hash_password(password, salt)
    database = get_db()

    try:
        cursor = database.execute(
            """
            INSERT INTO users (email, password_hash, password_salt)
            VALUES (?, ?, ?)
            """,
            (normalized_email, password_hash, salt.hex()),
        )
    except sqlite3.IntegrityError as error:
        raise ValueError("An account with that email already exists") from error

    database.commit()
    return {"id": cursor.lastrowid, "email": normalized_email}


def login_user(email, password):
    user = get_db().execute(
        "SELECT * FROM users WHERE email = ?",
        (email.strip().lower(),),
    ).fetchone()
    if user is None:
        return None

    password_hash = _hash_password(password, bytes.fromhex(user["password_salt"]))
    if not hmac.compare_digest(password_hash, user["password_hash"]):
        return None

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    database = get_db()
    database.execute(
        "INSERT INTO sessions (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user["id"], _hash_token(token), expires_at.isoformat()),
    )
    database.commit()
    return {"token": token, "expires_at": expires_at.isoformat(), "user": _user_response(user)}


def logout_user(session_token):
    database = get_db()
    database.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(session_token),))
    database.commit()


def get_user_from_session(session_token):
    session = get_db().execute(
        """
        SELECT users.*
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token_hash = ? AND sessions.expires_at > ?
        """,
        (_hash_token(session_token), datetime.now(timezone.utc).isoformat()),
    ).fetchone()
    return _user_response(session) if session is not None else None

def list_users():
    database = get_db()
    cursor = database.execute(
            """
            SELECT users.*
            FROM users
            """,
        )
    users = []
    for user in cursor.fetchall():
        users.append(_user_response(user))
    return users


def list_scheduled_bills(user_id):
    database = get_db()
    cursor = database.execute(
            """
            SELECT scheduled_bills.*
            FROM scheduled_bills
            WHERE scheduled_bills.user_id = ?
            """,
            (user_id,),
        )
    bills = []
    for bill in cursor.fetchall():
        bills.append(_scheduled_bill_response(bill))
    return bills

def delete_scheduled_bill(user_id, bill_id):
    database = get_db()
    cursor = database.execute(
        """
        DELETE FROM scheduled_bills
        WHERE scheduled_bills.user_id = ? AND scheduled_bills.id = ?
        """,
        (user_id, bill_id),
    )

    database.commit()
    return {}


def create_scheduled_bill(user_id, description, amount, due_date, frequency):
    database = get_db()

    cursor = database.execute(
            """
            INSERT INTO scheduled_bills (user_id, description, amount, due_date, frequency)
            VALUES(?,?,?,?,?)
            """,
            (user_id, description, amount, due_date, frequency),
        )
    database.commit()
    return {"id": cursor.lastrowid}

def delete_bill(user_id, bill_id):
    database = get_db()

    cursor = database.execute(
            """
            DELETE FROM bills
            WHERE bills.user_id = ? AND bills.id = ?
            """,
            (user_id, bill_id),
        )
    database.commit()
    return {}


def list_bills(user_id):
    database = get_db()

    cursor = database.execute(
            """
            SELECT bills.*
            FROM bills
            """,
        )
    bills = []
    for b in cursor.fetchall():
        bills.append(_bill_response(b))
    return bills


def create_bill(user_id, description, amount, paid_by, split_between, due_date=None):
    database = get_db()

    cursor = database.execute(
            """
            INSERT INTO bills (user_id, description, amount, paid_by, due_date, split_between)
            VALUES(?,?,?,?,?,?)
            """,
            (user_id, description, amount, paid_by, due_date, split_between),
        )
    database.commit()
    return {"id": cursor.lastrowid}


def get_expense_overview(user_id, start_date=None, end_date=None):
    raise NotImplementedError
