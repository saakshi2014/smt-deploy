from flask import Flask, render_template, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from firebase_config import initialize_firebase, get_firestore_client
import os

load_dotenv()

app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)

app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION'] = False

with app.app_context():
    initialize_firebase()

from routes.auth import auth_bp
app.register_blueprint(auth_bp)
from routes.stages import stages_bp
app.register_blueprint(stages_bp)
from routes.leads import leads_bp
app.register_blueprint(leads_bp)
from routes.tasks import tasks_bp
app.register_blueprint(tasks_bp)

from routes.notifications import notifications_bp
app.register_blueprint(notifications_bp)

from routes.custom_stages import custom_stages_bp
app.register_blueprint(custom_stages_bp)

from routes.kpi import kpi_bp
app.register_blueprint(kpi_bp)
from routes.coaching import coaching_bp
app.register_blueprint(coaching_bp)

from routes.reviews import reviews_bp
app.register_blueprint(reviews_bp)
from routes.export import export_bp
app.register_blueprint(export_bp)
def is_logged_in():
    return 'uid' in session and 'role' in session


def redirect_by_role(role):
    if role == 'employee':
        return redirect(url_for('employee_dashboard'))
    elif role == 'm1_manager':
        return redirect(url_for('m1_dashboard'))
    elif role == 'm2_manager':
        return redirect(url_for('m2_dashboard'))
    else:
        return redirect(url_for('login'))


@app.route('/')
def index():
    if is_logged_in():
        return redirect_by_role(session['role'])
    return render_template('login.html')


@app.route('/login')
def login():
    if is_logged_in():
        return redirect_by_role(session['role'])
    return render_template('login.html')


@app.route('/dashboard/employee')
def employee_dashboard():
    if not is_logged_in():
        return redirect(url_for('login'))
    if session['role'] != 'employee':
        return redirect_by_role(session['role'])
    return render_template('employee_dashboard.html',
                           user_name=session.get('email', ''),
                           role=session.get('role', ''))


@app.route('/dashboard/m1')
def m1_dashboard():
    if not is_logged_in():
        return redirect(url_for('login'))
    if session['role'] != 'm1_manager':
        return redirect_by_role(session['role'])
    return render_template('m1_dashboard.html',
                           user_name=session.get('email', ''),
                           role=session.get('role', ''))


@app.route('/dashboard/m2')
def m2_dashboard():
    if not is_logged_in():
        return redirect(url_for('login'))
    if session['role'] != 'm2_manager':
        return redirect_by_role(session['role'])
    return render_template('m2_dashboard.html',
                           user_name=session.get('email', ''),
                           role=session.get('role', ''))


@app.route('/logout')
def logout_page():
    session.clear()
    response = redirect(url_for('login'))
    response.delete_cookie('session')
    return response


@app.route('/test-firebase')
def test_firebase():
    try:
        db          = get_firestore_client()
        collections = [col.id for col in db.collections()]
        return jsonify({
            "status":      "success",
            "message":     "Firebase connected",
            "collections": collections
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    import os
    debug_mode = os.environ.get('FLASK_ENV', 'development') != 'production'
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=debug_mode
    )