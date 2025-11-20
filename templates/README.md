# 🎯 Quiz Paryaj - Platform Legal pou Genyen Lajan

Yon platform quiz skill-based kote itilizatè yo mete 25 HTG pou reponn kesyon futbòl. Si yo kòrèk, yo genyen 35-60 HTG. Si yo echwe, yo pèdi.

## 💰 Modèl Biznis

- **15% komisyon** sou chak paryaj
- Itilizatè genyen oswa pèdi → Ou toujou fè lajan
- Pa gen risk pou ou kòm pwopriete
- Revni pasif 24/7

## 🎮 Karakteristik

✅ 10 Quiz avèk kesyon/repons  
✅ 3 Nivo difikilte (Fasil, Mwayen, Difisil)  
✅ Peman MonCash reyèl  
✅ Firebase database sekirize  
✅ Sistema login/signup konplè  
✅ Dashboard ak estatistik  
✅ Istwa paryaj  
✅ Mobile-responsive  

## 📋 Prerequi

- Python 3.8+
- Firebase account
- MonCash Business account
- Git

## 🚀 Enstalasyon Lokal

### 1. Clone repository
```bash
git clone https://github.com/your-username/quiz-paryaj.git
cd quiz-paryaj
```

### 2. Kreye virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Konfigire environment variables
```bash
# Kopye .env.example nan .env
cp .env.example .env

# Modifye .env ak enfòmasyon ou yo
nano .env  # oswa open .env
```

### 5. Run aplikasyon
```bash
python app.py
```

Aplikasyon an ap kouri sou: `http://localhost:5000`

---

## 🌐 Deploiement sou Render

### 1. Kreye kont Render
Ale sou [render.com](https://render.com) epi kreye yon kont

### 2. Connect GitHub
- Click "New +" → "Web Service"
- Connect repository ou a
- Chwazi branch `main`

### 3. Configure Build Settings
```
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app --bind 0.0.0.0:$PORT
```

### 4. Add Environment Variables
Nan Render dashboard, ajoute tout variables nan `.env`:
- `FIREBASE_SERVICE_ACCOUNT_JSON`
- `MONCASH_CLIENT_ID`
- `MONCASH_CLIENT_SECRET`
- `SECRET_KEY`

### 5. Deploy
Click "Create Web Service" - Done!

---

## 🔐 Firebase Setup

### 1. Kreye Firebase Project
1. Ale sou [console.firebase.google.com](https://console.firebase.google.com)
2. Click "Add project"
3. Swiv etap yo

### 2. Enable Firestore Database
1. Nan Firebase console, click "Firestore Database"
2. Click "Create database"
3. Chwazi "Start in production mode"
4. Chwazi yon location

### 3. Generate Service Account Key
1. Project Settings → Service Accounts
2. Click "Generate new private key"
3. Telechaje JSON file la
4. Kopye tout kontni JSON la nan `FIREBASE_SERVICE_ACCOUNT_JSON`

### 4. Enable Authentication
1. Authentication → Sign-in method
2. Enable "Email/Password"

---

## 💳 MonCash Setup

### 1. Kreye MonCash Business Account
1. Ale sou [moncashbutton.digicelgroup.com](https://moncashbutton.digicelgroup.com)
2. Enskri pou yon kont biznis
3. Swiv pwosesis validation

### 2. Get API Credentials
1. Login nan MonCash dashboard
2. Ale nan "API Settings"
3. Kopye:
   - Client ID
   - Client Secret
4. Mete yo nan `.env`

### 3. Configure Webhooks (Optional)
- Return URL: `https://your-app.onrender.com/moncash-return`

---

## 📊 Estatistik & Analytics

### Revni Estimasyon

| Paryaj/Jou | Komisyon 15% | Revni/Jou | Revni/Mwa |
|------------|--------------|-----------|-----------|
| 100        | 3.75 HTG     | 375 HTG   | 11,250 HTG |
| 500        | 3.75 HTG     | 1,875 HTG | 56,250 HTG |
| 1,000      | 3.75 HTG     | 3,750 HTG | 112,500 HTG |

### Wè Estatistik
```bash
# Check health endpoint
curl https://your-app.onrender.com/health
```

---

## 🛠️ Maintenance

### Update Quiz Questions
Modifye `QUIZ_DATABASE` nan `app.py`:
```python
QUIZ_DATABASE = [
    {
        'id': 11,  # Nouvo ID
        'category': 'Futbòl',
        'difficulty': 'Fasil',
        'question': 'Nouvo kesyon?',
        'options': ['A', 'B', 'C', 'D'],
        'correct_answer': 'A',
        'bet_amount': 25,
        'win_amount': 40,
        'explanation': 'Eksplikasyon...'
    },
    # Ajoute plis quiz...
]
```

### Change Commission Rate
Modifye `PaymentConfig.PLATFORM_COMMISSION` nan `app.py`:
```python
PLATFORM_COMMISSION = 20  # Change to 20%
```

### View Database
```python
# Python shell
from firebase_admin import firestore
db = firestore.client()

# Get all users
users = db.collection('users').stream()
for user in users:
    print(user.to_dict())

# Get all bets
bets = db.collection('bets').stream()
for bet in bets:
    print(bet.to_dict())
```

---

## 🐛 Troubleshooting

### Error: Firebase not initialized
**Solution:** Verifye `FIREBASE_SERVICE_ACCOUNT_JSON` nan `.env`

### Error: MonCash authentication failed
**Solution:** Verifye `MONCASH_CLIENT_ID` ak `MONCASH_CLIENT_SECRET`

### Error: Template not found
**Solution:** Verifye estrikti dosye `templates/quiz_betting/`

### Application crashes on startup
**Solution:** Check logs:
```bash
# Render
Dashboard → Logs

# Local
python app.py
```

---

## 📞 Support

Pou kesyon oswa sipò:
- Email: support@quizparyaj.ht
- WhatsApp: +509 XXXX-XXXX

---

## ⚖️ Legal & Compliance

- ✅ Skill-based quiz (pa kazino)
- ✅ 18+ itilizatè sèlman
- ✅ Tèm ak kondisyon klè
- ✅ Peman sekirize
- ✅ Transparent

---

## 📝 License

Tout dwa rezève © 2025 Quiz Paryaj

---

## 🎯 Roadmap

- [ ] Ajoute plis kategori quiz
- [ ] Leader board
- [ ] Referral system
- [ ] Mobile app (iOS/Android)
- [ ] Live quiz tournaments
- [ ] Multi-language support

---

**Made with ❤️ for Haitian entrepreneurs**
```