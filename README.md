# Graficador - Sistema de Emparejamiento para Torneos de Taekwondo

Sistema de emparejamiento automático para torneos de Taekwondo que procesa archivos Excel con competidores y genera gráficas (brackets) optimizadas según reglas de compatibilidad.

## Requisitos Previos

- **Python**: Versión 3.11 o superior
- **Node.js**: Versión 18 o superior
- **npm**: Incluido con Node.js

## Estructura del Proyecto

```
Graficador/
├── backend/                 # API REST con FastAPI (Python)
│   ├── app/
│   │   ├── main.py          # Punto de entrada de la API
│   │   ├── models.py        # Modelos Pydantic
│   │   ├── parser.py        # Parser de archivos Excel
│   │   ├── algorithm.py     # Algoritmo de emparejamiento
│   │   ├── recommendations.py  # Sistema de recomendaciones
│   │   └── export_pdf.py    # Exportación a PDF
│   ├── tests/               # Pruebas automatizadas
│   ├── requirements.txt     # Dependencias Python
│   └── run.py               # Script de ejecución
├── frontend/                # Interfaz web con Astro + React
│   ├── src/
│   │   ├── pages/
│   │   │   └── index.astro  # Página principal
│   │   └── components/
│   │       ├── App.jsx          # Componente principal React
│   │       ├── UploadForm.jsx   # Formulario de subida
│   │       ├── ResultsPanel.jsx  # Panel de resultados
│   │       └── UnpairedManager.jsx  # Gestión de competidores sin pareja
│   ├── package.json         # Dependencias npm
│   └── astro.config.mjs    # Configuración de Astro
├── template/
│   ├── competidores_ejemplo.xlsx  # Archivo de ejemplo
│   └── fixtures/           # Archivos de prueba
├── espec.md                # Especificaciones técnicas
└── README.md               # Este archivo
```

---

## Instalación

### 1. Clonar o descargar el proyecto

```bash
git clone <repositorio> Graficador
cd Graficador
```

### 2. Configurar el Backend (Python)

#### a. Crear un entorno virtual (recomendado)

**Windows:**
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
```

#### b. Instalar las dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- `fastapi` - Framework web
- `uvicorn` - Servidor ASGI
- `numpy` - Cálculos numéricos
- `pandas` - Manipulación de datos
- `openpyxl` - Lectura de archivos Excel
- `pydantic` - Validación de datos
- `xlsxwriter` - Escritura de archivos Excel
- `reportlab` - Generación de PDFs

#### c. Verificar la instalación

```bash
python -c "import fastapi; print(f'FastAPI {fastapi.__version__} instalado correctamente')"
```

### 3. Configurar el Frontend (Node.js)

#### a. Navegar al directorio del frontend

```bash
cd frontend
```

#### b. Instalar las dependencias

```bash
npm install
```

Esto instalará:
- `astro` - Framework web moderno
- `react` - Biblioteca de UI
- `@astrojs/react` - Integración de React en Astro
- `xlsx` - Manipulación de archivos Excel en el cliente

#### c. Verificar la instalación

```bash
npm list astro react
```

---

## Ejecución del Proyecto

### Opción 1: Ejecutar ambos servicios manualmente

#### Iniciar el Backend

```bash
# En una terminal, desde la raíz del proyecto
cd backend
python run.py
```

El backend estará disponible en: **http://localhost:8000**

Puedes verificar que está funcionando:
- API Docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

#### Iniciar el Frontend

```bash
# En otra terminal, desde la raíz del proyecto
cd frontend
npm run dev
```

La aplicación estará disponible en: **http://localhost:4321**

### Opción 2: Ejecutar en paralelo (PowerShell)

```powershell
# Iniciar ambos servicios en背景
Start-Process powershell -ArgumentList "-Command", "cd backend; python run.py"
Start-Process powershell -ArgumentList "-Command", "cd frontend; npm run dev"
```

---

## Uso de la Aplicación

### 1. Acceder a la interfaz web

Abre tu navegador y visita: **http://localhost:4321**

### 2. Subir archivo Excel

1. En la página principal, haz clic en "Seleccionar archivo" o arrastra un archivo Excel
2. Selecciona el archivo `template/competidores_ejemplo.xlsx` (o tu propio archivo)
3. Haz clic en "Procesar"

### 3. Ver resultados

La aplicación mostrará:
- **Estadísticas globales**: Total de competidores, gráficas generadas, promedio de tamaño
- **Estadísticas por bloque**: Adultos, Infantil (por color de cinta), Pre-Taekwondo
- **Gráficas generadas**: Lista de brackets con competidores, puntajes de compatibilidad
- **Competidores sin pareja**: Lista de competidores que no pudieron ser emparejados

---

## Formato del Archivo Excel

El archivo debe contener **una hoja por bloque de competencia**.

### Hojas soportadas

| Hoja | Descripción |
|------|-------------|
| Adultos Grupo 1 | Adultos grupo 1 |
| Adultos Grupo 2 | Adultos grupo 2 |
| Infantil Azul | Infantil cinta azul |
| Infantil Verde | Infantil cinta verde |
| Infantil Amarilla | Infantil cinta amarilla |
| Infantil Blanca | Infantil cinta blanca |
| Infantil Marrón | Infantil cinta marrón |
| Infantil Roja | Infantil cinta roja |
| Infantil Negra | Infantil cinta negra |
| Pre-Taekwondo | Pre-Taekwondo |

### Columnas requeridas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| No | Integer (opcional) | Número de fila (ignorado) |
| Nombre | String | Nombre(s) del competidor |
| Apellido | String | Apellido(s) del competidor |
| Edad | Integer | Edad en años |
| H/M | String | H = Masculino, M = Femenino |
| Grado | String | Cinta (ej: "3 KUP", "Blanca", "1er Dan") |
| Peso | Float | Peso en kg (ej: 24.75) |
| Estatura | Float | Estatura en cm (ej: 122.00) |
| Modalidad | String | "Doble" o "Sencillo" |
| Doyang | String | Escuela/Club |

### Ejemplo de datos

| No | Nombre | Apellido | Edad | H/M | Grado | Peso | Estatura | Modalidad | Doyang |
|----|--------|----------|------|-----|-------|------|----------|-----------|--------|
| 1 | JESUS BALDEMAR | LÓPEZ CAMACHO | 7 | H | 3 KUP | 24.75 | 122 | Doble | MDK FLORIDO |
| 2 | DAMIAN ALEJANDRO | ZAMUDIO BOGARÍN | 7 | H | 3 KUP | 30.00 | 133 | Doble | MDK CASA BLANCA |

---

## API REST

### Endpoints disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información de la API |
| GET | `/health` | Verificar estado del servidor |
| POST | `/upload` | Subir archivo Excel y procesar |
| GET | `/tests` | Ejecutar pruebas con fixtures |
| GET | `/tests/random` | Ejecutar pruebas aleatorias |
| POST | `/api/recommendations/generate` | Generar recomendaciones |
| POST | `/api/recommendations/apply` | Aplicar recomendación |
| POST | `/api/manual_assign` | Asignación manual |
| POST | `/api/undo` | Deshacer última acción |
| POST | `/api/finalize` | Finalizar emparejamiento |
| GET | `/api/export/pdf` | Exportar a PDF |

### Ejemplos con curl

**Health check:**
```bash
curl http://localhost:8000/health
```

**Subir archivo:**
```bash
curl -X POST -F "file=@template/competidores_ejemplo.xlsx" http://localhost:8000/upload
```

**Ver documento Swagger:**
Abre http://localhost:8000/docs en tu navegador para ver la documentación interactiva.

---

## Algoritmo de Emparejamiento

El sistema utiliza un algoritmo de 3 etapas:

### Etapa 1: Filtros obligatorios
- Filtrar por sexo (H/M)
- Filtrar por cinta (Blanca, Amarilla, Verde, Azul, Marrón, Roja, Negra)

### Etapa 2: Emparejamiento por compatibilidad
Calcula un puntaje de compatibilidad para cada par:
- **Peso (50%)**: Diferencia de peso ≤ 5kg = puntaje máximo
- **Estatura (20%)**: Diferencia de estatura ≤ 10cm = puntaje máximo
- **Edad (20%)**: Diferencia de edad ≤ 1 año = puntaje máximo
- **Doyang (10%)**: Bonus si son de escuelas diferentes

### Etapa 3: Emparejamiento relajado
- **Ronda 1**: Permite diferencia de edad ±2 años
- **Ronda 2**: Limites relajados: ±6kg, ±12cm, ±2-3 años

### Numeración

- **Número de competidor**: Prefijo del bloque + secuencia (ej: MR 1, AD 15)
- **Número de gráfica**: Secuencial global
- **Número de área**: Ciclos de 1 a 12

---

## Desarrollo

### Ejecutar pruebas

```bash
cd backend
pytest tests/
```

### Ejecutar pruebas con coverage

```bash
cd backend
pytest --cov=app tests/
```

### Construir el frontend para producción

```bash
cd frontend
npm run build
```

Los archivos generados estarán en `frontend/dist/`

### Previsualizar build de producción

```bash
cd frontend
npm run preview
```

---

## Solución de Problemas

### Error: "Module not found" al importar dependencias

Asegúrate de haber activado el entorno virtual:
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

Luego reinstala las dependencias:
```bash
pip install -r requirements.txt
```

### Error: "Port 8000 is already in use"

Cambia el puerto en `backend/run.py`:
```python
uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=False)
```

### Error: "Port 4321 is already in use"

El frontend Astro intentará usar otro puerto automáticamente. Accede al puerto que se muestre en la terminal.

### Problemas con Excel en Windows

Si tienes problemas con la lectura de archivos Excel, asegúrate de tener Microsoft Visual C++ Redistributable instalado.

---

## Tecnologías Utilizadas

### Backend
- **Python 3.11+** - Lenguaje de programación
- **FastAPI** - Framework web moderno y rápido
- **Uvicorn** - Servidor ASGI de alto rendimiento
- **Pandas** - Manipulación y análisis de datos
- **NumPy** - Cálculos numéricos
- **OpenPyXL** - Lectura/escritura de archivos Excel

### Frontend
- **Astro** - Framework web moderno
- **React** - Biblioteca de componentes
- **XLSX** - Manipulación de Excel en el cliente
- **TypeScript** - Tipado estático opcional

---

## Licencia

MIT License

---

## Soporte

Para reportar errores o sugerir mejoras, por favor crea un issue en el repositorio del proyecto.
