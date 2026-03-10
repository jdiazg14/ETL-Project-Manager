# Matriz Rápida - Bootstrap vs Tailwind

## 📊 Estado de Refactorización por Archivo

```
LEGENDA:
🔴 = CRÍTICO (Refactorización urgente)
🟠 = ALTO (Refactorización necesaria)
🟡 = MODERADO (Cambios menores)
🟢 = BAJO O NINGUNO (Sin cambios o triviales)
```

### Estructura Visual del Proyecto

```
app/templates/
├── base.html                           🔴 CRÍTICO
│   ├─ Modal Bootstrap activo
│   ├─ Data-attributes: data-bs-toggle, data-bs-target, data-bs-dismiss
│   ├─ CDN Bootstrap 5.3.2 activo
│   └─ "Función en desarrollo" ENCONTRADA
│
├── auth/
│   ├── login.html                      🟢 BAJO (1 clase)
│   └── registro.html                   🟢 LIMPIO
│
├── config/
│   ├── dashboard.html                  🟢 LIMPIO
│   ├── db_status.html                  🟢 LIMPIO
│   │
│   ├── departamentos.html               🟢 LIMPIO
│   ├── departamento_form.html           🟢 LIMPIO
│   │
│   ├── distribuidores.html              🟠 ALTO (50+ cambios)
│   │   ├─ Grid system completo
│   │   ├─ Paginación Bootstrap
│   │   ├─ Badges
│   │   └─ Búsqueda/filtrado
│   ├── distribuidor_form.html           🟢 LIMPIO
│   │
│   ├── grupos.html                      🟠 ALTO (50+ cambios) [IDÉNTICO A distribuidores]
│   ├── grupo_form.html                  🟡 MODERADO (15+ cambios)
│   │   ├─ Card bootstrap
│   │   ├─ Form controls
│   │   └─ Botones
│   │
│   ├── municipios.html                  🟢 LIMPIO
│   ├── municipio_form.html              🟢 LIMPIO
│   │
│   ├── roles.html                       🟢 LIMPIO
│   ├── role_form.html                   🟢 LIMPIO
│   │
│   ├── usuarios.html                    🟢 LIMPIO
│   └── usuario_form.html                🟢 LIMPIO
│
├── etl/
│   ├── upload.html                      🟢 LIMPIO
│   ├── preview.html                     🟢 LIMPIO
│   ├── historial.html                   🟢 LIMPIO
│   └── ver_upload.html                  🟢 LIMPIO
│
├── 403.html                             🟢 LIMPIO
├── 404.html                             🟢 LIMPIO
└── 500.html                             🟢 LIMPIO
```

---

## 📈 Estadísticas

| Métrica | Cantidad |
|---------|----------|
| Archivos Totales | 24 |
| Con Bootstrap Activo | 5 (20.8%) |
| 100% Tailwind | 19 (79.2%) |
| **Clases Bootstrap encontradas** | **200+** |
| **Data-attributes Bootstrap** | **5+** |
| **"Función en desarrollo"** | **1** |

---

## 🎯 PRIORIDADES DE REFACTORIZACIÓN

### TIER 1 - CRÍTICO (Bloquea el sitio)
```
✗ base.html  
  │
  ├─ Quitar CDN Bootstrap 5.3.2
  ├─ Eliminar JS Bundle Bootstrap
  ├─ Reemplazar Modal Bootstrap
  ├─ Cambiar data-bs-* atributos
  ├─ Implementar showGlobalModal() / hideGlobalModal()
  └─ Manejo del mensaje "función en desarrollo"
```

**Dependencia:** Todo el sitio depende de base.html

### TIER 2 - ALTO (Formularios complejos)
```
✗ distribuidores.html (50+ cambios)
  ├─ Grid: .container-fluid → w-full
  ├─ Columnas: .col-md-6 → md:w-1/2
  ├─ Botones: .btn-outline-* → border-based
  ├─ Badges: .badge → bg-*/text-*
  ├─ Paginación: .pagination → custom Tailwind
  └─ Inline styles con colores (#6f42c1)

✗ grupos.html (50+ cambios)
  └─ IDÉNTICO a distribuidores.html → Reutilizar soluciones

✗ grupo_form.html (15+ cambios)
  ├─ Card: .card → bg-white rounded-lg
  ├─ Form: .form-control → border px-4 py-2
  └─ Botones: .btn-* → bg-*/hover:bg-*
```

**Dependencia:** Gestión de maestros, búsqueda, filtrado

### TIER 3 - BAJO (Trivial)
```
✓ login.html (1 clase)
  └─ .input-group-text → Hacer inline style
```

**Esfuerzo:** Mínimo

---

## 📋 CLASES BOOTSTRAP POR CATEGORÍA

### Layout & Grid
```html
<!-- Bootstrap -->
.container-fluid, .container
.row
.col-md-6 (y variantes)

<!-- Tailwind Equivalente -->
w-full, max-w-6xl mx-auto
grid grid-cols-* / flex
md:w-1/2 (y variantes)
```

### Flexbox & Spacing
```html
<!-- Bootstrap -->
.d-flex, .d-inline-flex
.align-items-center, .justify-content-center
.mb-3, .me-2, .py-4

<!-- Tailwind Equivalente -->
flex, inline-flex
items-center, justify-center
mb-3, mr-2, py-4
```

### Formularios
```html
<!-- Bootstrap -->
.form-label, .form-control, .form-control-sm
.form-select, .form-check

<!-- Tailwind Equivalente -->
block text-gray-700 font-semibold mb-2
bg-gray-50 border border-gray-300 rounded px-4 py-2
(precedente) text-sm
w-full (inherita de padre)
w-4 h-4 (check boxes)
```

### Botones
```html
<!-- Bootstrap -->
.btn, .btn-primary, .btn-success, .btn-secondary
.btn-outline-primary
.btn-sm, .btn-link

<!-- Tailwind Equivalente -->
px-4 py-2 rounded transition bg-blue-500 hover:bg-blue-600 text-white
border border-blue-500 text-blue-500 hover:bg-blue-50
text-sm
flex items-center justify-center
p-0 background-transparent
```

### Componentes
```html
<!-- Bootstrap -->
.card, .card-header, .card-body, .card-footer
.badge, .badge-secondary, .badge-success
.pagination, .page-item, .page-link
.modal, .modal-dialog, .modal-content, .btn-close

<!-- Tailwind Equivalente -->
bg-white rounded-lg shadow, px-6 py-4, ...
bg-gray-100 text-gray-800 px-3 py-1 rounded-full
custom pagination en Tailwind
fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center
```

### Utilidades
```html
<!-- Bootstrap -->
.text-dark, .text-white, .text-danger, .fw-bold
.text-decoration-none, .text-nowrap
.d-none, .d-block, .d-flex

<!-- Tailwind Equivalente -->
text-gray-800, text-white, text-red-600, font-bold
no-underline, whitespace-nowrap
hidden, block, flex
```

### Data-Attributes
```html
<!-- Bootstrap Específico - NO TIENE EQUIVALENTE EN TAILWIND -->
data-bs-toggle="modal"
data-bs-target="#modalId"
data-bs-dismiss="modal"
tabindex="-1"
aria-hidden="true"
aria-labelledby="modalTitle"

<!-- SOLUCIÓN TAILWIND -->
onclick="showGlobalModal()"
id="modalElement"
class="hidden" (toggle con JS)
aria-hidden="true" (mantener para accesibilidad)
```

---

## 🔧 CAMBIOS ESPECÍFICOS POR ARCHIVO

### base.html - Cambios Exactos Necesarios

**Línea 9-10:** Quitar CDN Bootstrap
```html
<!-- QUITAR -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

<!-- MANTENER -->
<script src="https://cdn.tailwindcss.com"></script>
```

**Línea 122:** Quitar JS Bootstrap
```html
<!-- QUITAR -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
```

**Línea 113-122:** Reemplazar Modal Completo
```html
<!-- QUITAR TODO ESTO -->
<div class="modal fade" id="historialModal" tabindex="-1" ...>
    <div class="modal-dialog modal-sm modal-dialog-centered">
        <div class="modal-content">
            ...
        </div>
    </div>
</div>

<!-- AGREGAR ESTO (ver plan en refactor-bootstrap-to-tailwind-plan.md) -->
<div id="globalModal" class="hidden fixed inset-0 bg-black...">
```

**Antes del `</body>`:** Agregar funciones JS
```html
<script>
function showGlobalModal(title, message) {
  document.getElementById('globalModalTitle').textContent = title;
  document.getElementById('globalModalBody').innerHTML = message;
  document.getElementById('globalModal').classList.remove('hidden');
}

function hideGlobalModal() {
  document.getElementById('globalModal').classList.add('hidden');
}
</script>
```

**Línea 42:** Cambiar enlace de Historial
```html
<!-- DE ESTO -->
<a href="#" data-bs-toggle="modal" data-bs-target="#historialModal">
    <i class="fas fa-history"></i> Historial
</a>

<!-- A ESTO -->
<a href="#" onclick="showGlobalModal('Historial', 'Esta función se encuentra actualmente en desarrollo.')">
    <i class="fas fa-history"></i> Historial
</a>
```

---

### distribuidores.html & grupos.html - Sample Changes

**Línea 1:** Grid System
```html
<!-- DE -->
<div class="container-fluid py-4">
    <div style="width: 95%; margin: 0 auto;">
        <div class="row align-items-center mb-3">
            <div class="col-md-6 d-flex align-items-center" style="gap: 0.5rem;">

<!-- A -->
<div class="w-full py-4">
    <div class="w-11/12 mx-auto">
        <div class="flex items-center mb-3">
            <div class="md:w-1/2 flex items-center gap-2">
```

**Formulario de Búsqueda:**
```html
<!-- DE -->
<form class="d-inline-flex align-items-center" method="get" action="">
    <input type="text" class="form-control form-control-sm me-2">
    <button class="btn btn-outline-primary btn-sm me-2">

<!-- A -->
<form class="inline-flex items-center gap-2" method="get" action="">
    <input type="text" class="bg-gray-50 border border-gray-300 rounded px-3 py-1 text-sm">
    <button class="border border-purple-600 text-purple-600 px-3 py-1 text-sm hover:bg-purple-50 rounded">
```

**Paginación:**
```html
<!-- DE -->
<ul class="pagination pagination-sm">
    <li class="page-item {% if not pagination.has_prev %}disabled{% endif %}">
        <a class="page-link" style="color: #6f42c1;">«</a>
    </li>

<!-- A (Componente Tailwind) -->
<nav class="mt-3 flex justify-center gap-1">
    <button class="{% if not pagination.has_prev %}opacity-50 cursor-not-allowed{% endif %} px-3 py-1 border rounded text-purple-600 hover:bg-purple-50">«</button>
```

---

## ✅ VALIDACIÓN DESPUÉS DE CAMBIOS

Para cada archivo refactorizado:

- [ ] **Responsive Check** - Probar en md: breakpoints (tablet)
- [ ] **Formulariosinciona** - Búsqueda, filtrado, validación
- [ ] **Paginación Funciona** - Navegar entre páginas
- [ ] **Badges Visibles** - Estados correcto (Sí/No, Activo/Inactivo)
- [ ] **Botones Accesibles** - Click, colores, hover
- [ ] **Modales Aparecen** - GlobalModal si aplica
- [ ] **Alineación Correcta** - Elementos centrados/alienados
- [ ] **Colores Consistency** - Usar paleta Tailwind
- [ ] **Sin Warnings Console** - Revisar dev tools
- [ ] **No hay estilos en conflicto** - Tailwind vs Bootstrap residuales

---

**Última actualización:** 2026-03-09  
**Responsable del análisis:** GitHub Copilot  
**Status:** ✅ Análisis Completado
