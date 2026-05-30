import os
import uuid
import mimetypes
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import httpx
from flask_wtf.csrf import CSRFProtect

load_dotenv()

SUPABASE_URL    = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY    = os.environ.get('SUPABASE_SERVICE_KEY', '')
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'fotos')

def _supabase_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }

def subir_imagen_supabase(file_storage) -> str | None:
    if not (SUPABASE_URL and SUPABASE_KEY):
        print("[Supabase] ERROR: Faltan variables SUPABASE_URL o SUPABASE_SERVICE_KEY")
        return None

    original = secure_filename(file_storage.filename)
    ext      = original.rsplit('.', 1)[-1].lower() if '.' in original else 'jpg'
    filename = f"{uuid.uuid4().hex}.{ext}"
    data     = file_storage.read()
    mime     = mimetypes.guess_type(original)[0] or 'application/octet-stream'

    url     = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
    headers = {**_supabase_headers(), 'Content-Type': mime}

    resp = httpx.put(url, content=data, headers=headers)
    if resp.status_code not in (200, 201):
        print(f"[Supabase] ERROR al subir {filename}: {resp.status_code} {resp.text}")
        return None

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
    return public_url

def eliminar_imagen_supabase(url: str):
    if not url or not (SUPABASE_URL and SUPABASE_KEY):
        return
    prefix = f"/storage/v1/object/public/{SUPABASE_BUCKET}/"
    if prefix not in url:
        return
    filename = url.split(prefix)[-1]
    del_url  = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
    httpx.delete(del_url, headers=_supabase_headers())

def procesar_imagen(file_storage) -> str | None:
    if not file_storage or not allowed_file(file_storage.filename):
        return None
    return subir_imagen_supabase(file_storage)

# ── Flask app ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config['DEBUG'] = os.environ.get('FLASK_ENV') == 'development'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '')
csrf = CSRFProtect(app)
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp', 'jfif'}
app.config['MAX_CONTENT_LENGTH'] = 35 * 1024 * 1024

uri = os.environ.get('DATABASE_URL')
if uri:
    print("DEBUG: ¡ÉXITO! Encontré la URL en el .env")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
else:
    print("DEBUG: ¡ERROR! No encontré ninguna URL. Usando SQLite.")
    uri = 'sqlite:///site.db'

app.config['SQLALCHEMY_DATABASE_URI']        = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db            = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ==========================================
# MODELOS
# ==========================================

class Admin(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class ConfiguracionGlobal(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    titulo_sitio     = db.Column(db.String(100), nullable=False, default="KAROL G")

    # Navbar
    sec_music        = db.Column(db.String(50), default="MUSIC")
    sec_tour         = db.Column(db.String(50), default="TOUR")
    sec_merch        = db.Column(db.String(50), default="MERCH")
    sec_video        = db.Column(db.String(50), default="VIDEO")

    # Redes sociales
    link_whatsapp    = db.Column(db.String(500), nullable=True, default="")
    link_instagram   = db.Column(db.String(500), nullable=True, default="")
    link_tiktok      = db.Column(db.String(500), nullable=True, default="")

    # Sección Hero (fondo total de pantalla)
    imagen_fondo     = db.Column(db.String(500), nullable=True, default="")  # fondo general

    # Sección 1: Hero principal
    imagen_titulo    = db.Column(db.String(500), nullable=True, default="")
    imagen_artista   = db.Column(db.String(500), nullable=True, default="")
    imagen_artista_2 = db.Column(db.String(500), nullable=True, default="")
    imagen_artista_3 = db.Column(db.String(500), nullable=True, default="")

    # Sección 2: Latest Release
    imagen_release   = db.Column(db.String(500), nullable=True, default="")  # foto del album/single
    titulo_release   = db.Column(db.String(200), nullable=True, default="UNA NOCHE EN MEDELLÍN")
    subtitulo_release= db.Column(db.String(200), nullable=True, default="X CRIS MJ X CASTRO")
    link_spotify     = db.Column(db.String(500), nullable=True, default="#")

    # Sección 3: Tour dates
    imagen_tour      = db.Column(db.String(500), nullable=True, default="")  # imagen completa de tour dates

    # Sección 4: Merch
    imagen_merch_1   = db.Column(db.String(500), nullable=True, default="")
    imagen_merch_2   = db.Column(db.String(500), nullable=True, default="")
    imagen_merch_3   = db.Column(db.String(500), nullable=True, default="")
    imagen_merch_4   = db.Column(db.String(500), nullable=True, default="")
    link_merch       = db.Column(db.String(500), nullable=True, default="#")

    # Nave flotante
    imagen_nave           = db.Column(db.String(500), nullable=True, default="")
    imagen_nave_2         = db.Column(db.String(500), nullable=True, default="")
    imagen_nave_3         = db.Column(db.String(500), nullable=True, default="")
    # Nave perseguidora
    imagen_perseguidora   = db.Column(db.String(500), nullable=True, default="")
    imagen_perseguidora_2 = db.Column(db.String(500), nullable=True, default="")
    imagen_perseguidora_3 = db.Column(db.String(500), nullable=True, default="")

# ==========================================
# LOGIN / CONTEXT PROCESSOR
# ==========================================

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

@app.context_processor
def inject_global_config():
    config = ConfiguracionGlobal.query.first()
    if not config:
        config = ConfiguracionGlobal()
        db.session.add(config)
        db.session.commit()
    return dict(global_config=config)

# ==========================================
# RUTAS PÚBLICAS
# ==========================================

@app.route('/')
def inicio():
    return render_template('inicio.html')

# ==========================================
# AUTENTICACIÓN
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        flash('Credenciales incorrectas.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('inicio'))

# ==========================================
# PANEL DE ADMINISTRACIÓN
# ==========================================

@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin.html')

# ── Configuración global ───────────────────────────────────────────────────────

@app.route('/admin/configuracion-global', methods=['POST'])
@login_required
def actualizar_configuracion_global():
    config = ConfiguracionGlobal.query.first()
    if not config:
        config = ConfiguracionGlobal()
        db.session.add(config)

    config.titulo_sitio       = request.form.get('titulo_sitio', 'KAROL G').upper()
    config.sec_music          = request.form.get('sec_music', 'MUSIC').upper()
    config.sec_tour           = request.form.get('sec_tour', 'TOUR').upper()
    config.sec_merch          = request.form.get('sec_merch', 'MERCH').upper()
    config.sec_video          = request.form.get('sec_video', 'VIDEO').upper()
    config.link_whatsapp      = request.form.get('link_whatsapp', '')
    config.link_instagram     = request.form.get('link_instagram', '')
    config.link_tiktok        = request.form.get('link_tiktok', '')
    config.titulo_release     = request.form.get('titulo_release', '')
    config.subtitulo_release  = request.form.get('subtitulo_release', '')
    config.link_spotify       = request.form.get('link_spotify', '#')
    config.link_merch         = request.form.get('link_merch', '#')

    # Imagen fondo general
    url = procesar_imagen(request.files.get('imagen_fondo'))
    if url:
        eliminar_imagen_supabase(config.imagen_fondo)
        config.imagen_fondo = url

    # Imagen título (BICHOTA png sin fondo)
    url = procesar_imagen(request.files.get('imagen_titulo'))
    if url:
        eliminar_imagen_supabase(config.imagen_titulo)
        config.imagen_titulo = url

    # Imagen artista (karol g con tiburon)
    url = procesar_imagen(request.files.get('imagen_artista'))
    if url:
        eliminar_imagen_supabase(config.imagen_artista)
        config.imagen_artista = url

    # Segunda imagen artista (alternante)
    url = procesar_imagen(request.files.get('imagen_artista_2'))
    if url:
        eliminar_imagen_supabase(config.imagen_artista_2)
        config.imagen_artista_2 = url

    # Tercera imagen artista (alternante)
    url = procesar_imagen(request.files.get('imagen_artista_3'))
    if url:
        eliminar_imagen_supabase(config.imagen_artista_3)
        config.imagen_artista_3 = url

    # Imagen latest release
    url = procesar_imagen(request.files.get('imagen_release'))
    if url:
        eliminar_imagen_supabase(config.imagen_release)
        config.imagen_release = url

    # Imagen tour dates
    url = procesar_imagen(request.files.get('imagen_tour'))
    if url:
        eliminar_imagen_supabase(config.imagen_tour)
        config.imagen_tour = url

    # Merch images
    for i in range(1, 5):
        url = procesar_imagen(request.files.get(f'imagen_merch_{i}'))
        if url:
            eliminar_imagen_supabase(getattr(config, f'imagen_merch_{i}'))
            setattr(config, f'imagen_merch_{i}', url)

    # Nave flotante
    for i in ['', '_2', '_3']:
        url = procesar_imagen(request.files.get(f'imagen_nave{i}'))
        if url:
            eliminar_imagen_supabase(getattr(config, f'imagen_nave{i}'))
            setattr(config, f'imagen_nave{i}', url)

    # Nave perseguidora
    for i in ['', '_2', '_3']:
        url = procesar_imagen(request.files.get(f'imagen_perseguidora{i}'))
        if url:
            eliminar_imagen_supabase(getattr(config, f'imagen_perseguidora{i}'))
            setattr(config, f'imagen_perseguidora{i}', url)

    db.session.commit()
    flash('Configuración actualizada con éxito.', 'success')
    return redirect(url_for('admin_dashboard'))

# ==========================================
# INICIO
# ==========================================

## Activar esto al hacer deploy:
with app.app_context():
     db.create_all()


"""if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        user = os.environ.get('ADMIN_USER')
        pwd  = os.environ.get('ADMIN_PASSWORD')

        if user and pwd:
            if not Admin.query.filter_by(username=user.strip()).first():
                hashed_pw = generate_password_hash(pwd.strip(), method='pbkdf2:sha256')
                db.session.add(Admin(username=user.strip(), password=hashed_pw))
                db.session.commit()
                print(f"✅ Usuario '{user.strip()}' creado correctamente.")
        else:
            print("⚠️ ERROR: No configuraste ADMIN_USER o ADMIN_PASSWORD en el archivo .env")
    app.run(debug=True)
"""