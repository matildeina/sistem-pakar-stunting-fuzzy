from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    render_template,
    redirect,
    url_for
)

from models.user import User
from models.activity_log import FailedLogin

from extensions import db, bcrypt, limiter
from utils.logger import log_security_event

from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)


# ==========================
# REGISTER
# ==========================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Jika sudah login jangan bisa akses register lagi
    if 'user_id' in session:
        return redirect(url_for("api.index"))

    if request.method == "POST":
        # Ambil data JSON dengan aman, jika gagal set menjadi dict kosong {}
        try:
            data = request.get_json()
            if data is None:
                data = request.form
        except Exception:
            data = request.form

        # Pastikan data tidak None sebelum memakai .get()
        if not data:
            return jsonify({"error": "Format data tidak valid atau kosong"}), 400

        username = data.get("username", "").strip() if data.get("username") else ""
        password = data.get("password", "")

        # 1. Validasi Input Kosong
        if not username or not password:
            return jsonify({
                "error": "Username dan password wajib diisi"
            }), 400

        # 2. Validasi Panjang Username
        if len(username) < 4:
            return jsonify({
                "error": "Username minimal 4 karakter"
            }), 400

        # 3. Validasi Panjang Password
        if len(password) < 6:
            return jsonify({
                "error": "Password minimal 6 karakter"
            }), 400

        # 4. Cek User yang Sudah Ada
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({
                "error": "Username sudah terdaftar"
            }), 400

        # 5. Hashing Password
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # 6. Simpan ke Database
        try:
            new_user = User(
                username=username,
                password_hash=hashed_password,
                role="User"
            )
            db.session.add(new_user)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Gagal menyimpan data ke database"}), 500

        # 7. Logging Security Event
        try:
            log_security_event(
                f"User baru terdaftar: {username}",
                "INFO",
                new_user.id
            )
        except Exception:
            # Jika logger error, registrasi tetap berhasil tapi log dilewati
            pass

        return jsonify({
            "message": "Registrasi berhasil, silakan login"
        }), 201

    return render_template("register.html")


# ==========================
# LOGIN
# ==========================
@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():

    # Jika sudah login langsung ke landing page
    if request.method == "GET" and 'user_id' in session:
        return redirect(url_for("api.index"))

    if request.method == "POST":

        data = request.get_json() or request.form

        username = data.get("username", "").strip()
        password = data.get("password", "")

        # ==========================
        # ANTI BRUTE FORCE
        # ==========================
        lima_menit_lalu = datetime.utcnow() - timedelta(minutes=5)

        failed_count = FailedLogin.query.filter(
            FailedLogin.ip_address == request.remote_addr,
            FailedLogin.created_at >= lima_menit_lalu
        ).count()

        if failed_count >= 5:

            log_security_event(
                f"IP {request.remote_addr} diblokir sementara karena brute-force login ({username})",
                "WARNING"
            )

            return jsonify({
                "error": "Terlalu banyak percobaan gagal. Silakan coba lagi dalam 5 menit."
            }), 429

        # ==========================
        # CEK USER
        # ==========================
        user = User.query.filter_by(
            username=username
        ).first()

        if user and bcrypt.check_password_hash(
            user.password_hash,
            password
        ):

            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role

            log_security_event(
                f"Login berhasil ({user.username})",
                "INFO",
                user.id
            )

            return jsonify({
                "message": "Login sukses",
                "role": user.role,

                # LANDING PAGE
                "redirect": url_for("api.index")
            })

        # ==========================
        # CATAT GAGAL LOGIN
        # ==========================
        fail_record = FailedLogin(
            username_attempted=username,
            ip_address=request.remote_addr or "127.0.0.1"
        )

        db.session.add(fail_record)
        db.session.commit()

        log_security_event(
            f"Gagal login username: {username}",
            "WARNING"
        )

        return jsonify({
            "error": "Username atau password salah"
        }), 401

    return render_template("login.html")


# ==========================
# LOGOUT
# ==========================
@auth_bp.route("/logout")
def logout():

    username = session.get("username", "Unknown")

    log_security_event(
        f"Logout user: {username}",
        "INFO"
    )

    session.clear()

    return redirect(url_for("auth.login"))