# 🏥 Hospital Rafá — Sistema de Farmacia

Sistema web completo para gestión de farmacia hospitalaria.

---

## 📋 Módulos incluidos

- ✅ Login con 5 roles (Admin, Farmacéutico, Recepcionista, Doctor, Cajero)
- ✅ Dashboard con estadísticas en tiempo real
- ✅ Punto de venta (POS) con código de barras
- ✅ Inventario completo de medicamentos
- ✅ Registro de compras y entradas
- ✅ Gestión de pacientes con historial
- ✅ Historial de ventas con filtros
- ✅ Control de caja
- ✅ Alertas de stock y vencimientos
- ✅ Reportes y estadísticas
- ✅ Tickets de venta imprimibles

---

## 🚀 CÓMO SUBIR A RAILWAY (Paso a paso)

### PASO 1 — Crear cuenta en GitHub
1. Ve a https://github.com
2. Crea una cuenta gratis

### PASO 2 — Subir el código
1. En GitHub, crea un repositorio nuevo llamado `hospital-rafa`
2. Sube todos estos archivos al repositorio

### PASO 3 — Crear cuenta en Railway
1. Ve a https://railway.app
2. Crea cuenta con tu Gmail
3. Clic en "New Project"
4. Selecciona "Deploy from GitHub repo"
5. Conecta tu repositorio `hospital-rafa`

### PASO 4 — Configurar variables
En Railway, ve a tu proyecto → Variables y agrega:
```
SECRET_KEY = hospitalrafa-2024-secreto
```

### PASO 5 — Railway despliega automáticamente
En unos minutos tendrás un link como:
`https://hospital-rafa.up.railway.app`

---

## 👥 Usuarios iniciales
| Usuario | Correo | Contraseña | Rol |
|---------|--------|------------|-----|
| Abdias | sistemacom40@gmail.com | Admin123 | Administrador |
| Farmacia | farmacia@hospitalrafa.com | Farma123 | Farmacéutico |

---

## 🔐 Permisos por rol
| Módulo | Admin | Farmacéutico | Recepcionista | Doctor | Cajero |
|--------|-------|-------------|---------------|--------|--------|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ |
| Nueva Venta | ✅ | ✅ | - | - | ✅ |
| Inventario | ✅ | ✅ | - | - | - |
| Compras | ✅ | ✅ | - | - | - |
| Pacientes | ✅ | ✅ | ✅ | ✅ | - |
| Caja | ✅ | - | - | - | ✅ |
| Alertas | ✅ | ✅ | - | - | - |
| Reportes | ✅ | - | - | - | - |
| Usuarios | ✅ | - | - | - | - |

---

## 💻 Correr localmente (para probar antes de subir)
```bash
pip install -r requirements.txt
python app.py
```
Abre: http://localhost:5000
