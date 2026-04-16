# 📊 Reporte de Analisis - Algoritmo de Emparejamiento

**Fecha:** 2026-04-15 17:57:27
**Total pruebas ejecutadas:** 3

---

## 📌 1. Resumen Ejecutivo

| Metrica | Valor |
|---------|-------|
| Tasa emparejamiento global | 66.2% |
| Calidad global | 99.5% |
| Mejor prueba | random_3 (68.49%) |
| Peor prueba | random_2 (64.22%) |

### Top Razones de Fallo

1. `no_hay_rival_compatible` (279 casos)
2. `estatura_diff=6cm` (16 casos)
3. `estatura_diff=9cm` (15 casos)
4. `estatura_diff=7cm` (14 casos)
5. `estatura_diff=10cm` (12 casos)

---

## 📊 2. Tabla Comparativa de Pruebas

| Prueba | Comp | Brackets | Emparej% | Calidad% | Score | Excl | Baja | Sin Rival |
|--------|------|----------|----------|----------|-------|------|------|----------|
| random_1 | 305 | 86 | 65.9% | 100.0% | 0 | 86 | 0 | 104 |
| random_2 | 232 | 65 | 64.22% | 98.46% | 0 | 64 | 0 | 83 |
| random_3 | 292 | 90 | 68.49% | 100.0% | 0 | 90 | 0 | 92 |

---

## 🧩 3. Analisis por Categoria (Bloque)

### Adultos Grupo 1

- **Competidores:** 22
- **Brackets:** 22
- **Score promedio:** 1.2
- **Problemas frecuentes:**
  - `estatura_diff=10cm` (4 veces)
  - `peso_diff=3.1kg` (2 veces)
  - `estatura_diff=17cm` (2 veces)

### Adultos Grupo 2

- **Competidores:** 18
- **Brackets:** 18
- **Score promedio:** 1.19
- **Problemas frecuentes:**
  - `estatura_diff=6cm` (4 veces)
  - `estatura_diff=7cm` (2 veces)
  - `peso_diff=3.39kg` (2 veces)

### Infantil Amarilla

- **Competidores:** 11
- **Brackets:** 11
- **Score promedio:** 1.43
- **Problemas frecuentes:**
  - `estatura_diff=11cm` (2 veces)
  - `peso_diff=3.71kg` (2 veces)
  - `peso_diff=3.6kg` (2 veces)

### Infantil Azul

- **Competidores:** 140
- **Brackets:** 140
- **Score promedio:** 1.59
- **Problemas frecuentes:**
  - `estatura_diff=8cm` (10 veces)
  - `estatura_diff=6cm` (9 veces)
  - `estatura_diff=7cm` (8 veces)

### Infantil Blanca

- **Competidores:** 32
- **Brackets:** 32
- **Score promedio:** 1.46
- **Problemas frecuentes:**
  - `estatura_diff=6cm` (6 veces)
  - `estatura_diff=10cm` (6 veces)
  - `estatura_diff=8cm` (2 veces)

### Infantil Marrón

- **Competidores:** 118
- **Brackets:** 118
- **Score promedio:** 1.56
- **Problemas frecuentes:**
  - `estatura_diff=7cm` (10 veces)
  - `estatura_diff=9cm` (8 veces)
  - `estatura_diff=10cm` (6 veces)

### Infantil Negra

- **Competidores:** 20
- **Brackets:** 20
- **Score promedio:** 1.26
- **Problemas frecuentes:**
  - `peso_diff=3.65kg` (2 veces)
  - `peso_diff=3.16kg` (2 veces)
  - `estatura_diff=14cm` (2 veces)

### Infantil Roja

- **Competidores:** 18
- **Brackets:** 18
- **Score promedio:** 1.37
- **Problemas frecuentes:**
  - `estatura_diff=9cm` (4 veces)
  - `estatura_diff=6cm` (4 veces)
  - `estatura_diff=8cm` (2 veces)

### Infantil Verde

- **Competidores:** 148
- **Brackets:** 148
- **Score promedio:** 1.6
- **Problemas frecuentes:**
  - `estatura_diff=11cm` (12 veces)
  - `estatura_diff=9cm` (10 veces)
  - `estatura_diff=5cm` (7 veces)

### Pre-Taekwondo

- **Competidores:** 23
- **Brackets:** 23
- **Score promedio:** 1.65
- **Problemas frecuentes:**
  - `peso_diff=3.73kg` (2 veces)
  - `peso_diff=3.11kg` (2 veces)

---

## 🔍 4. Brackets de Baja Calidad (< 1.0)

**Total:** 12 brackets de baja calidad

### 1. Bracket #4 (random_1, Infantil Blanca)

**Tipo:** normal | **Score:** 0.9

**Competidores:**
- DAMIAN PEREZ: 11 anos, 39.26kg, 107.0cm, PAQUI
- JOSE HERNANDEZ: 13 anos, 35.45kg, 113.0cm, TAEKWONDO PLUS

**Desglose:**
- Edad diff: 2 anos -> 0.5 pts
- Peso diff: 3.81kg -> 0.12 pts
- Estatura diff: 6cm -> 0.08 pts
- Doyang bonus: 0.2 pts

**Razones de fallo:** `peso_diff=3.81kg`, `estatura_diff=6cm`

### 2. Bracket #3 (random_1, Adultos Grupo 2)

**Tipo:** normal | **Score:** 0.79

**Competidores:**
- ANGELICA RIVERA: 18 anos, 51.74kg, 196.0cm, CHAMPIONS
- DIEGO GOMEZ: 29 anos, 52.87kg, 179.0cm, PAQUI

**Desglose:**
- Edad diff: 11 anos -> 0.2 pts
- Peso diff: 1.13kg -> 0.39 pts
- Estatura diff: 17cm -> 0.0 pts
- Doyang bonus: 0.2 pts

**Razones de fallo:** `edad_diff=11 anos`, `estatura_diff=17cm`

### 3. Bracket #2 (random_1, Adultos Grupo 1)

**Tipo:** normal | **Score:** 0.89

**Competidores:**
- JUAN GOMEZ: 18 anos, 89.31kg, 170.0cm, CHAMPIONS
- JUAN MARTINEZ: 25 anos, 85.76kg, 173.0cm, OLIMPICO

**Desglose:**
- Edad diff: 7 anos -> 0.4 pts
- Peso diff: 3.55kg -> 0.15 pts
- Estatura diff: 3cm -> 0.14 pts
- Doyang bonus: 0.2 pts

**Razones de fallo:** `peso_diff=3.55kg`

### 4. Bracket #3 (random_1, Adultos Grupo 1)

**Tipo:** normal | **Score:** 0.81

**Competidores:**
- ADRIANA RODRIGUEZ: 22 anos, 77.48kg, 179.0cm, MDK FLORIDO
- MARIA DIAZ: 29 anos, 72.82kg, 178.0cm, CHAMPIONS

**Desglose:**
- Edad diff: 7 anos -> 0.4 pts
- Peso diff: 4.66kg -> 0.03 pts
- Estatura diff: 1cm -> 0.18 pts
- Doyang bonus: 0.2 pts

**Razones de fallo:** `peso_diff=4.66kg`

### 5. Bracket #41 (random_2, Infantil Marrón)

**Tipo:** normal | **Score:** 0.96

**Competidores:**
- KEVIN GUTIERREZ: 13 anos, 37.78kg, 151.0cm, CHAMPIONS
- MARIA RAMOS: 11 anos, 41.81kg, 149.0cm, TAEKWONDO PLUS

**Desglose:**
- Edad diff: 2 anos -> 0.5 pts
- Peso diff: 4.03kg -> 0.1 pts
- Estatura diff: 2cm -> 0.16 pts
- Doyang bonus: 0.2 pts

**Razones de fallo:** `peso_diff=4.03kg`

### 6. Bracket #42 (random_2, Infantil Marrón)

**Tipo:** normal | **Score:** 0.85

**Competidores:**
- MARIA MARTINEZ: 10 anos, 48.67kg, 151.0cm, MDK CASA BLANCA
- CAMILA TORRES: 8 anos, 44.99kg, 160.0cm, PAQUI

**Desglose:**
- Edad diff: 2 anos -> 0.5 pts
- Peso diff: 3.68kg -> 0.13 pts
- Estatura diff: 9cm -> 0.02 pts
- Doyang bonus: 0.2 pts

**Razones de fallo:** `peso_diff=3.68kg`, `estatura_diff=9cm`

### 7. Bracket #3 (random_2, Infantil Negra)

**Tipo:** normal | **Score:** 0.56

**Competidores:**
- JOSE GOMEZ: 7 anos, 41.37kg, 150.0cm, CHAMPIONS
- ESTEBAN CRUZ: 9 anos, 45.79kg, 140.0cm, CHAMPIONS

**Desglose:**
- Edad diff: 2 anos -> 0.5 pts
- Peso diff: 4.42kg -> 0.06 pts
- Estatura diff: 10cm -> 0.0 pts
- Doyang bonus: 0.0 pts

**Razones de fallo:** `peso_diff=4.42kg`, `estatura_diff=10cm`

### 8. Bracket #3 (random_2, Adultos Grupo 2)

**Tipo:** normal | **Score:** 0.74

**Competidores:**
- DIANA GUTIERREZ: 18 anos, 93.58kg, 150.0cm, TAEKWONDO PLUS
- KARLA HERNANDEZ: 27 anos, 97.22kg, 165.0cm, MDK FLORIDO

**Desglose:**
- Edad diff: 9 anos -> 0.4 pts
- Peso diff: 3.64kg -> 0.14 pts
- Estatura diff: 15cm -> 0.0 pts
- Doyang bonus: 0.2 pts

**Razones de fallo:** `peso_diff=3.64kg`, `estatura_diff=15cm`

### 9. Bracket #5 (random_3, Adultos Grupo 1)

**Tipo:** normal | **Score:** 0.95

**Competidores:**
- CARLOS CRUZ: 25 anos, 68.97kg, 175.0cm, VICTORY
- DANIEL ORTIZ: 28 anos, 73.52kg, 156.0cm, PAQUI

**Desglose:**
- Edad diff: 3 anos -> 0.7 pts
- Peso diff: 4.55kg -> 0.05 pts
- Estatura diff: 19cm -> 0.0 pts
- Doyang bonus: 0.2 pts

**Razones de fallo:** `peso_diff=4.55kg`, `estatura_diff=19cm`

### 10. Bracket #8 (random_3, Infantil Blanca)

**Tipo:** normal | **Score:** 0.7

**Competidores:**
- LUIS DIAZ: 9 anos, 20.76kg, 123.0cm, KORYO
- SOFIA RODRIGUEZ: 11 anos, 25.76kg, 111.0cm, VICTORY

**Desglose:**
- Edad diff: 2 anos -> 0.5 pts
- Peso diff: 5.0kg -> 0.0 pts
- Estatura diff: 12cm -> 0.0 pts
- Doyang bonus: 0.2 pts

**Razones de fallo:** `peso_diff=5.0kg`, `estatura_diff=12cm`

_... y 2 mas_

---

## ❌ 5. Analisis de Competidores Sin Rival

**Total no emparejados:** 279

### Por Bloque

| Bloque | Cantidad | Porcentaje |
|--------|----------|------------|
| Infantil Azul | 42 | 15.1% |
| Infantil Verde | 37 | 13.3% |
| Infantil Marrón | 34 | 12.2% |
| Adultos Grupo 2 | 32 | 11.5% |
| Infantil Negra | 30 | 10.8% |
| Adultos Grupo 1 | 28 | 10.0% |
| Pre-Taekwondo | 27 | 9.7% |
| Infantil Amarilla | 19 | 6.8% |
| Infantil Blanca | 18 | 6.5% |
| Infantil Roja | 12 | 4.3% |

### Por Motivo

| Motivo | Casos |
|--------|-------|
| No compatible partner after Etapa 3 | 279 |

---

## 📈 6. Metricas por Componente

### Distribucion de Diferencias

| Componente | Avg | P50 | P75 | P95 | Max |
|------------|-----|-----|-----|-----|-----|
| Edad (anos) | 0.96 | 1 | 1 | 3 | 11 |
| Peso (kg) | 1.86 | 1.61 | 2.64 | 4.57 | 5.0 |
| Estatura (cm) | 5.5 | 5 | 8 | 13 | 19 |

### Scores Promedio por Componente

| Componente | Score Promedio |
|------------|----------------|
| Edad | 0.92 |
| Peso | 0.31 |
| Estatura | 0.1 |

**Doyang bonus aplicado:** 96.3% de brackets
**Total brackets analizados:** 241

---

## 🎯 Recomendaciones

- **Emparejamiento:** 33.7% de competidores no encuentran rival. Considerar relajamiento controlado.

---

_Reporte generado automaticamente el 2026-04-15 17:57:27_