from functools import wraps

from flask import Blueprint, g, jsonify, request

from . import data

api = Blueprint("api", __name__)


@api.get("/health")
def health_check():
    return jsonify({"status": "ok"})


def not_implemented(feature):
    return jsonify({"error": f"{feature} data access is not implemented yet"}), 501


def authenticated_route(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return jsonify({"error": "A bearer token is required"}), 401

        g.current_user = data.get_user_from_session(token)
        if g.current_user is None:
            return jsonify({"error": "Invalid or expired token"}), 401
        return view(*args, **kwargs)

    return wrapped


@api.post("/auth/register")
def register():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")
    password = payload.get("password", "")
    if not isinstance(email, str) or "@" not in email:
        return jsonify({"error": "A valid email is required"}), 400
    if not isinstance(password, str) or len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    try:
        user = data.register_user(email, password)
    except ValueError as error:
        return jsonify({"error": str(error)}), 409
    return jsonify({"user": user}), 201


@api.post("/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")
    password = payload.get("password", "")
    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "email and password are required"}), 400

    session = data.login_user(email, password)
    if session is None:
        return jsonify({"error": "Invalid email or password"}), 401
    return jsonify(session)


@api.post("/auth/logout")
@authenticated_route
def logout():
    authorization = request.headers["Authorization"]
    token = authorization.split(" ", 1)[1]
    data.logout_user(token)
    return jsonify({"message": "Logged out"})


@api.get("/auth/me")
@authenticated_route
def current_user():
    return jsonify({"user": g.current_user})

@api.get("/users")
@authenticated_route
def get_users():
    return data.list_users()


@api.get("/scheduled-bills")
@authenticated_route
def get_scheduled_bills():
   user_id = g.current_user["id"]
   return data.list_scheduled_bills(user_id)


@api.post("/scheduled-bills")
@authenticated_route
def create_scheduled_bill():
    user_id = g.current_user["id"]
    payload = request.get_json(silent=True) or {}
    description = payload.get("description", "")
    amount = payload.get("amount", "")
    frequency = payload.get("frequency", "")
    due_date = payload.get("due_date", "")
    return data.create_scheduled_bill(user_id, description, amount, frequency, due_date)


@api.delete("/scheduled-bills/<int:scheduled_bill_id>")
@authenticated_route
def delete_scheduled_bill(scheduled_bill_id):
    user_id = g.current_user["id"]
    return data.delete_scheduled_bill(user_id, scheduled_bill_id)

@api.get("/bills")
@authenticated_route
def get_bills():
    return data.list_bills()

@api.delete("/bills/<int:bill_id>")
@authenticated_route
def delete_bill(bill_id):
    user_id = g.current_user["id"]
    return data.delete_bill(user_id, bill_id)


@api.post("/bills")
@authenticated_route
def create_bill():
    user_id = g.current_user["id"]
    payload = request.get_json(silent=True) or {}
    description = payload.get("description", "")
    amount = payload.get("amount", "")
    paid_by = payload.get("paid_by", "")
    due_date = payload.get("due_date", "")
    split_between = payload.get("split_between", "")
    return data.create_bill(user_id, description, amount, paid_by, split_between, due_date)


@api.get("/expenses/overview")
@authenticated_route
def expense_overview():
    return not_implemented("Expense overview")
