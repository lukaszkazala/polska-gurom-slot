# Dziesięć przykładów do inspekcji

Jednostki wypłat: 100 = 1× całkowitej stawki. Przykłady wyeksportowane automatycznie; ich pełne przebiegi zweryfikowano niezależnym kalkulatorem w audycie całego banku. Nie jest to deklaracja dziesięciu ręcznych testów w ACP.

## Rekord 0

```text
L4 P3 L1 SCATTER WILD
L1 L1 P2 L1 L4
P4 SCATTER L4 P1 L1
```

| Linia | Symbol | Bębny | Wypłata × stawka |
|---|---|---|---:|
| 12 | L1 | 1–3 | 0.1 |
| 14 | L1 | 1–5 | 2 |
| 16 | L1 | 3–5 | 0.1 |
| 18 | L1 | 2–5 | 0.6 |

Scatter bazy: 0×. Baza łącznie z kaskadami: 2.8×. Bonus: 0/0 obrotów, 0×. Cała runda: **2.8×**, zgodna z CSV. Redukcja przez limit: 0×.

## Rekord 12

```text
P2 L4 L1 L1 L1
L4 L1 P1 P2 P1
L3 P4 L3 L4 L2
```

| Linia | Symbol | Bębny | Wypłata × stawka |
|---|---|---|---:|
| 4 | L1 | 3–5 | 0.1 |
| 12 | L1 | 2–4 | 0.1 |
| 20 | L1 | 2–4 | 0.1 |

Scatter bazy: 0×. Baza łącznie z kaskadami: 0.3×. Bonus: 0/0 obrotów, 0×. Cała runda: **0.3×**, zgodna z CSV. Redukcja przez limit: 0×.

## Rekord 15

```text
P4 L4 L1 P3 P1
L2 L2 P1 L2 L2
L1 P3 L3 WILD L3
```

| Linia | Symbol | Bębny | Wypłata × stawka |
|---|---|---|---:|
| 5 | L3 | 3–5 | 0.2 |

Scatter bazy: 0×. Baza łącznie z kaskadami: 0.2×. Bonus: 0/0 obrotów, 0×. Cała runda: **0.2×**, zgodna z CSV. Redukcja przez limit: 0×.

## Rekord 287

```text
SCATTER L2 P3 SCATTER L1
L1 P3 L1 L1 SCATTER
P1 L1 SCATTER P1 L1
```

| Linia | Symbol | Bębny | Wypłata × stawka |
|---|---|---|---:|
| 8 | L1 | 3–5 | 0.1 |
| 9 | L1 | 3–5 | 0.1 |

Scatter bazy: 5×. Baza łącznie z kaskadami: 5.2×. Bonus: 10/10 obrotów, 107.2×. Cała runda: **112.4×**, zgodna z CSV. Redukcja przez limit: 0×.

## Rekord 484

```text
L1 SCATTER P3 P3 P3
P1 L1 L1 L2 L1
L3 P1 SCATTER WILD SCATTER
```

| Linia | Symbol | Bębny | Wypłata × stawka |
|---|---|---|---:|
| 3 | L1 | 2–4 | 0.1 |
| 4 | P3 | 3–5 | 1 |
| 8 | L1 | 1–3 | 0.1 |
| 10 | L1 | 1–4 | 0.6 |

Scatter bazy: 1×. Baza łącznie z kaskadami: 2.8×. Bonus: 8/8 obrotów, 113.6×. Cała runda: **116.4×**, zgodna z CSV. Redukcja przez limit: 0×.

## Rekord 6507

```text
SCATTER L1 L4 SCATTER P3
L1 SCATTER L1 L1 L2
P1 L1 P4 P1 WILD
```

| Linia | Symbol | Bębny | Wypłata × stawka |
|---|---|---|---:|
| 9 | L1 | 3–5 | 0.1 |

Scatter bazy: 1×. Baza łącznie z kaskadami: 1.1×. Bonus: 8/8 obrotów, 292×. Cała runda: **293.1×**, zgodna z CSV. Redukcja przez limit: 0×.

## Rekord 46183

```text
L1 P1 L4 P3 P3
SCATTER L2 L3 L1 L1
L1 P2 P1 SCATTER SCATTER
```

| Linia | Symbol | Bębny | Wypłata × stawka |
|---|---|---|---:|

Scatter bazy: 1×. Baza łącznie z kaskadami: 1×. Bonus: 8/8 obrotów, 527.8×. Cała runda: **528.8×**, zgodna z CSV. Redukcja przez limit: 0×.

## Rekord 100020

```text
WILD WILD WILD L2 L2
L1 L1 L1 L3 L3
P2 P2 P2 WILD WILD
```

| Linia | Symbol | Bębny | Wypłata × stawka |
|---|---|---|---:|
| 1 | L1 | 1–3 | 0.1 |
| 2 | L1 | 1–3 | 0.1 |
| 3 | L1 | 1–5 | 2 |
| 4 | L2 | 1–5 | 2.8 |
| 5 | P2 | 1–5 | 12 |
| 6 | L3 | 1–5 | 3.6 |
| 7 | P2 | 1–3 | 0.6 |
| 8 | L1 | 1–3 | 0.1 |
| 10 | L1 | 1–5 | 2 |
| 12 | L1 | 1–3 | 0.1 |
| 14 | L3 | 3–5 | 0.2 |
| 16 | L3 | 1–5 | 3.6 |
| 18 | L3 | 3–5 | 0.2 |

Scatter bazy: 0×. Baza łącznie z kaskadami: 5000×. Bonus: 0/0 obrotów, 0×. Cała runda: **5000×**, zgodna z CSV. Redukcja przez limit: 115.4×.

## Rekord 100024

```text
L1 L1 P3 SCATTER SCATTER
SCATTER SCATTER L1 L1 L1
L1 L1 SCATTER P1 P1
```

| Linia | Symbol | Bębny | Wypłata × stawka |
|---|---|---|---:|
| 1 | L1 | 3–5 | 0.1 |

Scatter bazy: 20×. Baza łącznie z kaskadami: 20.7×. Bonus: 12/12 obrotów, 139.2×. Cała runda: **159.9×**, zgodna z CSV. Redukcja przez limit: 0×.

## Rekord 100048

```text
P1 L1 L1 L1 P3
L3 P2 P4 P1 L1
P4 L4 L3 L2 SCATTER
```

| Linia | Symbol | Bębny | Wypłata × stawka |
|---|---|---|---:|
| 4 | L1 | 2–4 | 0.1 |
| 12 | L1 | 3–5 | 0.1 |
| 20 | L1 | 3–5 | 0.1 |

Scatter bazy: 0×. Baza łącznie z kaskadami: 0.3×. Bonus: 0/0 obrotów, 0×. Cała runda: **0.3×**, zgodna z CSV. Redukcja przez limit: 0×.
