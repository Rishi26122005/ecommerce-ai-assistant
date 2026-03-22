"""
E-Commerce Product Recommendation & Search Engine
Full-Stack Flask Application
"""

import os
import json
import hashlib
import secrets
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, session, render_template, redirect, url_for, send_from_directory, Response, stream_with_context

from database import db, User, ChatHistory, init_db
from recommender import ProductRecommender

# ─── App Config ───────────────────────────────────────────────────────────────
app = Flask(__name__)
# app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ecommerce.db"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("SECRET_KEY", "ecommerce-ai-fixed-secret-key-2024")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ecommerce.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False

db.init_app(app)

# ─── Initialize Recommender ───────────────────────────────────────────────────
DATASET_PATH = os.environ.get("DATASET_PATH", "amazon.csv")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBMtgVWV2zjchz2WcIidDVFxbPl-VRmdG8")

recommender = ProductRecommender(DATASET_PATH, GEMINI_API_KEY)

# ─── Auth Decorator ───────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized. Please login."}), 401
        return f(*args, **kwargs)
    return decorated

# ─── Helper ───────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ─── Routes: Pages ────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat-history")
@app.route("/history-view")
def chat_history_view():
    return render_template("chat_history.html")

# ─── API: Auth ────────────────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409

    user = User(name=name, email=email, password_hash=hash_password(password))
    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id
    session["user_name"] = user.name
    return jsonify({"message": "Registered successfully!", "user": {"id": user.id, "name": user.name, "email": user.email}}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data  = request.get_json()
    email = data.get("email", "").strip().lower()
    pwd   = data.get("password", "")

    user = User.query.filter_by(email=email, password_hash=hash_password(pwd)).first()
    if not user:
        return jsonify({"error": "Invalid email or password."}), 401

    session["user_id"]   = user.id
    session["user_name"] = user.name
    return jsonify({"message": "Login successful!", "user": {"id": user.id, "name": user.name, "email": user.email}})


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out."})


@app.route("/api/auth/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"authenticated": False}), 200
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return jsonify({"authenticated": False}), 200
    return jsonify({"authenticated": True, "user": {"id": user.id, "name": user.name, "email": user.email}})


# ─── API: Products ────────────────────────────────────────────────────────────
@app.route("/api/products", methods=["GET"])
def get_products():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    category = request.args.get("category", "")
    min_price = request.args.get("min_price", None)
    max_price = request.args.get("max_price", None)
    min_rating = request.args.get("min_rating", None)
    sort_by  = request.args.get("sort_by", "rating")   # rating | price_asc | price_desc | discount

    products, total, categories = recommender.get_products(
        page=page,
        per_page=per_page,
        category=category,
        min_price=float(min_price) if min_price else None,
        max_price=float(max_price) if max_price else None,
        min_rating=float(min_rating) if min_rating else None,
        sort_by=sort_by,
    )
    return jsonify({
        "products": products,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "categories": categories,
    })


@app.route("/api/products/search", methods=["GET"])
def search_products():
    query = request.args.get("q", "").strip()
    top_k = int(request.args.get("top_k", 10))
    if not query:
        return jsonify({"error": "Query is required."}), 400
    results = recommender.search(query, top_k=top_k)
    return jsonify({"query": query, "results": results, "count": len(results)})


# ─── API: Recommendations (AI Chat) ───────────────────────────────────────────
@app.route("/api/recommend", methods=["POST"])
@login_required
def recommend():
    data  = request.get_json()
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query is required."}), 400

    ai_response, retrieved_products = recommender.recommend(query)

    # Save to chat history
    history = ChatHistory(
        user_id=session["user_id"],
        query=query,
        ai_response=ai_response,
        products_json=json.dumps(retrieved_products),
    )
    db.session.add(history)
    db.session.commit()

    return jsonify({
        "query": query,
        "ai_response": ai_response,
        "products": retrieved_products,
        "timestamp": history.created_at.isoformat(),
    })


# ─── API: Streaming Recommendations (SSE) ────────────────────────────────────
@app.route("/api/recommend/stream", methods=["POST"])
@login_required
def recommend_stream():
    data  = request.get_json()
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query is required."}), 400

    # Retrieve products first (fast)
    retrieved_products = recommender.get_retrieved(query, top_k=5)
    products_json_str  = json.dumps(retrieved_products)

    def generate():
        # First event: send products immediately
        yield f"event: products\ndata: {products_json_str}\n\n"

        # Stream the LLM response token by token
        full_response = ""
        try:
            for chunk in recommender.stream_recommend(query, retrieved_products):
                full_response += chunk
                payload = json.dumps({"chunk": chunk})
                yield f"event: chunk\ndata: {payload}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            return

        # Save full response to DB
        history = ChatHistory(
            user_id=session["user_id"],
            query=query,
            ai_response=full_response,
            products_json=products_json_str,
        )
        db.session.add(history)
        db.session.commit()

        # Final event: done
        yield f"event: done\ndata: {json.dumps({'timestamp': history.created_at.isoformat()})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─── API: Chat History ────────────────────────────────────────────────────────
@app.route("/api/history", methods=["GET"])
@login_required
def get_history():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    pagination = (
        ChatHistory.query
        .filter_by(user_id=session["user_id"])
        .order_by(ChatHistory.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    history = []
    for item in pagination.items:
        history.append({
            "id": item.id,
            "query": item.query,
            "ai_response": item.ai_response,
            "products": json.loads(item.products_json) if item.products_json else [],
            "timestamp": item.created_at.isoformat(),
        })

    return jsonify({
        "history": history,
        "total": pagination.total,
        "page": page,
        "total_pages": pagination.pages,
    })


@app.route("/api/history/<int:history_id>", methods=["DELETE"])
@login_required
def delete_history(history_id):
    item = ChatHistory.query.filter_by(id=history_id, user_id=session["user_id"]).first()
    if not item:
        return jsonify({"error": "Not found."}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Deleted."})


@app.route("/api/history/clear", methods=["DELETE"])
@login_required
def clear_history():
    ChatHistory.query.filter_by(user_id=session["user_id"]).delete()
    db.session.commit()
    return jsonify({"message": "History cleared."})


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        init_db(app)
    app.run(debug=True, host="0.0.0.0", port=5000)