from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'hospitalrafa-secret-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///hospitalrafa.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ═══════════════════════════════════════
# MODELOS
# ═══════════════════════════════════════

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(50), nullable=False)  # admin, farmaceutico, recepcionista, doctor, cajero
    activo = db.Column(db.Boolean, default=True)
    creado = db.Column(db.DateTime, default=datetime.utcnow)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(80))
    presentacion = db.Column(db.String(100))
    stock = db.Column(db.Integer, default=0)
    stock_min = db.Column(db.Integer, default=5)
    costo = db.Column(db.Float, default=0)
    precio = db.Column(db.Float, nullable=False)
    vencimiento = db.Column(db.Date, nullable=True)
    proveedor = db.Column(db.String(100))
    codigo_barras = db.Column(db.String(50), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    creado = db.Column(db.DateTime, default=datetime.utcnow)

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    dpi = db.Column(db.String(20), nullable=True)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(120), nullable=True)
    direccion = db.Column(db.String(200))
    creado = db.Column(db.DateTime, default=datetime.utcnow)

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=True)
    paciente_nombre = db.Column(db.String(150), default='Cliente general')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    metodo_pago = db.Column(db.String(30), default='efectivo')
    subtotal = db.Column(db.Float, default=0)
    descuento = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    con_receta = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('VentaItem', backref='venta', lazy=True)

class VentaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'))
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    producto_nombre = db.Column(db.String(150))
    cantidad = db.Column(db.Integer)
    precio_unit = db.Column(db.Float)
    subtotal = db.Column(db.Float)

class Compra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    producto_nombre = db.Column(db.String(150))
    proveedor = db.Column(db.String(100))
    cantidad = db.Column(db.Integer)
    costo_unit = db.Column(db.Float)
    total = db.Column(db.Float)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class CajaMovimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20))  # apertura, cierre, venta, devolucion
    monto = db.Column(db.Float)
    descripcion = db.Column(db.String(200))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# ═══════════════════════════════════════
# PERMISOS POR ROL
# ═══════════════════════════════════════
PERMISOS = {
    'admin':          ['dashboard','usuarios','inventario','ventas','compras','pacientes','recetas','caja','reportes','alertas'],
    'farmaceutico':   ['dashboard','inventario','ventas','compras','pacientes','recetas','alertas'],
    'recepcionista':  ['dashboard','pacientes','citas'],
    'doctor':         ['dashboard','pacientes','recetas'],
    'cajero':         ['dashboard','ventas','caja'],
}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def permiso_requerido(modulo):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('login'))
            rol = session.get('rol', '')
            if modulo not in PERMISOS.get(rol, []):
                flash('No tienes permiso para acceder a esta sección.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# ═══════════════════════════════════════
# RUTAS AUTH
# ═══════════════════════════════════════
@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo','').strip()
        password = request.form.get('password','')
        usuario = Usuario.query.filter_by(correo=correo, activo=True).first()
        if usuario and check_password_hash(usuario.password, password):
            session['usuario_id'] = usuario.id
            session['nombre'] = usuario.nombre
            session['rol'] = usuario.rol
            session['correo'] = usuario.correo
            return redirect(url_for('dashboard'))
        flash('Correo o contraseña incorrectos.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ═══════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════
@app.route('/dashboard')
@login_required
def dashboard():
    rol = session.get('rol')
    permisos = PERMISOS.get(rol, [])
    hoy = date.today()

    stats = {}
    if 'ventas' in permisos:
        ventas_hoy = Venta.query.filter(db.func.date(Venta.fecha) == hoy).all()
        stats['ventas_hoy'] = len(ventas_hoy)
        stats['total_hoy'] = sum(v.total for v in ventas_hoy)
        stats['ultimas_ventas'] = Venta.query.order_by(Venta.fecha.desc()).limit(6).all()

    if 'inventario' in permisos:
        stats['total_productos'] = Producto.query.filter_by(activo=True).count()
        stats['stock_bajo'] = Producto.query.filter(Producto.stock < Producto.stock_min, Producto.activo==True).count()

    if 'pacientes' in permisos:
        stats['total_pacientes'] = Paciente.query.count()

    alertas = []
    if 'alertas' in permisos or 'inventario' in permisos:
        productos_bajo = Producto.query.filter(Producto.stock < Producto.stock_min, Producto.activo==True).all()
        for p in productos_bajo:
            alertas.append({'tipo': 'warning', 'msg': f'{p.nombre} — Stock bajo ({p.stock} uds)'})
        productos_venc = Producto.query.filter(Producto.vencimiento != None, Producto.activo==True).all()
        for p in productos_venc:
            if p.vencimiento:
                dias = (p.vencimiento - hoy).days
                if dias < 0:
                    alertas.append({'tipo': 'danger', 'msg': f'{p.nombre} — VENCIDO'})
                elif dias <= 30:
                    alertas.append({'tipo': 'warning', 'msg': f'{p.nombre} — Vence en {dias} días'})

    stats['alertas'] = alertas[:5]
    stats['total_alertas'] = len(alertas)

    return render_template('dashboard.html', stats=stats, permisos=permisos)

# ═══════════════════════════════════════
# USUARIOS
# ═══════════════════════════════════════
@app.route('/usuarios')
@permiso_requerido('usuarios')
def usuarios():
    lista = Usuario.query.all()
    return render_template('usuarios.html', usuarios=lista)

@app.route('/usuarios/nuevo', methods=['POST'])
@permiso_requerido('usuarios')
def nuevo_usuario():
    data = request.form
    if Usuario.query.filter_by(correo=data['correo']).first():
        flash('El correo ya está registrado.', 'error')
        return redirect(url_for('usuarios'))
    u = Usuario(
        nombre=data['nombre'],
        correo=data['correo'],
        password=generate_password_hash(data['password']),
        rol=data['rol']
    )
    db.session.add(u)
    db.session.commit()
    flash('Usuario creado correctamente.', 'success')
    return redirect(url_for('usuarios'))

@app.route('/usuarios/editar/<int:id>', methods=['POST'])
@permiso_requerido('usuarios')
def editar_usuario(id):
    u = Usuario.query.get_or_404(id)
    u.nombre = request.form['nombre']
    u.correo = request.form['correo']
    u.rol = request.form['rol']
    if request.form.get('password'):
        u.password = generate_password_hash(request.form['password'])
    db.session.commit()
    flash('Usuario actualizado.', 'success')
    return redirect(url_for('usuarios'))

@app.route('/usuarios/toggle/<int:id>')
@permiso_requerido('usuarios')
def toggle_usuario(id):
    u = Usuario.query.get_or_404(id)
    u.activo = not u.activo
    db.session.commit()
    return redirect(url_for('usuarios'))

# ═══════════════════════════════════════
# INVENTARIO
# ═══════════════════════════════════════
@app.route('/inventario')
@permiso_requerido('inventario')
def inventario():
    categoria = request.args.get('categoria', '')
    busqueda = request.args.get('q', '')
    query = Producto.query.filter_by(activo=True)
    if categoria:
        query = query.filter_by(categoria=categoria)
    if busqueda:
        query = query.filter(Producto.nombre.ilike(f'%{busqueda}%'))
    productos = query.order_by(Producto.nombre).all()
    categorias = db.session.query(Producto.categoria).distinct().all()
    hoy = date.today()
    return render_template('inventario.html', productos=productos, categorias=[c[0] for c in categorias], hoy=hoy)

@app.route('/inventario/nuevo', methods=['POST'])
@permiso_requerido('inventario')
def nuevo_producto():
    d = request.form
    venc = datetime.strptime(d['vencimiento'], '%Y-%m-%d').date() if d.get('vencimiento') else None
    p = Producto(
        nombre=d['nombre'], categoria=d['categoria'],
        presentacion=d.get('presentacion',''), stock=int(d.get('stock',0)),
        stock_min=int(d.get('stock_min',5)), costo=float(d.get('costo',0)),
        precio=float(d['precio']), vencimiento=venc,
        proveedor=d.get('proveedor',''), codigo_barras=d.get('codigo_barras','')
    )
    db.session.add(p)
    db.session.commit()
    flash('Producto agregado.', 'success')
    return redirect(url_for('inventario'))

@app.route('/inventario/editar/<int:id>', methods=['POST'])
@permiso_requerido('inventario')
def editar_producto(id):
    p = Producto.query.get_or_404(id)
    d = request.form
    p.nombre = d['nombre']; p.categoria = d['categoria']
    p.presentacion = d.get('presentacion','')
    p.stock = int(d.get('stock', p.stock))
    p.stock_min = int(d.get('stock_min', p.stock_min))
    p.costo = float(d.get('costo', p.costo))
    p.precio = float(d['precio'])
    p.proveedor = d.get('proveedor','')
    p.codigo_barras = d.get('codigo_barras','')
    if d.get('vencimiento'):
        p.vencimiento = datetime.strptime(d['vencimiento'], '%Y-%m-%d').date()
    db.session.commit()
    flash('Producto actualizado.', 'success')
    return redirect(url_for('inventario'))

@app.route('/inventario/eliminar/<int:id>')
@permiso_requerido('inventario')
def eliminar_producto(id):
    p = Producto.query.get_or_404(id)
    p.activo = False
    db.session.commit()
    flash('Producto eliminado.', 'success')
    return redirect(url_for('inventario'))

@app.route('/api/producto/barcode/<codigo>')
@login_required
def buscar_barcode(codigo):
    p = Producto.query.filter_by(codigo_barras=codigo, activo=True).first()
    if p:
        return jsonify({'id': p.id, 'nombre': p.nombre, 'precio': p.precio, 'stock': p.stock})
    return jsonify({'error': 'No encontrado'}), 404

@app.route('/api/productos')
@login_required
def api_productos():
    q = request.args.get('q', '')
    productos = Producto.query.filter(Producto.nombre.ilike(f'%{q}%'), Producto.activo==True, Producto.stock > 0).limit(20).all()
    return jsonify([{'id': p.id, 'nombre': p.nombre, 'precio': p.precio, 'stock': p.stock, 'categoria': p.categoria} for p in productos])

# ═══════════════════════════════════════
# VENTAS / POS
# ═══════════════════════════════════════
@app.route('/ventas')
@permiso_requerido('ventas')
def ventas():
    productos = Producto.query.filter_by(activo=True).filter(Producto.stock > 0).order_by(Producto.nombre).all()
    pacientes = Paciente.query.order_by(Paciente.nombre).all()
    return render_template('ventas.html', productos=productos, pacientes=pacientes)

@app.route('/ventas/procesar', methods=['POST'])
@permiso_requerido('ventas')
def procesar_venta():
    data = request.get_json()
    if not data or not data.get('items'):
        return jsonify({'error': 'Carrito vacío'}), 400

    paciente_id = data.get('paciente_id')
    paciente_nombre = data.get('paciente_nombre', 'Cliente general')
    metodo_pago = data.get('metodo_pago', 'efectivo')
    con_receta = data.get('con_receta', False)
    descuento = float(data.get('descuento', 0))

    subtotal = sum(item['precio'] * item['cantidad'] for item in data['items'])
    total = subtotal - descuento

    venta = Venta(
        paciente_id=paciente_id, paciente_nombre=paciente_nombre,
        usuario_id=session['usuario_id'], metodo_pago=metodo_pago,
        subtotal=subtotal, descuento=descuento, total=total, con_receta=con_receta
    )
    db.session.add(venta)
    db.session.flush()

    for item in data['items']:
        prod = Producto.query.get(item['id'])
        if not prod or prod.stock < item['cantidad']:
            db.session.rollback()
            return jsonify({'error': f'Stock insuficiente: {item["nombre"]}'}), 400
        prod.stock -= item['cantidad']
        vi = VentaItem(
            venta_id=venta.id, producto_id=prod.id,
            producto_nombre=prod.nombre, cantidad=item['cantidad'],
            precio_unit=item['precio'], subtotal=item['precio']*item['cantidad']
        )
        db.session.add(vi)

    caja = CajaMovimiento(tipo='venta', monto=total, descripcion=f'Venta #{venta.id}', usuario_id=session['usuario_id'])
    db.session.add(caja)
    db.session.commit()

    return jsonify({'ok': True, 'venta_id': venta.id, 'total': total})

@app.route('/ventas/ticket/<int:id>')
@login_required
def ticket(id):
    venta = Venta.query.get_or_404(id)
    return render_template('ticket.html', venta=venta)

# ═══════════════════════════════════════
# HISTORIAL
# ═══════════════════════════════════════
@app.route('/historial')
@permiso_requerido('ventas')
def historial():
    fecha_desde = request.args.get('desde', '')
    fecha_hasta = request.args.get('hasta', '')
    query = Venta.query
    if fecha_desde:
        query = query.filter(Venta.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d'))
    if fecha_hasta:
        query = query.filter(Venta.fecha <= datetime.strptime(fecha_hasta + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    ventas_lista = query.order_by(Venta.fecha.desc()).all()
    return render_template('historial.html', ventas=ventas_lista)

# ═══════════════════════════════════════
# PACIENTES
# ═══════════════════════════════════════
@app.route('/pacientes')
@permiso_requerido('pacientes')
def pacientes():
    q = request.args.get('q', '')
    query = Paciente.query
    if q:
        query = query.filter(Paciente.nombre.ilike(f'%{q}%'))
    lista = query.order_by(Paciente.nombre).all()
    return render_template('pacientes.html', pacientes=lista, q=q)

@app.route('/pacientes/nuevo', methods=['POST'])
@permiso_requerido('pacientes')
def nuevo_paciente():
    d = request.form
    fn = datetime.strptime(d['fecha_nacimiento'], '%Y-%m-%d').date() if d.get('fecha_nacimiento') else None
    p = Paciente(nombre=d['nombre'], dpi=d.get('dpi',''), fecha_nacimiento=fn,
                 telefono=d.get('telefono',''), correo=d.get('correo',''), direccion=d.get('direccion',''))
    db.session.add(p)
    db.session.commit()
    flash('Paciente registrado.', 'success')
    return redirect(url_for('pacientes'))

@app.route('/pacientes/<int:id>')
@permiso_requerido('pacientes')
def ver_paciente(id):
    paciente = Paciente.query.get_or_404(id)
    compras_hist = Venta.query.filter_by(paciente_id=id).order_by(Venta.fecha.desc()).all()
    return render_template('paciente_detalle.html', paciente=paciente, historial=compras_hist)

@app.route('/pacientes/editar/<int:id>', methods=['POST'])
@permiso_requerido('pacientes')
def editar_paciente(id):
    p = Paciente.query.get_or_404(id)
    d = request.form
    p.nombre = d['nombre']; p.dpi = d.get('dpi','')
    p.telefono = d.get('telefono',''); p.correo = d.get('correo','')
    p.direccion = d.get('direccion','')
    if d.get('fecha_nacimiento'):
        p.fecha_nacimiento = datetime.strptime(d['fecha_nacimiento'], '%Y-%m-%d').date()
    db.session.commit()
    flash('Paciente actualizado.', 'success')
    return redirect(url_for('ver_paciente', id=id))

# ═══════════════════════════════════════
# COMPRAS
# ═══════════════════════════════════════
@app.route('/compras')
@permiso_requerido('compras')
def compras():
    lista = Compra.query.order_by(Compra.fecha.desc()).all()
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    return render_template('compras.html', compras=lista, productos=productos)

@app.route('/compras/nueva', methods=['POST'])
@permiso_requerido('compras')
def nueva_compra():
    d = request.form
    prod = Producto.query.get_or_404(int(d['producto_id']))
    cantidad = int(d['cantidad'])
    costo = float(d.get('costo_unit', 0))
    prod.stock += cantidad
    c = Compra(producto_id=prod.id, producto_nombre=prod.nombre,
               proveedor=d.get('proveedor',''), cantidad=cantidad,
               costo_unit=costo, total=cantidad*costo, usuario_id=session['usuario_id'])
    db.session.add(c)
    db.session.commit()
    flash(f'Compra registrada. Stock de {prod.nombre} actualizado.', 'success')
    return redirect(url_for('compras'))

# ═══════════════════════════════════════
# CAJA
# ═══════════════════════════════════════
@app.route('/caja')
@permiso_requerido('caja')
def caja():
    hoy = date.today()
    movimientos = CajaMovimiento.query.filter(db.func.date(CajaMovimiento.fecha) == hoy).order_by(CajaMovimiento.fecha.desc()).all()
    total_ventas = sum(m.monto for m in movimientos if m.tipo == 'venta')
    return render_template('caja.html', movimientos=movimientos, total_ventas=total_ventas)

@app.route('/caja/movimiento', methods=['POST'])
@permiso_requerido('caja')
def nuevo_movimiento():
    d = request.form
    m = CajaMovimiento(tipo=d['tipo'], monto=float(d['monto']),
                       descripcion=d.get('descripcion',''), usuario_id=session['usuario_id'])
    db.session.add(m)
    db.session.commit()
    flash('Movimiento registrado.', 'success')
    return redirect(url_for('caja'))

# ═══════════════════════════════════════
# ALERTAS
# ═══════════════════════════════════════
@app.route('/alertas')
@permiso_requerido('alertas')
def alertas():
    hoy = date.today()
    stock_bajo = Producto.query.filter(Producto.stock < Producto.stock_min, Producto.activo==True).all()
    vencidos = Producto.query.filter(Producto.vencimiento < hoy, Producto.activo==True, Producto.vencimiento != None).all()
    por_vencer = Producto.query.filter(
        Producto.vencimiento >= hoy,
        Producto.vencimiento <= date(hoy.year, hoy.month+1 if hoy.month < 12 else 1, hoy.day),
        Producto.activo==True
    ).all()
    return render_template('alertas.html', stock_bajo=stock_bajo, vencidos=vencidos, por_vencer=por_vencer, hoy=hoy)

# ═══════════════════════════════════════
# REPORTES
# ═══════════════════════════════════════
@app.route('/reportes')
@permiso_requerido('reportes')
def reportes():
    hoy = date.today()
    # Ventas del día
    ventas_hoy = Venta.query.filter(db.func.date(Venta.fecha) == hoy).all()
    total_hoy = sum(v.total for v in ventas_hoy)
    # Valor inventario
    productos_activos = Producto.query.filter_by(activo=True).all()
    valor_costo = sum(p.costo * p.stock for p in productos_activos)
    valor_venta = sum(p.precio * p.stock for p in productos_activos)
    # Top productos (de VentaItem)
    from sqlalchemy import func
    top = db.session.query(
        VentaItem.producto_nombre,
        func.sum(VentaItem.cantidad).label('total_vendido')
    ).group_by(VentaItem.producto_nombre).order_by(func.sum(VentaItem.cantidad).desc()).limit(8).all()

    return render_template('reportes.html',
        ventas_hoy=ventas_hoy, total_hoy=total_hoy,
        valor_costo=valor_costo, valor_venta=valor_venta,
        top_productos=top, total_productos=len(productos_activos)
    )

# ═══════════════════════════════════════
# INICIALIZACIÓN
# ═══════════════════════════════════════
def init_db():
    with app.app_context():
        db.create_all()
        if not Usuario.query.first():
            usuarios_demo = [
                Usuario(nombre='Abdias', correo='sistemacom40@gmail.com',
                        password=generate_password_hash('Admin123'), rol='admin'),
                Usuario(nombre='Farmacia', correo='farmacia@hospitalrafa.com',
                        password=generate_password_hash('Farma123'), rol='farmaceutico'),
            ]
            for u in usuarios_demo:
                db.session.add(u)
            # Productos demo
            productos_demo = [
                Producto(nombre='Amoxicilina 500mg', categoria='Antibióticos', presentacion='Cápsulas x20',
                         stock=45, stock_min=10, costo=15.0, precio=28.50,
                         vencimiento=date(2026,8,15), proveedor='Farmex GT'),
                Producto(nombre='Paracetamol 500mg', categoria='Analgésicos', presentacion='Tabletas x20',
                         stock=120, stock_min=20, costo=4.50, precio=9.00,
                         vencimiento=date(2027,1,10), proveedor='MedSupply'),
                Producto(nombre='Ibuprofeno 400mg', categoria='Antiinflamatorios', presentacion='Tabletas x10',
                         stock=8, stock_min=15, costo=8.0, precio=15.00,
                         vencimiento=date(2026,5,20), proveedor='Farmex GT'),
                Producto(nombre='Omeprazol 20mg', categoria='Digestivo', presentacion='Cápsulas x14',
                         stock=30, stock_min=10, costo=22.0, precio=42.00,
                         vencimiento=date(2026,12,1), proveedor='MedSupply'),
                Producto(nombre='Vitamina C 1000mg', categoria='Vitaminas', presentacion='Tabletas x30',
                         stock=55, stock_min=15, costo=18.0, precio=35.00,
                         vencimiento=date(2027,6,30), proveedor='NutriMed'),
            ]
            for p in productos_demo:
                db.session.add(p)
            db.session.commit()
            print("✅ Base de datos inicializada con datos de prueba.")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
