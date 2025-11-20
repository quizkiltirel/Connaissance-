# admin_routes.py - ADMIN DASHBOARD ROUTES
"""
Add this to app.py or create separate admin_routes.py
"""

# ==================== ADMIN DECORATORS ====================
ADMIN_EMAILS = ['admin@quizparyaj.ht', 'owner@quizparyaj.ht']  # Add your admin emails

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'uid' not in session:
            flash('Ou dwe konekte', 'error')
            return redirect(url_for('login'))
        
        email = session.get('email', '')
        if email not in ADMIN_EMAILS:
            flash('Aksè refize - Admin sèlman', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== ADMIN ROUTES ====================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard with full analytics"""
    try:
        # Get all stats
        stats = get_admin_stats()
        
        # Get recent activity
        recent_bets = get_recent_bets(limit=20)
        recent_users = get_recent_users(limit=10)
        top_players = get_top_players(limit=10)
        
        # Revenue breakdown
        revenue_data = calculate_revenue_breakdown()
        
        return render_template(
            'admin/dashboard.html',
            stats=stats,
            recent_bets=recent_bets,
            recent_users=recent_users,
            top_players=top_players,
            revenue=revenue_data
        )
    except Exception as e:
        logger.error(f"❌ Admin dashboard error: {e}")
        return render_template('admin/dashboard.html', stats={}, error=str(e))

@app.route('/admin/users')
@admin_required
def admin_users():
    """Manage all users"""
    try:
        users_ref = db.collection('users').order_by('created_at', direction=firestore.Query.DESCENDING)
        users = []
        
        for user_doc in users_ref.stream():
            user_data = user_doc.to_dict()
            user_data['uid'] = user_doc.id
            users.append(user_data)
        
        return render_template('admin/users.html', users=users)
    except Exception as e:
        logger.error(f"❌ Admin users error: {e}")
        return render_template('admin/users.html', users=[], error=str(e))

@app.route('/admin/bets')
@admin_required
def admin_bets():
    """View all bets"""
    try:
        bets_ref = db.collection('bets').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(100)
        bets = []
        
        for bet_doc in bets_ref.stream():
            bet_data = bet_doc.to_dict()
            
            # Get quiz info
            quiz = next((q for q in QUIZ_DATABASE if q['id'] == bet_data.get('quiz_id')), None)
            if quiz:
                bet_data['quiz_question'] = quiz['question']
            
            # Get user info
            try:
                user_doc = db.collection('users').document(bet_data.get('user_id')).get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    bet_data['username'] = user_data.get('username', 'Unknown')
            except:
                bet_data['username'] = 'Unknown'
            
            bets.append(bet_data)
        
        return render_template('admin/bets.html', bets=bets)
    except Exception as e:
        logger.error(f"❌ Admin bets error: {e}")
        return render_template('admin/bets.html', bets=[], error=str(e))

@app.route('/admin/quiz/add', methods=['GET', 'POST'])
@admin_required
def admin_add_quiz():
    """Add new quiz"""
    if request.method == 'POST':
        try:
            new_quiz = {
                'id': len(QUIZ_DATABASE) + 1,
                'category': request.form.get('category'),
                'difficulty': request.form.get('difficulty'),
                'question': request.form.get('question'),
                'options': [
                    request.form.get('option1'),
                    request.form.get('option2'),
                    request.form.get('option3'),
                    request.form.get('option4')
                ],
                'correct_answer': request.form.get('correct_answer'),
                'bet_amount': int(request.form.get('bet_amount', 25)),
                'win_amount': int(request.form.get('win_amount', 40)),
                'explanation': request.form.get('explanation')
            }
            
            # Save to database (or append to QUIZ_DATABASE)
            QUIZ_DATABASE.append(new_quiz)
            
            flash('Quiz ajoute avèk siksè!', 'success')
            return redirect(url_for('admin_quiz_list'))
        except Exception as e:
            logger.error(f"❌ Add quiz error: {e}")
            flash('Erè ajoute quiz', 'error')
    
    return render_template('admin/add_quiz.html')

@app.route('/admin/quiz')
@admin_required
def admin_quiz_list():
    """List all quizzes"""
    return render_template('admin/quiz_list.html', quizzes=QUIZ_DATABASE)

@app.route('/admin/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_quiz(quiz_id):
    """Edit quiz"""
    quiz = next((q for q in QUIZ_DATABASE if q['id'] == quiz_id), None)
    if not quiz:
        flash('Quiz pa jwenn', 'error')
        return redirect(url_for('admin_quiz_list'))
    
    if request.method == 'POST':
        try:
            quiz['category'] = request.form.get('category')
            quiz['difficulty'] = request.form.get('difficulty')
            quiz['question'] = request.form.get('question')
            quiz['options'] = [
                request.form.get('option1'),
                request.form.get('option2'),
                request.form.get('option3'),
                request.form.get('option4')
            ]
            quiz['correct_answer'] = request.form.get('correct_answer')
            quiz['bet_amount'] = int(request.form.get('bet_amount', 25))
            quiz['win_amount'] = int(request.form.get('win_amount', 40))
            quiz['explanation'] = request.form.get('explanation')
            
            flash('Quiz modifye avèk siksè!', 'success')
            return redirect(url_for('admin_quiz_list'))
        except Exception as e:
            logger.error(f"❌ Edit quiz error: {e}")
            flash('Erè modifye quiz', 'error')
    
    return render_template('admin/edit_quiz.html', quiz=quiz)

@app.route('/admin/quiz/<int:quiz_id>/delete', methods=['POST'])
@admin_required
def admin_delete_quiz(quiz_id):
    """Delete quiz"""
    try:
        global QUIZ_DATABASE
        QUIZ_DATABASE = [q for q in QUIZ_DATABASE if q['id'] != quiz_id]
        flash('Quiz efase', 'success')
    except Exception as e:
        logger.error(f"❌ Delete quiz error: {e}")
        flash('Erè efase quiz', 'error')
    
    return redirect(url_for('admin_quiz_list'))

@app.route('/admin/user/<uid>/balance', methods=['POST'])
@admin_required
def admin_adjust_balance(uid):
    """Adjust user balance"""
    try:
        amount = float(request.form.get('amount', 0))
        reason = request.form.get('reason', 'Admin adjustment')
        
        if update_user_balance(uid, amount, 'admin_adjustment'):
            flash(f'Balans ajiste: {amount} HTG', 'success')
        else:
            flash('Erè ajiste balans', 'error')
    except Exception as e:
        logger.error(f"❌ Adjust balance error: {e}")
        flash('Erè', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    """Platform settings"""
    if request.method == 'POST':
        try:
            # Update commission
            new_commission = int(request.form.get('commission', 15))
            if 0 <= new_commission <= 50:
                PaymentConfig.PLATFORM_COMMISSION = new_commission
                flash(f'Komisyon chanje: {new_commission}%', 'success')
            else:
                flash('Komisyon dwe ant 0-50%', 'error')
        except Exception as e:
            logger.error(f"❌ Settings error: {e}")
            flash('Erè', 'error')
    
    return render_template('admin/settings.html', 
                          commission=PaymentConfig.PLATFORM_COMMISSION)

# ==================== ADMIN HELPER FUNCTIONS ====================

def get_admin_stats():
    """Get comprehensive platform statistics"""
    try:
        # Count users
        users_ref = db.collection('users')
        total_users = len(list(users_ref.stream()))
        
        # Count bets
        bets_ref = db.collection('bets')
        all_bets = list(bets_ref.stream())
        total_bets = len(all_bets)
        
        # Calculate revenue
        total_revenue = 0
        total_bets_amount = 0
        total_wins = 0
        total_losses = 0
        
        for bet_doc in all_bets:
            bet_data = bet_doc.to_dict()
            commission = bet_data.get('platform_commission', 0)
            total_revenue += commission
            total_bets_amount += bet_data.get('bet_amount', 0)
            
            if bet_data.get('is_correct'):
                total_wins += 1
            else:
                total_losses += 1
        
        # Today's stats
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_bets_ref = bets_ref.where('timestamp', '>=', today_start)
        today_bets = list(today_bets_ref.stream())
        
        today_revenue = sum(bet.to_dict().get('platform_commission', 0) for bet in today_bets)
        today_bets_count = len(today_bets)
        
        return {
            'total_users': total_users,
            'total_bets': total_bets,
            'total_revenue': total_revenue,
            'total_bets_amount': total_bets_amount,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'win_rate': (total_wins / total_bets * 100) if total_bets > 0 else 0,
            'today_revenue': today_revenue,
            'today_bets': today_bets_count,
            'total_quizzes': len(QUIZ_DATABASE)
        }
    except Exception as e:
        logger.error(f"❌ Get admin stats error: {e}")
        return {}

def get_recent_bets(limit=20):
    """Get recent bets"""
    try:
        bets_ref = db.collection('bets').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        bets = []
        
        for bet_doc in bets_ref.stream():
            bet_data = bet_doc.to_dict()
            
            # Get user info
            try:
                user_doc = db.collection('users').document(bet_data.get('user_id')).get()
                if user_doc.exists:
                    bet_data['username'] = user_doc.to_dict().get('username', 'Unknown')
            except:
                bet_data['username'] = 'Unknown'
            
            # Get quiz info
            quiz = next((q for q in QUIZ_DATABASE if q['id'] == bet_data.get('quiz_id')), None)
            if quiz:
                bet_data['quiz_question'] = quiz['question']
            
            bets.append(bet_data)
        
        return bets
    except Exception as e:
        logger.error(f"❌ Get recent bets error: {e}")
        return []

def get_recent_users(limit=10):
    """Get recent users"""
    try:
        users_ref = db.collection('users').order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
        users = []
        
        for user_doc in users_ref.stream():
            user_data = user_doc.to_dict()
            user_data['uid'] = user_doc.id
            users.append(user_data)
        
        return users
    except Exception as e:
        logger.error(f"❌ Get recent users error: {e}")
        return []

def get_top_players(limit=10):
    """Get top players by wins"""
    try:
        users_ref = db.collection('users').order_by('total_wins', direction=firestore.Query.DESCENDING).limit(limit)
        players = []
        
        for user_doc in users_ref.stream():
            user_data = user_doc.to_dict()
            user_data['uid'] = user_doc.id
            
            # Calculate win rate
            total_bets = user_data.get('total_bets', 0)
            total_wins = user_data.get('total_wins', 0)
            user_data['win_rate'] = (total_wins / total_bets * 100) if total_bets > 0 else 0
            
            players.append(user_data)
        
        return players
    except Exception as e:
        logger.error(f"❌ Get top players error: {e}")
        return []

def calculate_revenue_breakdown():
    """Calculate detailed revenue breakdown"""
    try:
        bets_ref = db.collection('bets')
        all_bets = list(bets_ref.stream())
        
        # By day (last 7 days)
        daily_revenue = {}
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_revenue[date] = 0
        
        # By quiz
        quiz_revenue = {q['id']: 0 for q in QUIZ_DATABASE}
        
        for bet_doc in all_bets:
            bet_data = bet_doc.to_dict()
            commission = bet_data.get('platform_commission', 0)
            
            # Daily breakdown
            bet_date = bet_data.get('date', '')[:10]
            if bet_date in daily_revenue:
                daily_revenue[bet_date] += commission
            
            # Quiz breakdown
            quiz_id = bet_data.get('quiz_id')
            if quiz_id in quiz_revenue:
                quiz_revenue[quiz_id] += commission
        
        return {
            'daily': daily_revenue,
            'by_quiz': quiz_revenue
        }
    except Exception as e:
        logger.error(f"❌ Revenue breakdown error: {e}")
        return {'daily': {}, 'by_quiz': {}}