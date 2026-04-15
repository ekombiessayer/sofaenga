import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sofaenga2026_super_secret_changez_moi')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DATABASE (SQLite dev → PostgreSQL Render)
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL'].replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sofaenga.db'

db = SQLAlchemy(app)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))  # recette, depense
    raison = db.Column(db.String(200))
    montant = db.Column(db.Float)
    date_heure = db.Column(db.DateTime, default=datetime.utcnow)
    service = db.Column(db.String(50))
    periode = db.Column(db.String(20), default='tous')

class LocationVoiture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_client = db.Column(db.String(100))
    tel = db.Column(db.String(20))
    adresse = db.Column(db.String(200))
    voiture = db.Column(db.String(50))
    prix_jour = db.Column(db.Float)
    nb_jours = db.Column(db.Integer)
    montant = db.Column(db.Float)
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)

class Formation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    tel = db.Column(db.String(20))
    formation_type = db.Column(db.String(100))
    montant = db.Column(db.Float)
    date_formation = db.Column(db.Date)
    nb_seances = db.Column(db.Integer)
    date_fin = db.Column(db.Date)

class AssistanceVoyage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_client = db.Column(db.String(100))
    type_assistance = db.Column(db.String(50))
    nb_personnes = db.Column(db.Integer)
    montant = db.Column(db.Float)

class SousTraitance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_agent = db.Column(db.String(100))
    lieu_affectation = db.Column(db.String(100))
    montant = db.Column(db.Float)
    date_debut = db.Column(db.Date)

class Reception(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    nom = db.Column(db.String(100))
    tel = db.Column(db.String(20))
    motif = db.Column(db.String(100))
    direction = db.Column(db.String(50))
    services_compromis = db.Column(db.Text)

class OffreEmploi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.String(20), unique=True)
    titre_poste = db.Column(db.String(100))
    nb_postes = db.Column(db.Integer)
    description = db.Column(db.Text)
    date_fin = db.Column(db.Date)
    exigences = db.Column(db.Text)

class MessageInterService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_origine = db.Column(db.String(50))
    service_dest = db.Column(db.String(50))
    contenu = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    lu = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)

# MOTS DE PASSE (OK)
MOTS_DE_PASSE = {
    'finance': 'PAPA',
    'location': 'PAPA', 
    'formation': 'PAPA',
    'travail': 'PAPA',
    'strayant': 'PAPA',
    'reception': 'PAPA',
    'direction': 'PAPA1'
}


@app.route('/')
def index():
    offres = OffreEmploi.query.all()
    return render_template('index.html', offres=offres)

@app.route('/bureau')
def bureau():
    if session.get('master_access') != 'granted':
        return redirect(url_for('master_login'))
    return render_template('bureau.html')
@app.route('/master_login', methods=['GET', 'POST'])
def master_login():
    if request.method == 'POST':
        password = request.form['master_password']
        if password == 'sofaenga2026':  # ← TON MDP FIXE
            session['master_access'] = 'granted'
            flash('✅ Accès maître autorisé !', 'success')
            return redirect(url_for('bureau'))
        else:
            flash('❌ Mot de passe maître incorrect !', 'error')
    return render_template('master_login.html')

# Navbar → master_login au lieu de bureau direct
@app.route('/admin')  # Lien navbar
def admin_access():
    return redirect(url_for('master_login'))

# 3. LOGIN SERVICE ✅ CORRIGÉ
@app.route('/login_service', methods=['GET', 'POST'])
def login_service():
    if request.method == 'POST':
        service = request.form['service']
        password = request.form['password']
        
        if service in MOTS_DE_PASSE and MOTS_DE_PASSE[service] == password:
            session['service'] = service
            flash(f'Bienvenue dans {service.capitalize()}', 'success')
            return redirect(url_for(service))  # ← DÉSORMAIS url_for('finance') marche
        else:
            flash('❌ Mot de passe incorrect !', 'error')
    
    return render_template('login_service.html')

# 4. LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    flash('Déconnecté avec succès', 'info')
    return redirect(url_for('index'))
@app.route('/finance')
def finance():
    if session.get('service') != 'finance':
        return redirect(url_for('login_service'))
    # Stats
    total_recettes = db.session.query(db.func.sum(Transaction.montant)).filter(Transaction.type == 'recette').scalar() or 0
    total_depenses = db.session.query(db.func.sum(Transaction.montant)).filter(Transaction.type == 'depense').scalar() or 0
    total_general = total_recettes - total_depenses
    transactions = Transaction.query.order_by(Transaction.date_heure.desc()).limit(100).all()
    return render_template('finance.html', 
                         tresorerie=total_general, recettes=total_recettes,
                         depenses=total_depenses, transactions=transactions)

@app.route('/ajouter_depense', methods=['POST'])
def ajouter_depense():
    if session.get('service') != 'finance':
        return jsonify({'error': 'Accès refusé'}), 403
    raison = request.form['raison']
    montant = float(request.form['montant'])
    t = Transaction(type='depense', raison=raison, montant=montant, service='finance')
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('finance'))

@app.route('/location')
def location():
    if session.get('service') != 'location':
        return redirect(url_for('login_service'))
    locations = LocationVoiture.query.order_by(LocationVoiture.id.desc()).all()
    return render_template('location.html', locations=locations)

@app.route('/enregistrer_location', methods=['POST'])
def enregistrer_location():
    if session.get('service') != 'location':
        return jsonify({'error': 'Accès refusé'}), 403
    nom_client = request.form['nom_client']
    tel = request.form['tel']
    voiture = request.form['voiture']
    prix_jour = float(request.form['prix_jour'])
    nb_jours = int(request.form['nb_jours'])
    date_debut = datetime.strptime(request.form['date_debut'], '%Y-%m-%d').date()
    montant = prix_jour * nb_jours
    date_fin = date_debut + timedelta(days=nb_jours)
    
    loc = LocationVoiture(nom_client=nom_client, tel=tel, voiture=voiture,
                         prix_jour=prix_jour, nb_jours=nb_jours, montant=montant,
                         date_debut=date_debut, date_fin=date_fin)
    db.session.add(loc)
    
    t = Transaction(type='recette', raison=f'Location {nom_client} - {voiture}', 
                    montant=montant, service='location')
    db.session.add(t)
    db.session.commit()
    flash('Location enregistrée + recette finance OK !', 'success')
    return redirect(url_for('finance'))

@app.route('/formation')
def formation():
    if session.get('service') != 'formation':
        return redirect(url_for('login_service'))
    formations = Formation.query.order_by(Formation.id.desc()).all()
    return render_template('formation.html', formations=formations)

@app.route('/enregistrer_formation', methods=['POST'])
def enregistrer_formation():
    if session.get('service') != 'formation':
        return jsonify({'error': 'Accès refusé'}), 403
    nom = request.form['nom']
    tel = request.form['tel']
    formation_type = request.form['formation']
    montant = float(request.form['montant'])
    date_formation = datetime.strptime(request.form['date_formation'], '%Y-%m-%d').date()
    nb_seances = int(request.form['nb_seances'])
    date_fin = date_formation + timedelta(days=nb_seances * 3)
    
    form = Formation(nom=nom, tel=tel, formation_type=formation_type, 
                     montant=montant, date_formation=date_formation,
                     nb_seances=nb_seances, date_fin=date_fin)
    db.session.add(form)
    
    t = Transaction(type='recette', raison=f'Formation {formation_type}', 
                    montant=montant, service='formation')
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('finance'))

# Autres routes (voyage, strayant, reception, direction...)
@app.route('/travel')
def travel():
    if session.get('service') != 'travail':
        return redirect(url_for('login_service'))
    voyages = AssistanceVoyage.query.order_by(AssistanceVoyage.id.desc()).all()
    return render_template('travel.html', voyages=voyages)

@app.route('/strayant')
def strayant():
    if session.get('service') != 'strayant':
        return redirect(url_for('login_service'))
    agents = SousTraitance.query.order_by(SousTraitance.id.desc()).all()
    return render_template('strayant.html', strayants=agents)

@app.route('/reception')
def reception():
    if session.get('service') != 'reception':
        return redirect(url_for('login_service'))
    visiteurs = Reception.query.order_by(Reception.date.desc()).all()
    return render_template('reception.html', receptions=visiteurs)

@app.route('/direction')
def direction():
    if session.get('service') != 'direction':
        return redirect(url_for('login_service'))
    stats = {
        'total_recettes': db.session.query(db.func.sum(Transaction.montant)).filter(Transaction.type == 'recette').scalar() or 0,
        'total_depenses': db.session.query(db.func.sum(Transaction.montant)).filter(Transaction.type == 'depense').scalar() or 0,
        'locations': LocationVoiture.query.count(),
        'formations': Formation.query.count()
    }
    return render_template('direction.html', stats=stats)

# Messagerie (OK)
@app.route('/send_message', methods=['POST'])
def send_message():
    if 'service' not in session:
        return jsonify({'error': 'Non connecté'}), 403
    service_dest = request.json['service_dest']
    contenu = request.json['contenu']
    msg = MessageInterService(service_origine=session['service'], service_dest=service_dest, contenu=contenu)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/get_messages')
def get_messages():
    if 'service' not in session:
        return jsonify({'error': 'Non connecté'}), 403
    messages = MessageInterService.query.filter_by(service_dest=session['service'], deleted=False).order_by(MessageInterService.date.desc()).all()
    return jsonify([{'origine': m.service_origine, 'contenu': m.contenu, 'date': m.date.strftime('%d/%m %H:%M')} for m in messages])

# 1. Cette partie doit être "libre" (pas cachée dans le if name)
with app.app_context():
    db.create_all()
    if OffreEmploi.query.count() == 0:
        offre1 = OffreEmploi(
            num='SOF-001', 
            titre_poste='Chauffeur VIP', 
            nb_postes=3,
            description='Location voitures avec chauffeur', 
            date_fin=datetime(2026, 5, 15).date(),
            exigences='Permis B, 5 ans expérience'
        )
        db.session.add(offre1)
        db.session.commit()

# 2. Ce bloc ne sert que pour ton PC local
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)