# app.py - QUIZ PARYAJ COMPLETE - MonCash Payment
import os
import sys
import logging
import re
import secrets
import base64
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Tuple, Optional, Dict, Any, List
import random

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import firebase_admin
from firebase_admin import credentials, auth, firestore
from dotenv import load_dotenv
import requests

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("🎯 Quiz Paryaj Platform - COMPLETE VERSION")
logger.info("=" * 60)

# ==================== CONFIG ====================
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_urlsafe(32))
    DEBUG = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class PaymentConfig:
    MONCASH_CLIENT_ID = os.getenv('MONCASH_CLIENT_ID')
    MONCASH_CLIENT_SECRET = os.getenv('MONCASH_CLIENT_SECRET')
    MONCASH_BASE_URL = os.getenv('MONCASH_BASE_URL', 'https://api.moncashbutton.digicelgroup.com')
    PLATFORM_COMMISSION = 15  # 15% komisyon pou platfòm

# ==================== QUIZ DATABASE ====================
QUIZ_DATABASE = [
    {
        'id': 1,
        'category': 'Futbòl',
        'difficulty': 'Fasil',
        'question': 'Ki ekip ki genyen World Cup 2022?',
        'options': ['Brazil', 'Argentina', 'France', 'Germany'],
        'correct_answer': 'Argentina',
        'bet_amount': 25,
        'win_amount': 40,
        'explanation': 'Argentina te genyen World Cup 2022 nan Qatar, yo bat France 4-2 nan penalty.'
    },
    {
        'id': 2,
        'category': 'Futbòl',
        'difficulty': 'Fasil',
        'question': 'Ki koulè mayo Liverpool?',
        'options': ['Ble', 'Wouj', 'Vèt', 'Jòn'],
        'correct_answer': 'Wouj',
        'bet_amount': 25,
        'win_amount': 35,
        'explanation': 'Liverpool jwe ak mayo wouj. Yo rele yo "The Reds".'
    },
    {
        'id': 3,
        'category': 'Futbòl',
        'difficulty': 'Mwayen',
        'question': 'Ki jwè ki gen plis Ballon d\'Or?',
        'options': ['Cristiano Ronaldo', 'Lionel Messi', 'Neymar', 'Mbappé'],
        'correct_answer': 'Lionel Messi',
        'bet_amount': 25,
        'win_amount': 50,
        'explanation': 'Lionel Messi gen 8 Ballon d\'Or (2023), pi fò pase tout lòt jwè.'
    },
    {
        'id': 4,
        'category': 'Istwa',
        'difficulty': 'Mwayen',
        'question': 'Ki ane Brazil te genyen premye World Cup yo?',
        'options': ['1950', '1958', '1962', '1970'],
        'correct_answer': '1958',
        'bet_amount': 25,
        'win_amount': 50,
        'explanation': 'Brazil te genyen premye World Cup yo an 1958 nan Sweden, ak Pelé 17 an.'
    },
    {
        'id': 5,
        'category': 'Futbòl',
        'difficulty': 'Difisil',
        'question': 'Ki ekip ki gen plis Champions League?',
        'options': ['Barcelona', 'Real Madrid', 'AC Milan', 'Bayern Munich'],
        'correct_answer': 'Real Madrid',
        'bet_amount': 25,
        'win_amount': 60,
        'explanation': 'Real Madrid gen 14 Champions League, pi fò nan listwa.'
    },
    {
        'id': 6,
        'category': 'Estatistik',
        'difficulty': 'Difisil',
        'question': 'Ki jwè ki make plis gòl nan yon World Cup?',
        'options': ['Pelé', 'Ronaldo', 'Miroslav Klose', 'Gerd Müller'],
        'correct_answer': 'Miroslav Klose',
        'bet_amount': 25,
        'win_amount': 60,
        'explanation': 'Miroslav Klose (Germany) gen 16 gòl nan World Cup, rekò mondyal.'
    },
    {
        'id': 7,
        'category': 'Futbòl',
        'difficulty': 'Fasil',
        'question': 'Konbyen jwè ki sou teren pou yon ekip?',
        'options': ['10', '11', '12', '9'],
        'correct_answer': '11',
        'bet_amount': 25,
        'win_amount': 35,
        'explanation': 'Chak ekip gen 11 jwè sou teren, enkli gadyen an.'
    },
    {
        'id': 8,
        'category': 'Règ',
        'difficulty': 'Mwayen',
        'question': 'Apre konbyen kat jòn yon jwè resevwa kat wouj?',
        'options': ['1', '2', '3', '4'],
        'correct_answer': '2',
        'bet_amount': 25,
        'win_amount': 50,
        'explanation': 'Apre 2 kat jòn, jwè a resevwa kat wouj epi li sòti nan match.'
    },
    {
        'id': 9,
        'category': 'Istwa',
        'difficulty': 'Difisil',
        'question': 'Ki peyi ki òganize premye World Cup?',
        'options': ['France', 'Brazil', 'Uruguay', 'Italy'],
        'correct_answer': 'Uruguay',
        'bet_amount': 25,
        'win_amount': 60,
        'explanation': 'Uruguay te òganize epi genyen premye World Cup an 1930.'
    },
    {
        'id': 10,
        'category': 'Futbòl',
        'difficulty': 'Fasil',
        'question': 'Ki non estadyòm Barcelona?',
        'options': ['Santiago Bernabéu', 'Camp Nou', 'Old Trafford', 'Anfield'],
        'correct_answer': 'Camp Nou',
        'bet_amount': 25,
        'win_amount': 40,
        'explanation': 'Camp Nou se estadyòm Barcelona, pi gwo nan Ewòp.'
    }
]

# ==================== FLASK SETUP ====================
app = Flask(
    __name__,
    template_folder=os.path.join(project_root, 'templates'),
    static_folder=os.path.join(project_root, 'static')
)
app.config.from_object(Config)

CORS(app, supports_credentials=True)
limiter = Limiter(get_remote_address, app=app, default_limits=["200/hour"], storage_uri="memory://")

# ==================== FIREBASE ====================
db = None

def initialize_firebase():
    global db
    try:
        if not firebase_admin._apps:
            firebase_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
            if not firebase_json:
                logger.error("❌ FIREBASE_SERVICE_ACCOUNT_JSON missing")
                return None
            service_account_data = json.loads(firebase_json)
            cred = credentials.Certificate(service_account_data)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("✅ Firebase connected")
        return db
    except Exception as e:
        logger.error(f"❌ Firebase error: {e}")
        return None

db = initialize_firebase()

# ==================== MONCASH API ====================
class MonCashAPI:
    def __init__(self):
        self.client_id = PaymentConfig.MONCASH_CLIENT_ID
        self.client_secret = PaymentConfig.MONCASH_CLIENT_SECRET
        self.base_url = PaymentConfig.MONCASH_BASE_URL
        self.access_token = None
        self.token_expiry = datetime.now()
    
    def _authenticate(self) -> Optional[str]:
        if not self.client_id or not self.client_secret:
            logger.error("❌ MonCash credentials missing")
            return None
        
        if self.access_token and self.token_expiry > datetime.now() + timedelta(seconds=10):
            return self.access_token
        
        try:
            auth_url = f'{self.base_url}/oauth/token'
            auth_string = f"{self.client_id}:{self.client_secret}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_auth}',
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            payload = {'scope': 'read,write', 'grant_type': 'client_credentials'}
            
            response = requests.post(auth_url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get('access_token')
            expires_in = data.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("✅ MonCash authenticated")
            return self.access_token
        except Exception as e:
            logger.error(f"❌ MonCash auth error: {e}")
            return None
    
    def create_payment(self, amount: float, order_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        token = self._authenticate()
        if not token:
            return False, "MonCash pa disponib", None
        
        try:
            payment_url = f'{self.base_url}/Api/v1/CreatePayment'
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            payload = {'amount': amount, 'orderId': order_id}
            
            response = requests.post(payment_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            payment_token = data.get('payment_token')
            
            if payment_token:
                redirect_url = f'{self.base_url}/Moncash-middleware/Payment/Redirect?token={payment_token}'
                return True, "Peman kreye", redirect_url
            return False, "Erè kreye peman", None
        except Exception as e:
            logger.error(f"❌ MonCash payment error: {e}")
            return False, "Erè koneksyon", None
    
    def verify_payment(self, transaction_id: str) -> Tuple[bool, Optional[Dict]]:
        token = self._authenticate()
        if not token:
            return False, None
        
        try:
            verify_url = f'{self.base_url}/Api/v1/RetrieveTransactionPayment'
            headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
            
            response = requests.post(verify_url, headers=headers, json={'transactionId': transaction_id}, timeout=10)
            response.raise_for_status()
            return True, response.json()
        except Exception as e:
            logger.error(f"❌ Verify error: {e}")
            return False, None

moncash_api = MonCashAPI()

# ==================== HELPERS ====================
def get_user_data(uid: str) -> Dict[str, Any]:
    defaults = {
        'username': 'User',
        'email': '',
        'balance': 0,
        'total_bets': 0,
        'total_wins': 0,
        'total_losses': 0,
        'bet_history': []
    }
    
    if not db:
        return defaults.copy()
    
    try:
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return defaults.copy()
        
        user_data = user_doc.to_dict() or {}
        for key, default_value in defaults.items():
            if key not in user_data:
                user_data[key] = default_value
        return user_data
    except Exception as e:
        logger.error(f"❌ Get user error: {e}")
        return defaults.copy()

def update_user_balance(uid: str, amount: float, transaction_type: str) -> bool:
    """Update user balance"""
    if not db:
        return False
    
    try:
        user_ref = db.collection('users').document(uid)
        
        @firestore.transactional
        def update_in_transaction(transaction):
            snapshot = user_ref.get(transaction=transaction)
            user_data = snapshot.to_dict() or {}
            
            current_balance = user_data.get('balance', 0)
            new_balance = current_balance + amount
            
            if new_balance < 0:
                return False
            
            transaction.update(user_ref, {
                'balance': new_balance,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            return True
        
        return update_in_transaction(db.transaction())
    except Exception as e:
        logger.error(f"❌ Update balance error: {e}")
        return False

def record_bet(uid: str, quiz_id: int, bet_amount: float, user_answer: str, is_correct: bool, win_amount: float = 0) -> bool:
    """Record bet in database"""
    if not db:
        return False
    
    try:
        bet_record = {
            'user_id': uid,
            'quiz_id': quiz_id,
            'bet_amount': bet_amount,
            'user_answer': user_answer,
            'is_correct': is_correct,
            'win_amount': win_amount,
            'platform_commission': bet_amount * (PaymentConfig.PLATFORM_COMMISSION / 100),
            'timestamp': firestore.SERVER_TIMESTAMP,
            'date': datetime.now().isoformat()
        }
        
        db.collection('bets').add(bet_record)
        
        # Update user stats
        user_ref = db.collection('users').document(uid)
        user_ref.update({
            'total_bets': firestore.Increment(1),
            'total_wins': firestore.Increment(1 if is_correct else 0),
            'total_losses': firestore.Increment(0 if is_correct else 1)
        })
        
        return True
    except Exception as e:
        logger.error(f"❌ Record bet error: {e}")
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'uid' not in session:
            flash('Ou dwe konekte', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== VALIDATORS ====================
class DataValidator:
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        if not email or not isinstance(email, str):
            return False, "Email obligatwa"
        email = email.strip().lower()
        if not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,63}$', email):
            return False, "Email pa valid"
        return True, email
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        if not username or not isinstance(username, str):
            return False, "Non obligatwa"
        username = username.strip()
        if len(username) < 3 or len(username) > 30:
            return False, "Non 3-30 karakterè"
        return True, username

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Homepage"""
    if 'uid' in session:
        return redirect(url_for('dashboard'))
    
    stats = {
        'total_users': random.randint(5000, 15000),
        'total_bets': random.randint(20000, 50000),
        'total_questions': len(QUIZ_DATABASE)
    }
    
    return render_template('quiz_betting/index.html', stats=stats)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5/minute")
def login():
    """Login"""
    if request.method == 'POST':
        try:
            if not db:
                return render_template('quiz_betting/login.html', error="Sistèm pa disponib")
            
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            is_valid, validated_email = DataValidator.validate_email(email)
            if not is_valid:
                return render_template('quiz_betting/login.html', error=validated_email)
            
            user = auth.get_user_by_email(validated_email)
            user_doc = db.collection('users').document(user.uid).get()
            
            if not user_doc.exists:
                return render_template('quiz_betting/login.html', error="Kont pa egziste")
            
            user_dict = user_doc.to_dict() or {}
            session.permanent = True
            session['uid'] = user.uid
            session['email'] = validated_email
            session['username'] = user_dict.get('username', 'User')
            
            flash('Koneksyon reyisi!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return render_template('quiz_betting/login.html', error="Erè koneksyon")
    
    return render_template('quiz_betting/login.html')

@app.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5/minute")
def signup():
    """Signup"""
    if request.method == 'POST':
        try:
            if not db:
                return render_template('quiz_betting/signup.html', error="Sistèm pa disponib")
            
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            is_valid_user, validated_username = DataValidator.validate_username(username)
            if not is_valid_user:
                return render_template('quiz_betting/signup.html', error=validated_username)
            
            is_valid_email, validated_email = DataValidator.validate_email(email)
            if not is_valid_email:
                return render_template('quiz_betting/signup.html', error=validated_email)
            
            if len(password) < 6:
                return render_template('quiz_betting/signup.html', error="Modpas 6+ karakterè")
            
            user = auth.create_user(email=validated_email, password=password, display_name=validated_username)
            
            db.collection('users').document(user.uid).set({
                'username': validated_username,
                'email': validated_email,
                'balance': 0,
                'total_bets': 0,
                'total_wins': 0,
                'total_losses': 0,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            
            session.permanent = True
            session['uid'] = user.uid
            session['email'] = validated_email
            session['username'] = validated_username
            
            flash('Kont kreye! Ajoute lajan pou kòmanse jwe.', 'success')
            return redirect(url_for('dashboard'))
        except auth.EmailAlreadyExistsError:
            return render_template('quiz_betting/signup.html', error="Email deja itilize")
        except Exception as e:
            logger.error(f"❌ Signup error: {e}")
            return render_template('quiz_betting/signup.html', error="Erè")
    
    return render_template('quiz_betting/signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Ou sòti', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard"""
    uid = session['uid']
    user_data = get_user_data(uid)
    
    # Kategorize quiz yo
    easy_quizzes = [q for q in QUIZ_DATABASE if q['difficulty'] == 'Fasil']
    medium_quizzes = [q for q in QUIZ_DATABASE if q['difficulty'] == 'Mwayen']
    hard_quizzes = [q for q in QUIZ_DATABASE if q['difficulty'] == 'Difisil']
    
    return render_template(
        'quiz_betting/dashboard.html',
        user=user_data,
        easy_quizzes=easy_quizzes,
        medium_quizzes=medium_quizzes,
        hard_quizzes=hard_quizzes,
        total_quizzes=len(QUIZ_DATABASE)
    )

@app.route('/quiz/<int:quiz_id>')
@login_required
def quiz_detail(quiz_id):
    """Quiz detail"""
    uid = session['uid']
    user_data = get_user_data(uid)
    
    quiz = next((q for q in QUIZ_DATABASE if q['id'] == quiz_id), None)
    if not quiz:
        flash('Quiz pa jwenn', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('quiz_betting/quiz_detail.html', quiz=quiz, user=user_data)

@app.route('/quiz/<int:quiz_id>/play', methods=['POST'])
@login_required
def play_quiz(quiz_id):
    """Play quiz"""
    uid = session['uid']
    user_data = get_user_data(uid)
    
    quiz = next((q for q in QUIZ_DATABASE if q['id'] == quiz_id), None)
    if not quiz:
        return jsonify({'success': False, 'error': 'Quiz pa jwenn'})
    
    user_answer = request.form.get('answer')
    if not user_answer:
        return jsonify({'success': False, 'error': 'Chwazi yon repons'})
    
    # Check balance
    if user_data['balance'] < quiz['bet_amount']:
        return jsonify({'success': False, 'error': 'Balans ensiifisan', 'redirect': url_for('add_balance')})
    
    # Check answer
    is_correct = user_answer == quiz['correct_answer']
    
    if is_correct:
        # Win
        win_amount = quiz['win_amount']
        net_win = win_amount - quiz['bet_amount']
        update_user_balance(uid, net_win, 'win')
        record_bet(uid, quiz_id, quiz['bet_amount'], user_answer, True, win_amount)
        
        return jsonify({
            'success': True,
            'correct': True,
            'message': f'🎉 Bravo! Ou genyen {win_amount} HTG!',
            'explanation': quiz['explanation'],
            'win_amount': win_amount,
            'new_balance': user_data['balance'] + net_win
        })
    else:
        # Loss
        update_user_balance(uid, -quiz['bet_amount'], 'loss')
        record_bet(uid, quiz_id, quiz['bet_amount'], user_answer, False, 0)
        
        return jsonify({
            'success': True,
            'correct': False,
            'message': f'❌ Move repons. Repons kòrèk: {quiz["correct_answer"]}',
            'explanation': quiz['explanation'],
            'correct_answer': quiz['correct_answer'],
            'new_balance': user_data['balance'] - quiz['bet_amount']
        })

@app.route('/add-balance')
@login_required
def add_balance():
    """Add balance page"""
    uid = session['uid']
    user_data = get_user_data(uid)
    return render_template('quiz_betting/add_balance.html', user=user_data)

@app.route('/process-payment', methods=['POST'])
@login_required
def process_payment():
    """Process MonCash payment"""
    try:
        amount = float(request.form.get('amount', 0))
        
        if amount < 25 or amount > 10000:
            flash('Montan dwe ant 25 ak 10,000 HTG', 'error')
            return redirect(url_for('add_balance'))
        
        uid = session['uid']
        order_id = f"BAL-{uid}-{int(datetime.now().timestamp())}"
        
        session['pending_payment_amount'] = amount
        session['pending_order_id'] = order_id
        
        success, message, redirect_url = moncash_api.create_payment(amount, order_id)
        
        if success and redirect_url:
            return redirect(redirect_url)
        else:
            flash(message or 'Erè MonCash', 'error')
            return redirect(url_for('add_balance'))
    except Exception as e:
        logger.error(f"❌ Payment error: {e}")
        flash('Erè pwosesis peman', 'error')
        return redirect(url_for('add_balance'))

@app.route('/moncash-return')
@login_required
def moncash_return():
    """MonCash return"""
    try:
        transaction_id = request.args.get('transactionId')
        if not transaction_id:
            flash('Transaction ID manke', 'error')
            return redirect(url_for('dashboard'))
        
        success, payment_data = moncash_api.verify_payment(transaction_id)
        
        if success:
            amount = session.pop('pending_payment_amount', 0)
            uid = session['uid']
            
            if update_user_balance(uid, amount, 'deposit'):
                flash(f'✅ {amount} HTG ajoute nan kont ou!', 'success')
                logger.info(f"✅ Balance added: {uid}, {amount} HTG")
            else:
                flash('Erè ajoute balans', 'error')
        else:
            flash('Erè verifye peman', 'error')
        
        return redirect(url_for('dashboard'))
    except Exception as e:
        logger.error(f"❌ Return error: {e}")
        flash('Erè', 'error')
        return redirect(url_for('dashboard'))

@app.route('/history')
@login_required
def bet_history():
    """Bet history"""
    uid = session['uid']
    
    try:
        bets_ref = db.collection('bets').where('user_id', '==', uid).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50)
        bets = []
        
        for bet_doc in bets_ref.stream():
            bet_data = bet_doc.to_dict()
            quiz = next((q for q in QUIZ_DATABASE if q['id'] == bet_data.get('quiz_id')), None)
            if quiz:
                bet_data['quiz_question'] = quiz['question']
            bets.append(bet_data)
        
        user_data = get_user_data(uid)
        return render_template('quiz_betting/history.html', bets=bets, user=user_data)
    except Exception as e:
        logger.error(f"❌ History error: {e}")
        return render_template('quiz_betting/history.html', bets=[], user=get_user_data(uid))

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'firebase': 'connected' if db else 'disconnected',
        'moncash': 'configured' if PaymentConfig.MONCASH_CLIENT_ID else 'not configured',
        'total_quizzes': len(QUIZ_DATABASE),
        'timestamp': datetime.now().isoformat()
    }), 200

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(error):
    return render_template('quiz_betting/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.exception("500 Error")
    return render_template('quiz_betting/500.html'), 500

# ==================== MAIN ====================
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("✅ Quiz Paryaj READY!")
    logger.info(f"📚 Total Quiz: {len(QUIZ_DATABASE)}")
    logger.info(f"💰 MonCash: {'✅' if PaymentConfig.MONCASH_CLIENT_ID else '❌'}")
    logger.info(f"📊 Commission: {PaymentConfig.PLATFORM_COMMISSION}%")
    logger.info("=" * 60)
    
    app.run(
        host=os.getenv('FLASK_RUN_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_RUN_PORT', 5000)),
        threaded=True
    )