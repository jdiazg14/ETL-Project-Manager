# Análisis Detallado - Bootstrap Classes & Data-Attributes en Templates

**Fecha:** 9 de Marzo de 2026  
**Proyecto:** ETL Project Manager  
**Objetivo:** Identificar todas las dependencias de Bootstrap 5 para refactorización a Tailwind CSS

---

## 📊 RESUMEN EJECUTIVO

### Estadísticas Generales
- **Total de archivos HTML:** 24
- **Archivos con Bootstrap:** 5 (20.8%)
- **Archivos 100% Tailwind:** 19 (79.2%)
- **Criticidad:** ALTA (base.html + 2 archivos complejos con formularios)

### Nivel de Urgencia por Archivo
| Criticidad | Archivos | Acción |
|-----------|----------|--------|
| 🔴 CRÍTICO | base.html | Debe refactorizarse primero (modal + JS bootstrap) |
| 🟠 ALTO | distribuidores.html, grupos.html | Requieren refactorización completa del grid |
| 🟡 MODERADO | grupo_form.html | Formulario con clases Bootstrap |
| 🟢 BAJO | login.html | Una sola clase Bootstrap |

---

## 📝 ANÁLISIS POR ARCHIVO

---

### 1️⃣ **base.html** - 🔴 CRÍTICO

**Ubicación:** `app/templates/base.html`

#### Recursos Bootstrap (CDN)
```html
<!-- CDN CSS -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

<!-- Bootstrap JS Bundle -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
```

#### Clases Bootstrap Identificadas
| Clase | Ubicación | Reemplazo Tailwind |
|-------|-----------|-------------------|
| `.modal.fade` | Modal historial | `.hidden` (toggle) |
| `.modal-dialog`, `.modal-sm`, `.modal-dialog-centered` | Modal estructura | `fixed inset-0 flex items-center justify-center` |
| `.modal-content` | Modal container | `bg-white rounded-lg shadow-xl` |
| `.modal-header`, `.modal-title` | Modal encabezado | `px-6 py-4 flex justify-between items-center` |
| `.modal-body` | Modal cuerpo | `px-6 py-4 text-center` |
| `.modal-footer` | Modal pie | `px-6 py-4 flex justify-center gap-2 border-t` |
| `.btn-close`, `.btn-close-white` | Botón cerrar | `hover:opacity-75 transition` |
| `.btn`, `.d-flex`, `.justify-content-center` | Botones | Clases Tailwind equivalentes |

#### Data-Attributes de Bootstrap
```html
<!-- Modal trigger (DEBE CAMBIAR) -->
<a href="#" data-bs-toggle="modal" data-bs-target="#historialModal">

<!-- Dentro del modal -->
<button data-bs-dismiss="modal" aria-label="Cerrar">
```

#### "Función en Desarrollo" - ENCONTRADO ✓
```html
<!-- En: Modal #historialModal -->
<div class="modal-body text-center">
    Esta función se encuentra actualmente en desarrollo.
</div>
```

#### Cambios Necesarios
1. ✓ Quitar CDN de Bootstrap CSS
2. ✓ Quitar JS Bundle de Bootstrap
3. ✓ Reemplazar modal Bootstrap por estructura Tailwind
4. ✓ Cambiar `data-bs-toggle="modal"` a `onclick="showGlobalModal()"`
5. ✓ Implementar funciones `showGlobalModal()` y `hideGlobalModal()`
6. ✓ Reemplazar todas las clases del modal con Tailwind

**Bloqueador:** Este archivo es base para todo el sitio.

---

### 2️⃣ **config/distribuidores.html** - 🟠 ALTO

**Ubicación:** `app/templates/config/distribuidores.html`

#### Clases Bootstrap Identificadas (Grid & Layout)
```html
<!-- Grid System -->
<div class="container-fluid py-4">          <!-- → w-full py-4 -->
    <div class="row align-items-center mb-3">  <!-- → flex items-center mb-3 -->
        <div class="col-md-6 d-flex align-items-center">  <!-- → md:w-1/2 flex items-center -->
```

#### Form Controls
```html
<input type="text" class="form-control form-control-sm me-2">  
<!-- → bg-gray-50 border border-gray-300 rounded px-4 py-2 mr-2 -->

<button class="btn btn-outline-primary btn-sm me-2">
<!-- → border border-purple-600 text-purple-600 px-4 py-2 text-sm hover:bg-purple-50 -->
```

#### Componentes
```html
<!-- Tabla -->
<div class="card shadow-sm">
    <div class="card-body p-0">
        <!-- Badges -->
        <span class="badge bg-success">Sí</span>  <!-- → bg-green-100 text-green-800 -->
        <span class="badge bg-secondary">No</span>  <!-- → bg-gray-100 text-gray-800 -->
```

#### Paginación Bootstrap
```html
<ul class="pagination pagination-sm">
    <li class="page-item disabled">
        <a class="page-link">«</a>
    </li>
    <li class="page-item active">
        <a class="page-link">1</a>
</ul>
```

#### Inline Styles (Crítico)
```html
style="display:inline;"           <!-- Cambiar por flex -->
style="white-space:nowrap;"       <!-- Cambiar por whitespace-nowrap -->
style="gap: 0.5rem;"              <!-- Cambiar por gap-2 -->
style="color: #6f42c1;"           <!-- Cambiar por text-purple-600 -->
style="background-color: #6f42c1; border-color: #6f42c1; color: #fff;"
```

#### Clases Bootstrap a Reemplazar
- `.container-fluid` (1x)
- `.row` (1x)
- `.col-md-6` (2x)
- `.d-flex`, `.d-inline-flex` (4x)
- `.align-items-center` (2x)
- `.me-2`, `.mb-3` (4x)
- `.form-control` (1x)
- `.form-control-sm` (1x)
- `.btn` (2x)
- `.btn-outline-primary`, `.btn-outline-secondary` (2x)
- `.btn-sm` (2x)
- `.text-end` (1x)
- `.card`, `.card-body`, `.p-0` (3x)
- `.badge`, `.bg-success`, `.bg-secondary` (múltiples)
- `.btn-link`, `.p-0`, `.mx-1` (3x)
- `.text-primary`, `.text-danger` (2x)
- `.pagination`, `.pagination-sm`, `.page-item`, `.page-link` (múltiples)
- `.text-decoration-none`, `.text-nowrap` (2x)
- `.text-dark`, `.h2`, `.fw-bold` (3x)

#### "Función en Desarrollo"
❌ No encontrada

#### Cambios Necesarios
1. Reemplazar grid system completo (`.container-fluid`, `.row`, `.col-md-6`)
2. Convertir todos los `.btn-*` a Tailwind equivalentes
3. Refactorizar paginación Bootstrap a estructura Tailwind
4. Eliminar inline styles con colores Bootstrap
5. Convertir badges a Tailwind
6. Reemplazar `.form-control` por equivalente Tailwind

**Impacto:** Alto - Afecta búsqueda, filtrado, paginación

---

### 3️⃣ **config/grupos.html** - 🟠 ALTO

**Ubicación:** `app/templates/config/grupos.html`

#### Análisis
**Idéntico a `distribuidores.html`** en estructura y problemas de Bootstrap.

#### Clases Bootstrap (Resumen)
- Grid: `.container-fluid`, `.row`, `.col-md-6` (3x)
- Flexbox: `.d-flex`, `.d-inline-flex`, `.align-items-center` (4x)
- Espaciado: `.mb-3`, `.me-2`, `.me-2` (4x)
- Formularios: `.form-control`, `.form-control-sm` (2x)
- Botones: `.btn`, `.btn-outline-primary`, `.btn-sm` (3x)
- Tarjetas: `.card`, `.card-body`, `.shadow-sm` (3x)
- Badges: `.badge`, `.bg-success`, `.bg-secondary` (3x)
- Paginación: `.pagination`, `.page-item`, `.page-link`, etc. (múltiples)
- Utilidades: `.text-end`, `.fw-bold`, `.text-dark`, `.text-decoration-none` (4x)

#### "Función en Desarrollo"
❌ No encontrada

#### Cambios Necesarios
1. Refactorización idéntica a `distribuidores.html`
2. Énfasis en componentes reutilizables para paginación

**Impacto:** Alto - Similar al archivo anterior

---

### 4️⃣ **config/grupo_form.html** - 🟡 MODERADO

**Ubicación:** `app/templates/config/grupo_form.html`

#### Clases Bootstrap Identificadas
```html
<!-- Layout grid -->
<div class="container py-4">                    <!-- → max-w-2xl mx-auto py-4 -->
    <div class="row justify-content-center">    <!-- → flex justify-center -->
        <div class="col-md-7">                  <!-- → w-full md:max-w-2xl -->
            <!-- Card -->
            <div class="card shadow-sm">        <!-- → bg-white rounded-lg shadow -->
                <div class="card-header gradient-bg text-white">  
                    <!-- OK ya tienen custom class -->
                <div class="card-body">         <!-- → p-6 -->
```

#### Formularios
```html
<label for="nombre_grupo" class="form-label">  <!-- → block text-gray-700 font-semibold mb-2 -->
{{ form.nombre_grupo(class="form-control", ...)}}  
<!-- → bg-gray-50 border border-gray-300 rounded px-4 py-2 focus:ring-2 focus:ring-blue-500 -->
```

#### Botones
```html
<button type="submit" class="btn btn-success">    <!-- → bg-green-500 hover:bg-green-600 -->
<a class="btn btn-secondary">Cancelar</a>         <!-- → bg-gray-500 hover:bg-gray-600 -->
```

#### Clases Bootstrap a Reemplazar
- `.container` (1x)
- `.py-4` (1x)
- `.row` (1x)
- `.justify-content-center` (1x)
- `.col-md-7` (1x)
- `.card`, `.shadow-sm` (2x)
- `.card-header` (1x)
- `.card-body` (1x)
- `.form-label` (3x)
- `.form-control` (3x)
- `.mb-3` (3x)
- `.d-flex`, `.justify-content-end`, `.gap-2` (1x)
- `.btn`, `.btn-success`, `.btn-secondary` (2x)
- `.text-danger`, `.small` (1x)

#### "Función en Desarrollo"
❌ No encontrada

#### Cambios Necesarios
1. Convertir `.container` a `max-w-xl mx-auto`
2. Reemplazar grid de Bootstrap por Tailwind `flex` / `max-w-*`
3. Convertir `.form-label` y `.form-control` a clases Tailwind estándar
4. Reemplazar `.btn-success` y `.btn-secondary` por equivalentes Tailwind
5. Cambiar `.text-danger` por `text-red-500`

**Impacto:** Moderado - Formulario de creación/edición

---

### 5️⃣ **auth/login.html** - 🟢 BAJO

**Ubicación:** `app/templates/auth/login.html`

#### Clases Bootstrap Identificadas
```html
<!-- Una única clase Bootstrap encontrada: -->
<span class="input-group-text bg-transparent border-0 p-0" tabindex="-1">
    <i id="toggleIcon" class="fas fa-eye text-gray-500"></i>
</span>
```

#### "Función en Desarrollo"
❌ No encontrada

#### Cambios Necesarios
1. Reemplazar `.input-group-text` con `bg-transparent border-0 p-0` (ya está)
2. Solo requiere eliminar esa clase y mantener los atributos inline

**Impacto:** Bajo - Una sola clase trivial

---

## 📋 ARCHIVOS COMPLETAMENTE LIMPIOS (Tailwind 100%)

✅ **Estos archivos NO requieren cambios de Bootstrap:**

### Formularios
- `config/departamento_form.html` - Usa `.form-input` (clase custom)
- `config/municipio_form.html` - Usa `.form-input` (clase custom)
- `config/role_form.html` - Usa `.form-input` (clase custom)
- `config/usuario_form.html` - Usa `.form-input`, `.form-select`, `.form-checkbox` (custom)

### Listados
- `config/departamentos.html`
- `config/municipios.html`
- `config/roles.html`
- `config/usuarios.html`

### Auth & Errors
- `auth/registro.html`
- `403.html`
- `404.html`
- `500.html`

### Configuración & Historial
- `config/dashboard.html`
- `config/db_status.html`
- `etl/upload.html`
- `etl/preview.html`
- `etl/historial.html`
- `etl/ver_upload.html`

---

## 🎯 PLAN DE REFACTORIZACIÓN PRIORIZADO

### Fase 1 - CRÍTICO (Bloquea el sitio)
1. **base.html**
   - Eliminar CDN Bootstrap
   - Reemplazar modal Bootstrap por estructura Tailwind global
   - Implementar JS para `showGlobalModal()` / `hideGlobalModal()`
   - Ventaja: Una vez hecho, sirve para todo el sitio

### Fase 2 - ALTO (Formularios complejos)
2. **config/distribuidores.html**
   - Reemplazar grid system Bootstrap
   - Convertir formulario de búsqueda
   - Refactorizar paginación

3. **config/grupos.html**
   - Idéntico a distribuidores.html
   - Reutilizar componentes de paginación

4. **config/grupo_form.html**
   - Convertir formulario con tarjeta
   - Reemplazar botones Bootstrap

### Fase 3 - BAJO (Trivial)
5. **auth/login.html**
   - Eliminar `.input-group-text`

---

## 📊 TABLA RESUMEN COMPLETA

| Archivo | Criticidad | Bootstrap | Data-Attrs | Función Dev | Cambios Aprox |
|---------|-----------|-----------|-----------|-------------|---------------|
| base.html | 🔴 Crítico | Modal 5.3 | data-bs-* | SÍ | 20+ |
| distribuidores.html | 🟠 Alto | Grid+Forms | NO | NO | 50+ |
| grupos.html | 🟠 Alto | Grid+Forms | NO | NO | 50+ |
| grupo_form.html | 🟡 Medio | Form | NO | NO | 15+ |
| login.html | 🟢 Bajo | 1 clase | NO | NO | 1 |
| Otros 19 archivos | 🟢 Bajo/Ninguno | NINGUNO | NO | NO | 0 |

---

## 🛠️ REEMPLAZOS PRINCIPALES

### Grid System
```
Bootstrap             →  Tailwind
.container-fluid      →  w-full
.row                  →  grid / flex
.col-md-6             →  md:w-1/2
.align-items-center   →  items-center
.justify-content-*    →  justify-*
```

### Formularios
```
Bootstrap             →  Tailwind
.form-control         →  px-4 py-2 border border-gray-300 rounded focus:ring-2
.form-control-sm      →  (precedente) text-sm
.form-label           →  block text-gray-700 font-semibold mb-2
```

### Botones
```
Bootstrap             →  Tailwind
.btn                  →  px-4 py-2 rounded transition
.btn-primary          →  bg-blue-500 hover:bg-blue-600 text-white
.btn-success          →  bg-green-500 hover:bg-green-600 text-white
.btn-outline-primary  →  border border-blue-500 text-blue-500 hover:bg-blue-50
```

### Utilidades
```
Bootstrap             →  Tailwind
.d-flex               →  flex
.mb-3                 →  mb-3
.me-2                 →  mr-2
.text-dark            →  text-gray-800
.fw-bold              →  font-bold
.text-decoration-none →  no-underline
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### Antes de empezar
- [ ] Hacer backup de archivos actuales
- [ ] Crear rama `feature/bootstrap-to-tailwind`
- [ ] Verificar que Tailwind CSS ya está en `base.html`

### Fase 1: base.html
- [ ] Quitar CDN Bootstrap CSS
- [ ] Quitar JS Bootstrap Bundle
- [ ] Crear estructura de modal global Tailwind
- [ ] Implementar funciones `showGlobalModal()` / `hideGlobalModal()`
- [ ] Actualizar enlace de "Historial" con `onclick="showGlobalModal(...)"`
- [ ] Probar en navegador

### Fase 2: Componentes complejos
- [ ] Refactorizar `distribuidores.html`
- [ ] Refactorizar `grupos.html`
- [ ] Refactorizar `grupo_form.html`
- [ ] Crear componentes reutilizables (paginación, badges, botones)

### Fase 3: Limpieza
- [ ] Refactorizar `login.html`
- [ ] Revisar que no haya inline styles con colores Bootstrap
- [ ] Validar que todos los archivos usen Tailwind consistently

### Testing
- [ ] Revisar responsive en md: breakpoints
- [ ] Probar modales y funcionalidad JS
- [ ] Validar formularios
- [ ] Verificar paginación

---

## 📍 NOTAS IMPORTANTES

1. **ColorPrimary Bootstrap:** #6f42c1 (purple) → Usar `text-purple-600`, `bg-purple-600`
2. **Tailwind ya está:** Yacargado en `base.html`, listo para usar
3. **Custom Classes:** Mantener `.gradient-bg` y `.card-shadow`
4. **Responsive:** Bootstrap usa `.md:`, Tailwind también
5. **Modal Global:** Hacer UN solo modal reutilizable que maneje todos los "función en desarrollo" mensajes

---

**Documento generado:** 2026-03-09  
**Estado:** Análisis Completo ✓
