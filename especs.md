# MVP Specifications: Bracket Automation System for Taekwondo Tournaments

## 1. MVP Scope

The goal of this MVP is to **test the core pairing algorithm** by allowing an administrator to upload an Excel file with a specific format (one sheet per competition block) and automatically generate brackets (gráficas) following the rules defined in the project brief. Additionally, the system will display a **statistics panel** to evaluate the results.

**What is included in the MVP:**

- File upload (Excel `.xlsx`) with predefined structure.
- Automatic classification and pairing algorithm (Etapas 1, 2 and basic Etapa 3).
- Generation of competitor numbers, bracket numbers, and area numbers.
- Visual display of generated brackets (list or tree view).
- Statistics panel: totals, distribution, quality indicators.
- Basic error reporting for unpaired competitors.

**What is NOT included in this MVP (post-MVP features):**

- User roles (Admin, Collaborator, Professor, Parent).
- Manual adjustment of brackets via UI.
- Public search portal for parents.
- PDF/printable output generation.
- History and tournament management.
- Notifications and approval workflows.

---

## 2. Input Excel Format

The system accepts one `.xlsx` file containing **one sheet per competition block** (bloque). Each sheet name **must match one of the predefined blocks** from the brief:
AD (Adultos grupo 1)
AD (Adultos grupo 2) → Use “AD2” or “Adultos Grupo 2” but brief shows same prefix. For MVP, accept:

“Adultos Grupo 1”

“Adultos Grupo 2”

“Infantil Azul”

“Infantil Verde”

“Infantil Amarilla”

“Infantil Blanca”

“Pre-Taekwondo”

“Infantil Marrón”

“Infantil Roja”

“Infantil Negra”

text

If a sheet name does not match any known block, it will be ignored or shown as error.

### 2.1 Columns (exactly as in the image)

| Column name | Type | Description |
|-------------|------|-------------|
| `No` | Integer (optional) | Ignored by the system (internal row number). |
| `Nombre` | String | First name(s). |
| `Apellido` | String | Last name(s). |
| `Edad` | Integer | Age in years. |
| `H/M` | String | `H` for male, `M` for female. |
| `Grado` | String | Cinta value (e.g., `3 KUP`, `2 KUP`, `1er Dan`, `Blanca`, etc.) |
| `Peso` | Float | Weight in kg (decimal with comma or dot). |
| `Estatura` | Float | Height in cm. |
| `Modalidad` | String | `Doble` or `Sencillo`. May also accept `Combate`/`Poomsae`. |
| `Doyang` | String | School name. |

**Example row (from image):**
MR 1, JESUS BALDEMAR, LÓPEZ CAMACHO, 7, H, 3 KUP, 24,75, 122,00, Doble, MDK FLORIDO

text

### 2.2 Data normalization

- **Sexo**: `H` → Masculino, `M` → Femenino.
- **Peso / Estatura**: Convert comma to dot (e.g., `24,75` → `24.75`).
- **Grado mapping to cinta block** (for filtering in Etapa 1):

| Input value | Assigned block |
|-------------|----------------|
| `Pre-Taekwondo` | Pre-Taekwondo |
| `Blanca`, `10 KUP` | Blanca |
| `Amarilla`, `9 KUP` | Amarilla |
| `Verde`, `8 KUP` | Verde |
| `Azul`, `7 KUP` | Azul |
| `Marrón`, `3 KUP` | Marrón |
| `Roja`, `2 KUP`, `1 KUP` | Roja |
| `1er Dan`, `1er Poom`, `1 Dan` | Negra (Dan or Poom) |
| `2do Dan`, `2nd Dan`, etc. | Negra (Dan) |
| `1er Poom`, `2do Poom` | Negra (Poom) |

**Important**: For `Negra`, the system must distinguish between **Poom** (infantil, <15 years) and **Dan** (adulto, ≥15 years). If `Edad` < 15 and Grado contains `Poom`, assign to `Negra (Poom)`. If `Edad` ≥ 15, assign to `Negra (Dan)`. If only “Negra” is provided without Dan/Poom, infer from age.

---

## 3. Core Algorithm (MVP implementation)

The algorithm follows the three-stage logic described in the brief, with a simplified Etapa 3 (only Ronda 1 and Ronda 2 are automated; Ronda 3/4 will be logged as “needs manual review” but not resolved in UI).

### 3.1 Etapa 1 – Mandatory filters

For each sheet (bloque), group competitors by:

1. **Sexo** (M/F)
2. **Cinta block** (according to mapping above)

If a competitor has no other competitor in the same sex + same cinta block, they are immediately marked as **“sin rival – Etapa 1”** and will appear in the statistics panel.

### 3.2 Etapa 2 – Compatibility score & pairing

Inside each (sexo, cinta block) group:

- Sort competitors by age (ascending).
- Compute a compatibility score for every possible pair (i, j) using:
Score =
(PesoScore * 0.5) +
(EstaturaScore * 0.2) +
(EdadScore * 0.2) +
(DoyangBonus * 0.1)

Where:

PesoScore = max(0, 1 - abs(peso_i - peso_j) / 5.0) capped at 1.

EstaturaScore = max(0, 1 - abs(est_i - est_j) / 10.0)

EdadScore = 1 if abs(edad_i - edad_j) <= 1, else max(0, 1 - (abs(edad_i - edad_j)-1)/2)

DoyangBonus = 0.2 if doyang_i != doyang_j else 0

text

**Pairing logic** (greedy):

- While there are at least 2 competitors left:
  - Find the pair with highest score.
  - Form a bracket of size 2.
  - Optionally, try to add a 3rd competitor if:
    - There exists a competitor with average score to the existing pair >= 0.6
  - Optionally, try to add a 4th competitor if:
    - There exists a competitor with average score to the existing trio >= 0.5
  - Remove selected competitors from the pool.
- Remaining competitors (1 or 2 that couldn’t form a valid pair) go to **Etapa 3**.

### 3.3 Etapa 3 – Relaxation (MVP limited)

For competitors not paired in Etapa 2:

- **Ronda 1**: Search within the same cinta block but allow age difference up to ±2 years. Use same weight/height limits (±5 kg, ±10 cm). If a partner found, mark bracket as `type = "relaxed_age"`.
- **Ronda 2**: Same cinta block, relaxed limits: ±6 kg, ±12 cm, age ±2 years (infantil) / ±3 years (adulto). If partner found, mark bracket as `type = "relaxed_limits"`.
- If still unpaired, mark competitor as **“sin rival – requiere revisión manual”** (no automated cross-block search in MVP).

**Note**: Cross-block pairing (Ronda 3 and 4) is **not implemented** in MVP; those cases will be flagged for manual handling.

---

## 4. Numbering & Output Generation

After all brackets are formed (including relaxed ones), the system assigns:

### 4.1 Competitor number (Número de competidor)

- Format: `{prefijo} {secuencia}` where `prefijo` is from the block (see table below).
- Sequence resets per block and increments by 1.
- Example: `MR 1`, `MR 2`, `AD 1`, `RJ 23`.

| Bloque | Prefijo |
|--------|---------|
| Adultos Grupo 1 | AD |
| Adultos Grupo 2 | AD |
| Infantil Azul | AZ |
| Infantil Verde | VD |
| Infantil Amarilla | AM |
| Infantil Blanca | BC |
| Pre-Taekwondo | PT |
| Infantil Marrón | MR |
| Infantil Roja | RJ |
| Infantil Negra | PM |

### 4.2 Bracket number (Número de gráfica)

- Global sequential number starting from 1.
- Adults blocks (both AD groups) always start from 1.
- Then continue with the rest of blocks in the order they appear in the file (or fixed order: AD1, AD2, then AZ, VD, AM, BC, PT, MR, RJ, PM).

### 4.3 Area number (Número de área)

- `((bracket_number - 1) % 12) + 1` → cycles from 1 to 12.

---

## 5. Statistics Panel

After processing, the MVP shows a dashboard with the following metrics:

### 5.1 Global statistics

- Total competitors
- Total brackets generated
- Average bracket size (total competitors / total brackets)
- Number of brackets of size 2, 3, 4
- Number of “sin rival” competitors (unpaired after Etapa 3)

### 5.2 Per-block statistics (table)

| Bloque | Competitors | Brackets | Avg size | Sin rival | Relaxed brackets (Ronda 1/2) |
|--------|-------------|----------|----------|-----------|------------------------------|

### 5.3 Quality indicators

- Percentage of brackets with score ≥ 70 (Excelente/Bueno)
- Percentage of brackets with score < 50 (Bajo/Muy bajo, includes relaxed)

### 5.4 List of unpaired competitors

Show each unpaired competitor with:
- Nombre, Apellido, Bloque, Edad, Peso, Estatura, Grado, Doyang
- Reason: `“No rival in same sex & cinta block”` or `“No compatible partner after Etapa 3”`

---

## 6. UI Screens (MVP)

The MVP will have **two main screens**:

### Screen 1: File Upload & Processing

- Drag-and-drop or file picker for `.xlsx`.
- Button “Procesar”.
- While processing: show loading spinner.
- After processing: redirect to results screen or show inline results.

### Screen 2: Results & Statistics

- Statistics panel (as described above).
- Collapsible view per block showing all brackets.
- For each bracket display:
  - Bracket number, area number
  - List of competitors with their assigned competitor number, name, age, weight, height, doyang.
  - Compatibility score (if bracket size=2 show pair score; if size>2 show average score).
  - Tag: `Normal`, `Relajado (edad)`, `Relajado (peso/estatura)`
- Button “Export JSON” (for debugging) – optional.
- Button “Reset” to upload a new file.

---

## 7. Technical Notes (for developers)

### 7.1 Backend (suggested)

- Python + FastAPI or Flask
- Use `pandas` to read Excel, `openpyxl` as engine.
- Implement algorithm in a separate module.

### 7.2 Frontend (suggested)

- React or Vue.js (simple)
- Display tables with sorting/filtering.

### 7.3 Data structures

```python
class Competidor:
    id: str (generated)
    nombre: str
    apellido: str
    edad: int
    sexo: str ("M" or "F")
    grado_raw: str
    cinta_block: str
    peso_kg: float
    estatura_cm: float
    modalidad: str ("Doble", "Sencillo")
    doyang: str
    bloque: str  # sheet name
    numero_competidor: Optional[str]
    
class Bracket:
    id: int (global)
    area: int
    competidores: List[Competidor]
    tipo: str ("normal", "relaxed_age", "relaxed_limits")
    score: float  # average compatibility
7.4 Validation rules
Required fields: Nombre, Apellido, Edad, H/M, Grado, Peso, Estatura, Modalidad, Doyang.

If any field missing, skip row and add to error list.

Invalid numeric values (e.g., peso=“abc”) → skip.

8. Acceptance Criteria for MVP
Upload: User can upload an Excel file with multiple sheets named as valid blocks.

Processing: System reads each sheet, maps grades to cinta blocks, filters by sex and cinta, computes pair scores, and creates brackets.

Numbering: Competitor numbers, bracket numbers, area numbers are assigned correctly according to rules.

Statistics panel displays all required metrics.

Unpaired cases are clearly listed with reasons.

Performance: Processing 1000 competitors takes less than 5 seconds.

Errors: If file format is wrong, show descriptive error (e.g., “Missing column 'Edad' in sheet 'Infantil Marrón'”).

9. Future enhancements (after MVP)
Manual override UI for unpaired cases.

Cross-block pairing (Ronda 3 & 4).

PDF/printable bracket sheets.

User roles and collaborative workflow.

Parent search portal.

10. Sample Excel (mock)
Create a file named competidores_ejemplo.xlsx with two sheets:

Sheet “Infantil Marrón”

No	Nombre	Apellido	Edad	H/M	Grado	Peso	Estatura	Modalidad	Doyang
1	JESUS BALDEMAR	LÓPEZ CAMACHO	7	H	3 KUP	24,75	122	Doble	MDK FLORIDO
2	DAMIAN ALEJANDRO	ZAMUDIO BOGARÍN	7	H	3 KUP	30,00	133	Doble	MDK CASA BLANCA
Sheet “Infantil Roja”

No	Nombre	Apellido	Edad	H/M	Grado	Peso	Estatura	Modalidad	Doyang
1	SOFIA	MARTINEZ	9	M	2 KUP	28,5	130	Sencillo	MDK EL DORADO
Upload this file → the system should create one bracket for the two male Infantil Marrón competitors and mark the female Infantil Roja as “sin rival” because no same-sex partner.

11. Definition of Done for MVP
Backend API endpoint /upload accepts file and returns JSON with brackets, statistics, and unpaired list.

Frontend displays the results in a clean, readable layout.

The algorithm output matches manual verification on at least 3 sample Excel files provided by the client.

A simple README explains how to run the MVP locally.

.5 Automated Testing Strategy (Validating the Algorithm)
To ensure the pairing algorithm works correctly across thousands of possible scenarios—including edge cases like extreme weight differences, missing rivals, and mixed modalidades—the MVP will include a comprehensive automated test suite built with pytest (since the backend is Python‑based). The test suite will cover three layers:

Unit tests for individual scoring functions (compute_weight_score, compute_edad_score, etc.) using pytest.mark.parametrize to feed dozens of pre‑defined input‑output pairs.

Integration tests that run the full pair_competitors() function on synthetic competitor lists (generated either manually as fixtures or automatically with Hypothesis), asserting that the output brackets respect Etapa 1 filters, produce correct bracket sizes, and correctly flag unpaired competitors.

Regression tests using real Excel extracts from past tournaments (anonymised), stored in a tests/fixtures/ folder, to verify that the algorithm’s decisions match previously approved manual bracketings.

All tests will be executed automatically on every code change (via a simple script or GitHub Actions) and must pass before any new feature is merged. This approach guarantees that the algorithm remains reliable and predictable, even as we later add relaxation rounds (Ronda 3/4) and cross‑block pairing.