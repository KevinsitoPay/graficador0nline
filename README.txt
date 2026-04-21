================================================================================
                    GRAFICADOR - SISTEMA DE EMPAEJAMINETO
                    PARA TORNEOS DE TAEKWONDO
================================================================================

DESCRIPCION GENERAL
================================================================================

Graficador es un sistema automatizado para generar graficas (brackets) de
competencia en torneos de Taekwondo. El sistema procesa un archivo Excel con
la lista de competidores y aplica un algoritmo inteligente de emparejamiento
que tiene en cuenta factores como:

- Sexo del competidor (Masculino/Femenino)
- Cinturon (Grado tecnico: Blanca, Amarilla, Verde, Azul, Marron, Roja, Negra)
- Edad
- Peso
- Estatura
- Escuela/Club (Doyang)
- Modalidad (Doble o Sencillo)

El objetivo es crear emparejamientos justos y competitivos donde los
competidores tengan caracteristicas similares, garantizando combates
equilibrados y seguros.


REQUISITOS DEL SISTEMA
================================================================================

Para ejecutar este proyecto necesitas instalar los siguientes programas
en tu computadora:

1. PYTHON 3.11 O SUPERIOR
   ------------------------
   Python es el lenguaje de programacion utilizado para el backend (servidor).

   Como verificar si ya lo tienes:
   - Abre una terminal (CMD en Windows, Terminal en Mac/Linux)
   - Escribe: python --version
   - Si te muestra un numero como "3.11.7" o superior, ya lo tienes
   - Si no lo tienes, descargalo desde: https://www.python.org/downloads/
   - IMPORTANTE: Durante la instalacion, marca la opcion "Add Python to PATH"

2. NODE.JS 18 O SUPERIOR
   ----------------------
   Node.js es un entorno de ejecucion para JavaScript utilizado en el frontend.

   Como verificar si ya lo tienes:
   - Abre una terminal y escribe: node --version
   - Si te muestra un numero como "18.19.0" o superior, ya lo tienes
   - Si no lo tienes, descargalo desde: https://nodejs.org/
   - Se recomienda la version LTS (Long Term Support)

3. NPM (incluido con Node.js)
   ---------------------------
   NPM es el gestor de paquetes de Node.js y se instala automaticamente con el.

   Como verificar:
   - Escribe: npm --version
   - Deberia mostrar un numero de version


ESTRUCTURA DE CARPETAS
================================================================================

El proyecto esta organizado de la siguiente manera:

Graficador/
|
|-- backend/                    (Carpeta del servidor/backend)
|   |-- app/
|   |   |-- main.py            (Archivo principal de la API)
|   |   |-- models.py          (Modelos de datos)
|   |   |-- parser.py          (Lee archivos Excel)
|   |   |-- algorithm.py       (Logica de emparejamiento)
|   |   |-- recommendations.py (Sugerencias para competidores sin pareja)
|   |   |-- export_pdf.py      (Genera archivos PDF)
|   |-- tests/                 (Pruebas automatizadas)
|   |-- requirements.txt      (Lista de dependencias Python)
|   |-- run.py                 (Script para iniciar el servidor)
|
|-- frontend/                   (Carpeta de la interfaz web)
|   |-- src/
|   |   |-- pages/
|   |   |   |-- index.astro   (Pagina principal)
|   |   |-- components/
|   |   |   |-- App.jsx            (Componente principal)
|   |   |   |-- UploadForm.jsx     (Formulario de subida de archivos)
|   |   |   |-- ResultsPanel.jsx   (Muestra los resultados)
|   |   |   |-- UnpairedManager.jsx (Gestiona competidores sin pareja)
|   |-- package.json           (Lista de dependencias JavaScript)
|   |-- astro.config.mjs       (Configuracion de Astro)
|
|-- template/
|   |-- competidores_ejemplo.xlsx (Archivo Excel de ejemplo)
|   |-- fixtures/              (Archivos para pruebas)
|
|-- espec.md                    (Especificaciones tecnicas detalladas)
|-- README.txt                  (Este archivo)


INSTALACION - BACKEND (PYTHON)
================================================================================

El backend es la parte del sistema que procesa los datos, ejecuta el algoritmo
de emparejamiento y proporciona los resultados. Esta hecho en Python.

PASO 1: Abrir una terminal
---------------------------
- En Windows: Busca "CMD" o "PowerShell" en el menu inicio
- En Mac: Busca "Terminal" en Launchpad o Spotlight
- En Linux: Abre tu terminal favorita

PASO 2: Navegar a la carpeta del backend
-----------------------------------------
Escribe el siguiente comando (ajusta la ruta segun donde guardaste el proyecto):

    cd C:\Users\USUARIO\Desktop\sitiosLocales\Graficador\backend

(Si estas en Mac/Linux usa barras normales: ~/Desktop/sitiosLocales/Graficador/backend)

PASO 3: Crear un entorno virtual
--------------------------------
Un entorno virtual es como un espacio aislado donde se instalan las librerias
del proyecto sin afectar otras instalaciones de Python.

    python -m venv venv

Esto creara una carpeta llamada "venv" dentro de backend/

PASO 4: Activar el entorno virtual
-----------------------------------
- En Windows (CMD):
      venv\Scripts\activate

- En Windows (PowerShell):
      .\venv\Scripts\Activate

- En Mac/Linux:
      source venv/bin/activate

Cuando este activo, veras (venv) al inicio de tu linea de comandos.

PASO 5: Instalar las dependencias
------------------------------------
Ahora vamos a instalar todas las librerias necesarias que el proyecto necesita:

    pip install -r requirements.txt

Esto leera el archivo requirements.txt e instalara cada paquete listedo alli.
El proceso puede tomar unos minutos.

Paquetes que se instalaran:
- fastapi: Framework web moderno para crear APIs
- uvicorn: Servidor para ejecutar la aplicacion
- numpy: Libreria para calculos matematicos
- pandas: Libreria para manejar datos en tablas
- openpyxl: Permite leer archivos Excel (.xlsx)
- pydantic: Validacion de datos
- xlsxwriter: Permite escribir archivos Excel
- reportlab: Generacion de documentos PDF

PASO 6: Verificar la instalacion
---------------------------------
Para asegurarte que todo esta bien, puedes probar:

    python -c "import fastapi; print('FastAPI instalado correctamente')"

Si ves el mensaje, todo esta listo!


INSTALACION - FRONTEND (NODE.JS)
================================================================================

El frontend es la parte visual de la aplicacion, la pagina web que ves en
tu navegador. Esta hecho con Astro y React.

PASO 1: Abrir una terminal nueva
--------------------------------
Es mejor tener una terminal separada para el frontend.

PASO 2: Navegar a la carpeta del frontend
-----------------------------------------

    cd C:\Users\USUARIO\Desktop\sitiosLocales\Graficador\frontend

PASO 3: Instalar las dependencias
----------------------------------
    npm install

Este comando leera el archivo package.json e instalara todas las librerias
necesarias para el frontend. Tardara un poco mas la primera vez.

Paquetes que se instalaran:
- astro: Framework web moderno
- react: Biblioteca para crear interfaces de usuario
- @astrojs/react: Integracion de React con Astro
- xlsx: Libreria para leer archivos Excel en el navegador


EJECUTAR EL PROYECTO
================================================================================

Ahora que todo esta instalado, vamos a ejecutar la aplicacion.

IMPORTANTE: Necesitas ejecutar el backend Y el frontend al mismo tiempo.
Para eso, necesitas dos terminales abiertas.

TERMINAL 1 - INICIAR EL BACKEND
-------------------------------

1. Asegurate de estar en la carpeta backend:
       cd C:\Users\USUARIO\Desktop\sitiosLocales\Graficador\backend

2. Activa el entorno virtual:
       venv\Scripts\activate   (Windows)
       source venv/bin/activate   (Mac/Linux)

3. Inicia el servidor:
       python run.py

Deberias ver mensajes indicando que el servidor esta arrancando.
Cuando termine de iniciar, veras algo como:

       Uvicorn running on http://0.0.0.0:8000

Esto significa que el backend esta funcionando en el puerto 8000.

TERMINAL 2 - INICIAR EL FRONTEND
--------------------------------

1. Abre una nueva terminal
2. Navega a la carpeta frontend:
       cd C:\Users\USUARIO\Desktop\sitiosLocales\Graficador\frontend

3. Inicia el servidor de desarrollo:
       npm run dev

Despues de unos segundos, veras un mensaje como:

       🚀  astro  v4.x.x  ready in 534 ms

       ┃ Local    http://localhost:4321/
       ┃ Network  use --host to expose

Esto significa que el frontend esta funcionando en el puerto 4321.


USAR LA APLICACION
================================================================================

Ahora puedes abrir tu navegador web (Chrome, Firefox, Edge, etc.) y escribir:

    http://localhost:4321

Deberia aparecer la pagina principal del Graficador.

PASO 1: Subir un archivo Excel
-------------------------------

1. En la pagina principal, veras un boton o area para subir archivos
2. Haz clic en "Seleccionar archivo" o arrastra el archivo
3. Navega a la carpeta template del proyecto
4. Selecciona el archivo "competidores_ejemplo.xlsx"
5. Haz clic en "Procesar" o boton similar

PASO 2: Esperar el procesamiento
--------------------------------
El sistema procesara el archivo. Esto puede tomar desde unos segundos
hasta un minuto, dependiendo de la cantidad de competidores.

Veras una barra de progreso o indicador de carga.

PASO 3: Ver los resultados
--------------------------
Una vez procesado, veras:

a) ESTADISTICAS GLOBALES:
   - Total de competidores procesados
   - Total de graficas generadas
   - Promedio de competidores por grafica

b) ESTADISTICAS POR BLOQUE:
   - Adultos Grupo 1
   - Adultos Grupo 2
   - Infantil Azul, Verde, Amarilla, Blanca, Marron, Roja, Negra
   - Pre-Taekwondo

c) GRAFICAS GENERADAS:
   - Lista de cada grafica con sus competidores
   - Numero de competidores en cada grafica
   - Puntaje de compatibilidad (que tan bien emparejados estan)

d) COMPETIDORES SIN PAREJA:
   - Lista de competidores que no pudieron ser emparejados
   - Razon por la que no tienen pareja


FORMATO DEL ARCHIVO EXCEL
================================================================================

Para que el sistema funcione correctamente, el archivo Excel debe seguir
un formato especifico.

ESTRUCTURA DEL ARCHIVO
-----------------------

El archivo debe tener una HOJA por cada bloque de competencia.

Hojas validas (el nombre debe coincidir exactamente):
- Adultos Grupo 1
- Adultos Grupo 2
- Infantil Azul
- Infantil Verde
- Infantil Amarilla
- Infantil Blanca
- Infantil Marron
- Infantil Roja
- Infantil Negra
- Pre-Taekwondo

COLUMNAS REQUERIDAS
-------------------

Cada hoja debe tener las siguientes columnas (en este orden o con estos nombres):

| Columna   | Tipo    | Descripcion                                    |
|-----------|---------|------------------------------------------------|
| No        | Numero  | (Opcional) Numero de fila                     |
| Nombre    | Texto   | Nombre(s) del competidor                      |
| Apellido  | Texto   | Apellido(s) del competidor                    |
| Edad      | Numero  | Edad en anos (ej: 7, 12, 18)                  |
| H/M       | Texto   | H = Hombre (Masculino), M = Mujer (Femenino) |
| Grado     | Texto   | Cinturon (ej: "3 KUP", "Blanca", "1er Dan")  |
| Peso      | Numero  | Peso en kilogramos (ej: 24.75)               |
| Estatura  | Numero  | Estatura en centimetros (ej: 122.00)          |
| Modalidad | Texto   | "Doble" o "Sencillo"                          |
| Doyang    | Texto   | Nombre de la escuela/club                      |

EJEMPLO DE DATOS
----------------

| No | Nombre           | Apellido          | Edad | H/M | Grado   | Peso   | Estatura | Modalidad | Doyang           |
|----|------------------|-------------------|------|-----|---------|--------|----------|-----------|------------------|
| 1  | JESUS BALDEMAR   | LOPEZ CAMACHO     | 7    | H   | 3 KUP   | 24.75  | 122      | Doble     | MDK FLORIDO      |
| 2  | DAMIAN ALEJANDRO | ZAMUDIO BOGARIN   | 7    | H   | 3 KUP   | 30.00  | 133      | Doble     | MDK CASA BLANCA |
| 3  | SOFIA            | MARTINEZ          | 9    | M   | 2 KUP   | 28.50  | 130      | Sencillo  | MDK EL DORADO    |

NOTAS IMPORTANTES:
- El peso y estatura pueden usar coma o punto decimal (24,75 o 24.75)
- La columna "No" es opcional y sera ignorada por el sistema
- Los grados se normalizan automaticamente (3 KUP = Marron, Blanca = Blanca, etc.)
- Si una hoja no tiene competidores, sera ignorada


ALGORITMO DE EMPAEJAMINETO
================================================================================

El sistema utiliza un algoritmo de tres etapas para crear los emparejamientos:

ETAPA 1: FILTROS OBLIGATORIOS
------------------------------

Antes de emparejar, el sistema filtra a los competidores:

1. Por sexo: Los hombres solo compiten con hombres, mujeres con mujeres
2. Por cinturon: Solo se emparejan competidores del mismo grado/cinturon

Si un competidor no tiene ningun otro del mismo sexo y cinturon, sera
marcado como "sin rival - Etapa 1" y no podra ser emparejado.

ETAPA 2: COMPATIBILIDAD
------------------------

Para competidores del mismo sexo y cinturon, el sistema calcula un
"puntaje de compatibilidad" para cada posible par:

    PUNTAGE TOTAL = (Puntaje Peso x 50%) + (Puntaje Estatura x 20%) + 
                    (Puntaje Edad x 20%) + (Bonus Escuela x 10%)

Donde:

- PUNTAJE PESO: 
  * Misma libra = 100%
  * Diferencia de 5kg = 0%
  * Entre mas cerca, mayor el puntaje

- PUNTAJE ESTATURA:
  * Misma estatura = 100%
  * Diferencia de 10cm = 0%

- PUNTAJE EDAD:
  * Misma edad = 100%
  * Diferencia de 1 ano = 100%
  * Diferencia de 3 anos = 0%

- BONUS ESCUELA:
  * Si son de escuelas diferentes = +10%
  * Esto promueve diversidad entre clubes

El sistema forma graficas de 2, 3 o 4 competidores buscando los mejores
puntajes de compatibilidad.

ETAPA 3: RELAJAMIENTO
----------------------

Si un competidor no encontro pareja en la Etapa 2, el sistema intenta
emparejarlo con reglas mas flexibles:

RONDA 1 - Edad relajada:
- Permite diferencia de edad de hasta 2 anos
- Mantiene limites de peso (±5kg) y estatura (±10cm)

RONDA 2 - Limites relajados:
- Permite diferencia de edad de 2-3 anos
- Permite diferencia de peso de hasta 6kg
- Permite diferencia de estatura de hasta 12cm

Si aun asi no encuentra pareja, el competidor queda marcado como
"sin rival - requiere revision manual".

NUMERACION
----------

Una vez generadas las graficas, el sistema asigna numeros:

- NUMERO DE COMPETIDOR: 
  Prefijo del bloque + numero secuencial
  Ejemplos: "MR 1", "MR 2", "AD 15", "AZ 3"

  Prefijos por bloque:
  - Adultos Grupo 1 y 2: AD
  - Infantil Azul: AZ
  - Infantil Verde: VD
  - Infantil Amarilla: AM
  - Infantil Blanca: BC
  - Infantil Marron: MR
  - Infantil Roja: RJ
  - Infantil Negra: PM
  - Pre-Taekwondo: PT

- NUMERO DE GRAFICA: 
  Numero secuencial global (1, 2, 3, ...)

- NUMERO DE AREA: 
  Cicla del 1 al 12 ((numero_grafica - 1) % 12) + 1


API REST - DOCUMENTACION TECNICA
================================================================================

El backend expone los siguientes endpoints:

ENDPOINTS PRINCIPALES
----------------------

GET  /                   - Informacion general de la API
GET  /health            - Verificar que el servidor funciona
POST /upload            - Subir archivo Excel para procesar

ENDPOINTS DE PRUEBAS
-------------------

GET  /tests             - Ejecutar pruebas con archivos de prueba
GET  /tests/random      - Ejecutar pruebas con datos aleatorios
GET  /tests/latest      - Ver ultimo reporte de pruebas

ENDPOINTS DE RECOMENDACIONES
----------------------------

POST /api/recommendations/generate - Generar recomendaciones para sin pareja
POST /api/recommendations/apply     - Aplicar una recomendacion
POST /api/manual_assign             - Asignar manualmente un competidor
POST /api/undo                       - Deshacer ultima accion
POST /api/finalize                   - Finalizar emparejamiento

EJEMPLOS DE USO CON CURL
-------------------------

Verificar que el servidor funciona:
    curl http://localhost:8000/health

Subir un archivo Excel:
    curl -X POST -F "file=@template/competidores_ejemplo.xlsx" http://localhost:8000/upload

Ver documentacion interactiva (Swagger UI):
    Abre en tu navegador: http://localhost:8000/docs


SOLUCION DE PROBLEMAS
================================================================================

PROBLEMA: "python no se reconoce como un comando interno"
-----------------------------------------------------------
- Asegurate de haber agregado Python al PATH durante la instalacion
- O usa la ruta completa: C:\Python311\python.exe

PROBLEMA: "Port 8000 is already in use"
---------------------------------------
Otro programa esta usando el puerto 8000. Puedes:
- Cerrar el otro programa
- O cambiar el puerto en backend/run.py modificando: port=8001

PROBLEMA: "Port 4321 is already in use"
---------------------------------------
El frontend intentara automaticamente en otro puerto.
Revisa el mensaje en la terminal para ver que puerto uso.

PROBLEMA: Error al leer archivo Excel
-------------------------------------
- Asegurate de que el archivo sea .xlsx (no .xls)
- Verifica que las hojas tengan los nombres correctos
- Verifica que las columnas existan

PROBLEMA: "Module not found" o errores de importacion
-------------------------------------------------------
- Asegurate de haber activado el entorno virtual
- Ejecuta: pip install -r requirements.txt

PROBLEMA: El navegador no conecta al servidor
---------------------------------------------
- Verifica que el backend este corriendo (terminal 1)
- Verifica que el frontend este corriendo (terminal 2)
- Intenta en otro navegador


EJECUTAR PRUEBAS
================================================================================

Si quieres ejecutar las pruebas automatizadas del proyecto:

1. Abre una terminal
2. Navega al backend:
       cd C:\Users\USUARIO\Desktop\sitiosLocales\Graficador\backend
3. Activa el entorno virtual:
       venv\Scripts\activate
4. Ejecuta las pruebas:
       pytest tests/

Tambien puedes ver las pruebas disponibles en:
    http://localhost:8000/tests


CONSTRUIR PARA PRODUCCION
================================================================================

Si quieres crear una version de produccion del frontend:

1. Navega al frontend:
       cd C:\Users\USUARIO\Desktop\sitiosLocales\Graficador\frontend

2. Ejecuta el build:
       npm run build

3. Los archivos estaran en: frontend/dist/
   Puedes servir estos archivos con cualquier servidor web estatico.


INFORMACION ADICIONAL
================================================================================

TECNOLOGIAS UTILIZADAS
----------------------

Backend:
- Python 3.11+ - Lenguaje de programacion
- FastAPI - Framework web moderno y rapido
- Uvicorn - Servidor ASGI de alto rendimiento
- Pandas - Manipulacion y analisis de datos
- NumPy - Calculos numericos
- OpenPyXL - Lectura de archivos Excel

Frontend:
- Astro - Framework web moderno
- React - Biblioteca de componentes de interfaz
- XLSX - Manipulacion de Excel en el navegador
- TypeScript - Tipado opcional

ESPECIFICACIONES TECNICAS
--------------------------

Para ver las especificaciones tecnicas completas del algoritmo y sistema,
consulta el archivo: espec.md

Este documento contiene informacion detallada sobre:
- Reglas exactas del algoritmo
- Mapeo de grados a cinturones
- Calculos de puntajes de compatibilidad
- Estructuras de datos
- Criterios de aceptacion


================================================================================
                    GRAFICADOR - TAEKWONDO BRACKET SYSTEM
================================================================================

Proyecto creado para automatizar el proceso de emparejamiento en torneos
de Taekwondo, garantizando competencia justa y equilibrada.

Para soporte o reportar errores, por favor contacta al equipo de desarrollo.
