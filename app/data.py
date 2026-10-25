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
    return {"id": user["id"], "email": user["email"], "user_name": user["user_name"]}

def _bill_response(bill):
    return {"id": bill["id"], "description": bill["description"], "amount": bill["amount"], "paid_by": bill["paid_by"], "due_date": bill["due_date"], "split_between": bill["split_between"]}

def _scheduled_bill_response(scheduled_bills):
    return {"id": scheduled_bills["id"], "description": scheduled_bills["description"], "amount": scheduled_bills["amount"], "due_date": scheduled_bills["due_date"], "frequency": scheduled_bills["frequency"]}


def register_user(username,email, password):
    normalized_email = email.strip().lower()
    salt = secrets.token_bytes(16)
    password_hash = _hash_password(password, salt)
    database = get_db()

    try:
        cursor = database.execute(
            """
            INSERT INTO users (user_name,email, password_hash, password_salt)
            VALUES (?,?, ?, ?)
            """,
            (username,normalized_email, password_hash, salt.hex()),
        )
    except sqlite3.IntegrityError as error:
        print(f"IntegrityError: {error}")
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

def delete_user(id):
    database = get_db()
    cursor = database.execute(
    """
    DELETE FROM users
    WHERE users.id = ?
    """,
    (id,),
    )
    database.commit()
    return {}


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


def list_bills():
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


def _as_int(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_split_between(raw_value):
    if raw_value in (None, ""):
        return []
    participants = []
    for part in str(raw_value).split(","):
        user_id = _as_int(part.strip())
        if user_id is not None and user_id not in participants:
            participants.append(user_id)
    return participants


def _round_money(value):
    return round(float(value), 2)


def get_expense_overview(user_id, start_date=None, end_date=None):
    database = get_db()
    query = "SELECT bills.* FROM bills WHERE 1 = 1"
    params = []

    if start_date:
        query += " AND due_date IS NOT NULL AND due_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND due_date IS NOT NULL AND due_date <= ?"
        params.append(end_date)

    query += " ORDER BY due_date ASC, id ASC"
    cursor = database.execute(query, params)

    user_names = {
        row["id"]: row["user_name"]
        for row in database.execute("SELECT id, user_name FROM users").fetchall()
    }

    my_expenses = {"total": 0.0, "bills": [], "by_category": {}}
    my_debts = {"total": 0.0, "by_person": {}, "chart": []}
    debts_to_me = {"total": 0.0, "by_person": {}, "chart": []}

    for bill in cursor.fetchall():
        bill_amount = _round_money(bill["amount"])
        payer_id = _as_int(bill["paid_by"])
        participants = _parse_split_between(bill["split_between"])
        if not participants or payer_id is None:
            continue

        if payer_id == user_id:
            my_expenses["total"] = _round_money(my_expenses["total"] + bill_amount)
            my_expenses["bills"].append({
                "id": bill["id"],
                "description": bill["description"],
                "amount": bill_amount,
                "paid_by": payer_id,
                "due_date": bill["due_date"],
                "split_between": participants,
            })
            category_key = bill["description"].strip() or "Other"
            my_expenses["by_category"][category_key] = my_expenses["by_category"].get(category_key, 0.0) + bill_amount

        if user_id in participants:
            share = _round_money(bill_amount / len(participants))
            if payer_id != user_id:
                current_debt = my_debts["by_person"].get(payer_id, 0.0)
                my_debts["by_person"][payer_id] = _round_money(current_debt + share)
                my_debts["total"] = _round_money(my_debts["total"] + share)

        if payer_id == user_id:
            for participant_id in participants:
                if participant_id == user_id:
                    continue
                current_credit = debts_to_me["by_person"].get(participant_id, 0.0)
                share = _round_money(bill_amount / len(participants))
                debts_to_me["by_person"][participant_id] = _round_money(current_credit + share)
                debts_to_me["total"] = _round_money(debts_to_me["total"] + share)

    def _to_chart_entries(breakdown):
        entries = []
        for user_id_key, amount in sorted(breakdown.items(), key=lambda item: (-item[1], item[0])):
            entries.append({
                "user_id": user_id_key,
                "user_name": user_names.get(user_id_key, "Unknown user"),
                "amount": _round_money(amount),
            })
        return entries

    my_debts["chart"] = _to_chart_entries(my_debts["by_person"])
    debts_to_me["chart"] = _to_chart_entries(debts_to_me["by_person"])

    overall = {
        "total_i_owe": _round_money(my_debts["total"]),
        "total_owed_to_me": _round_money(debts_to_me["total"]),
        "net_balance": _round_money(debts_to_me["total"] - my_debts["total"]),
        "chart": [
            {"label": "I owe", "value": _round_money(my_debts["total"])},
            {"label": "Owed to me", "value": _round_money(debts_to_me["total"])},
            {"label": "Net", "value": _round_money(debts_to_me["total"] - my_debts["total"])},
        ],
    }

    summary = {
        "total_paid_by_me": _round_money(my_expenses["total"]),
        "total_i_owe": overall["total_i_owe"],
        "total_owed_to_me": overall["total_owed_to_me"],
        "net_balance": overall["net_balance"],
    }

    return {
        "summary": summary,
        "my_expenses": {
            "total": _round_money(my_expenses["total"]),
            "bills": my_expenses["bills"],
            "by_category": {key: _round_money(value) for key, value in sorted(my_expenses["by_category"].items())},
            "chart": [
                {"label": key, "value": _round_money(value)}
                for key, value in sorted(my_expenses["by_category"].items(), key=lambda item: (-item[1], item[0]))
            ],
        },
        "my_debts": {
            "total": _round_money(my_debts["total"]),
            "by_person": {
                str(user_id): _round_money(amount)
                for user_id, amount in sorted(my_debts["by_person"].items(), key=lambda item: (-item[1], item[0]))
            },
            "chart": my_debts["chart"],
        },
        "debts_to_me": {
            "total": _round_money(debts_to_me["total"]),
            "by_person": {
                str(user_id): _round_money(amount)
                for user_id, amount in sorted(debts_to_me["by_person"].items(), key=lambda item: (-item[1], item[0]))
            },
            "chart": debts_to_me["chart"],
        },
        "overall": overall,
    }
