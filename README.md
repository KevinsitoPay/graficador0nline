# Graficador - Taekwondo Bracket System

Sistema de emparejamiento automático para torneos de Taekwondo.

## Requisitos

- Python 3.11+
- Node.js 18+

## Instalación

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Uso

### 1. Iniciar el backend

```bash
cd backend
python run.py
```

El backend estará disponible en http://localhost:8000

### 2. Iniciar el frontend

```bash
cd frontend
npm run dev
```

La aplicación estará disponible en http://localhost:4321

### 3. Subir archivo Excel

1. Abre http://localhost:4321
2. Selecciona el archivo `template/competidores_ejemplo.xlsx`
3. Click en "Procesar"

## Archivo Excel

El archivo debe contener una hoja por bloque de competencia:

- Adultos Grupo 1
- Adultos Grupo 2
- Infantil Azul
- Infantil Verde
- Infantil Amarilla
- Infantil Blanca
- Infantil Marrón
- Infantil Roja
- Infantil Negra
- Pre-Taekwondo

Columnas requeridas:
- No (opcional)
- Nombre
- Apellido
- Edad
- H/M (H=Masculino, F=Femenino)
- Grado (cinta)
- Peso (kg)
- Estatura (cm)
- Modalidad (Doble/Sencillo)
- Doyang (escuela)

## API

### Endpoint: POST /upload

Sube un archivo Excel y recibe las gráficas generadas.

```bash
curl -X POST -F "file=@competidores_ejemplo.xlsx" http://localhost:8000/upload
```

### Endpoint: GET /health

Verifica que el servidor esté funcionando.

```bash
curl http://localhost:8000/health
```

## Desarrollo

### Estructura del proyecto

```
graficador/
├── backend/
│   ├── app/
│   │   ├── main.py      # FastAPI app
│   │   ├── models.py   # Pydantic models
│   │   ├── parser.py  # Excel parser
│   │   └── algorithm.py # Pairing algorithm
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── index.astro
│   │   └── components/
│   │       ├── UploadForm.jsx
│   │       └── ResultsPanel.jsx
│   └── package.json
├── template/
│   └── competidores_ejemplo.xlsx
└── README.md
```

### Algoritmo

El sistema usa un algoritmo de 3 etapas:

1. **Etapa 1**: Filtrar por sexo y cinta
2. **Etapa 2**: Emparejamiento por compatibilidad
3. **Etapa 3**: Emparejamiento relajado (por edad/límites)

Ver `especs.md` para detalles completos.