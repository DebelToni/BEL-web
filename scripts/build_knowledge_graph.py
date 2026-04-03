from __future__ import annotations

import csv
import html
import itertools
import json
import math
import random
import re
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "graph"
DB_PATH = OUTPUT_DIR / "knowledge_graph.db"
HTML_PATH = OUTPUT_DIR / "knowledge_graph.html"
JSON_PATH = OUTPUT_DIR / "graph_data.json"
WORKS_CSV_PATH = OUTPUT_DIR / "works.csv"
EDGES_CSV_PATH = OUTPUT_DIR / "edges.csv"
WORK_MOTIFS_CSV_PATH = OUTPUT_DIR / "work_motif_scores.csv"
MOTIFS_MD_PATH = OUTPUT_DIR / "motifs.md"


STOPWORDS = {
    "и",
    "в",
    "на",
    "с",
    "за",
    "по",
    "от",
    "се",
    "че",
    "е",
    "са",
    "не",
    "като",
    "но",
    "до",
    "или",
    "при",
    "над",
    "под",
    "то",
    "тя",
    "те",
    "той",
    "му",
    "й",
    "го",
    "ги",
    "си",
    "със",
    "във",
    "тази",
    "този",
    "това",
    "които",
    "който",
    "която",
    "както",
    "чрез",
    "без",
    "едно",
    "един",
    "една",
    "всичко",
    "всички",
    "само",
    "още",
    "тях",
    "него",
    "нея",
    "между",
    "сред",
    "подчертава",
    "показва",
    "разкрива",
    "творбата",
    "произведението",
    "текстът",
    "авторът",
    "лирическият",
    "говорител",
    "героят",
    "героите",
    "образът",
    "анализ",
    "описание",
    "основни",
    "мотиви",
}


MOTIFS = [
    {
        "id": "love",
        "label": "Любов",
        "color": "#ff1744",
        "description": "Любов, близост, нежност, раздяла и интимно посвещение.",
        "hover_phrase": "любовта, близостта и интимното преживяване",
        "keywords": [
            "любов",
            "либ",
            "любим",
            "неж",
            "сърц",
            "раздял",
            "щаст",
            "целув",
            "красот",
            "посвещ",
            "любовн",
        ],
    },
    {
        "id": "homeland_memory",
        "label": "Родина и памет",
        "color": "#ff6d00",
        "description": "Родина, народ, национална памет, будителство и историческа принадлежност.",
        "hover_phrase": "родината, народа и историческата памет",
        "keywords": [
            "родин",
            "отече",
            "народ",
            "българ",
            "национал",
            "родолюб",
            "будит",
            "памет",
            "възраждан",
            "историческ",
            "отечеств",
        ],
    },
    {
        "id": "freedom_revolt",
        "label": "Свобода и бунт",
        "color": "#ffd600",
        "description": "Свобода, съпротива, бунт, революционен избор и отказ от покорство.",
        "hover_phrase": "свободата, борбата и отказа от покорство",
        "keywords": [
            "свобод",
            "борб",
            "бунт",
            "револю",
            "робств",
            "въстан",
            "саможертв",
            "съпротив",
            "пробужд",
            "освобожд",
        ],
    },
    {
        "id": "faith_spirituality",
        "label": "Вяра и духовност",
        "color": "#aeea00",
        "description": "Вяра, молитва, духовна светлина, манастир, религиозна и нравствена опора.",
        "hover_phrase": "вярата, духовната опора и нравственото търсене",
        "keywords": [
            "вяр",
            "бог",
            "молит",
            "духов",
            "манаст",
            "светин",
            "свят",
            "свято",
            "кръст",
            "монах",
            "светлин",
            "спас",
        ],
    },
    {
        "id": "nature",
        "label": "Природа",
        "color": "#00c853",
        "description": "Природа, пейзаж, земя, стихии, море, езеро и жив свят.",
        "hover_phrase": "природата като среда, символ и изпитание",
        "keywords": [
            "природ",
            "езер",
            "градуш",
            "планин",
            "манастир",
            "море",
            "земя",
            "слънц",
            "нощ",
            "дъжд",
            "животн",
            "реколт",
            "село",
            "рила",
        ],
    },
    {
        "id": "family_kinship",
        "label": "Семейство и род",
        "color": "#00b8d4",
        "description": "Семейство, род, дом, наследство, поколение и родова връзка.",
        "hover_phrase": "семейството, рода и наследената принадлежност",
        "keywords": [
            "семей",
            "род",
            "дом",
            "майк",
            "бащ",
            "наслед",
            "потом",
            "поколен",
            "родов",
            "дец",
            "домът",
        ],
    },
    {
        "id": "labor_creativity",
        "label": "Труд и творчество",
        "color": "#00b0ff",
        "description": "Труд, майсторство, занаят, изкуство, творчество и съзидание.",
        "hover_phrase": "труда, майсторството и творческото съзидание",
        "keywords": [
            "труд",
            "майстор",
            "дарб",
            "творч",
            "изкуств",
            "занаят",
            "поез",
            "слово",
            "колел",
            "цигул",
            "работ",
            "сътвор",
        ],
    },
    {
        "id": "social_power",
        "label": "Общество и власт",
        "color": "#2962ff",
        "description": "Власт, обществена неправда, бюрокрация, бедност и социален натиск.",
        "hover_phrase": "сблъсъка между човека, властта и социалната неправда",
        "keywords": [
            "власт",
            "общест",
            "социал",
            "бедност",
            "несправ",
            "чинов",
            "бюрокр",
            "закон",
            "високомер",
            "манипул",
            "публич",
            "примирен",
            "система",
        ],
    },
    {
        "id": "identity_conflict",
        "label": "Личност и вътрешен конфликт",
        "color": "#6200ea",
        "description": "Личен избор, раздвоение, съвест, самота, идентичност и самопознание.",
        "hover_phrase": "вътрешния избор, самотата и търсенето на себе си",
        "keywords": [
            "душ",
            "съвест",
            "избор",
            "самот",
            "раздво",
            "вътреш",
            "идентич",
            "самопозн",
            "болк",
            "страдан",
            "личност",
            "трагич",
        ],
    },
    {
        "id": "death_sacrifice",
        "label": "Смърт и саможертва",
        "color": "#aa00ff",
        "description": "Смърт, жертва, война, памет за мъртвите, трагизъм и гробна символика.",
        "hover_phrase": "смъртта, жертвата и паметта за загиналите",
        "keywords": [
            "смърт",
            "жертв",
            "войн",
            "гроб",
            "загин",
            "покой",
            "траур",
            "гробищ",
            "мъртв",
            "саркоф",
            "война",
        ],
    },
    {
        "id": "foreign_other",
        "label": "Чуждото и другият",
        "color": "#d500f9",
        "description": "Чуждото, срещата с другия, Европа, пленникът и различната гледна точка.",
        "hover_phrase": "чуждото, срещата с другия и различната гледна точка",
        "keywords": [
            "чужд",
            "друг",
            "европ",
            "плен",
            "сръбск",
            "чужден",
            "балкан",
            "другост",
            "пленник",
        ],
    },
    {
        "id": "hope_community",
        "label": "Надежда и общност",
        "color": "#ff4081",
        "description": "Надежда, съпричастност, солидарност, милосърдие, спасение и общност.",
        "hover_phrase": "надеждата, общността и човешката взаимност",
        "keywords": [
            "надежд",
            "общност",
            "съчув",
            "съприч",
            "милосърд",
            "солидар",
            "доброт",
            "спас",
            "утех",
            "заедно",
            "човеч",
            "закрил",
        ],
    },
]


MOTIF_BY_ID = {motif["id"]: motif for motif in MOTIFS}
TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁёЍѝ0-9]+", re.UNICODE)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def tokenize(text: str) -> list[str]:
    tokens = []
    for match in TOKEN_RE.finditer(text.lower()):
        token = match.group(0)
        if len(token) < 3:
            continue
        if token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def parse_work(folder: Path) -> dict:
    number_str, _, folder_name = folder.name.partition(". ")
    work_id = int(number_str)

    opisanie = read_text(folder / "opisanie.txt")
    motivi = read_text(folder / "motivi.txt")
    analiz = read_text(folder / "analiz.txt")

    opisanie_lines = [line.strip() for line in opisanie.splitlines() if line.strip()]
    title = opisanie_lines[0].split(":", 1)[1].strip() if opisanie_lines and ":" in opisanie_lines[0] else folder_name
    author = opisanie_lines[1].split(":", 1)[1].strip() if len(opisanie_lines) > 1 and ":" in opisanie_lines[1] else "Неуточнен автор"
    description = " ".join(opisanie_lines[2:]).strip()

    motif_lines = []
    for line in motivi.splitlines():
        stripped = line.strip()
        if stripped.startswith("-"):
            motif_lines.append(stripped.lstrip("-").strip())

    analysis_lines = []
    for line in analiz.splitlines():
        stripped = line.strip()
        if stripped == "Източници:" or stripped.startswith("-"):
            break
        if stripped:
            analysis_lines.append(stripped)
    analysis = " ".join(analysis_lines)

    combined_text = " ".join([description, " ".join(motif_lines), analysis])

    return {
        "id": work_id,
        "folder": folder.name,
        "title": title,
        "author": author,
        "description": description,
        "motif_bullets": motif_lines,
        "analysis": analysis,
        "combined_text": combined_text,
        "tokens": tokenize(combined_text),
    }


def score_motifs(work: dict) -> dict:
    description_tokens = tokenize(work["description"])
    analysis_tokens = tokenize(work["analysis"])
    bullet_tokens = tokenize(" ".join(work["motif_bullets"]))
    title_tokens = tokenize(work["title"])

    def source_hits(tokens: list[str], stems: list[str]) -> tuple[int, list[str]]:
        count = 0
        hits = []
        for token in tokens:
            for stem in stems:
                if token.startswith(stem):
                    count += 1
                    hits.append(token)
                    break
        return count, hits

    raw_scores = {}
    motif_hits = {}
    for motif in MOTIFS:
        stems = motif["keywords"]
        desc_count, desc_hits = source_hits(description_tokens, stems)
        analysis_count, analysis_hits = source_hits(analysis_tokens, stems)
        bullet_count, bullet_hits = source_hits(bullet_tokens, stems)
        title_count, title_hits = source_hits(title_tokens, stems)

        score = (
            desc_count * 1.8
            + analysis_count * 1.3
            + bullet_count * 3.4
            + title_count * 2.0
        )

        if motif["id"] == "homeland_memory" and work["author"] in {"Иван Вазов", "Христо Ботев", "Димитър Талев"}:
            score += 0.5
        if motif["id"] == "love" and work["author"] in {"Христо Фотев", "Петя Дубарова", "Емилиян Станев"}:
            score += 0.5
        if motif["id"] == "labor_creativity" and any(word in work["title"].lower() for word in ["колелетата", "георг хених", "честен кръст"]):
            score += 0.8

        raw_scores[motif["id"]] = score
        motif_hits[motif["id"]] = sorted(set(desc_hits + analysis_hits + bullet_hits + title_hits))[:12]

    total = sum(raw_scores.values()) or 1.0
    normalized = {key: value / total for key, value in raw_scores.items()}

    dominance = max(normalized.values()) if normalized else 0.0
    dominant_motif = max(normalized.keys(), key=lambda key: normalized[key]) if normalized else MOTIFS[0]["id"]

    return {
        "scores": normalized,
        "raw_scores": raw_scores,
        "dominant_motif": dominant_motif,
        "dominance": dominance,
        "hits": motif_hits,
    }


def build_tfidf_vectors(works: list[dict]) -> dict[int, dict[str, float]]:
    token_counts = {work["id"]: Counter(work["tokens"]) for work in works}
    doc_frequency = Counter()
    for counts in token_counts.values():
        doc_frequency.update(counts.keys())

    doc_total = len(works)
    vectors = {}
    for work in works:
        counts = token_counts[work["id"]]
        max_tf = max(counts.values()) if counts else 1
        vector = {}
        for token, count in counts.items():
            if doc_frequency[token] < 2:
                continue
            tf = count / max_tf
            idf = math.log((1 + doc_total) / (1 + doc_frequency[token])) + 1
            vector[token] = tf * idf
        vectors[work["id"]] = vector
    return vectors


def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    shared = set(vec_a).intersection(vec_b)
    dot = sum(vec_a[token] * vec_b[token] for token in shared)
    norm_a = math.sqrt(sum(value * value for value in vec_a.values()))
    norm_b = math.sqrt(sum(value * value for value in vec_b.values()))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def join_labels(labels: list[str]) -> str:
    if not labels:
        return "общи тематични ядра"
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} и {labels[1]}"
    return ", ".join(labels[:-1]) + f" и {labels[-1]}"


def build_reason(work_a: dict, work_b: dict, top_motifs: list[tuple[str, float]], weight: float) -> str:
    motif_labels = [MOTIF_BY_ID[motif_id]["label"].lower() for motif_id, score in top_motifs if score > 0.02][:3]
    motif_phrases = [MOTIF_BY_ID[motif_id]["hover_phrase"] for motif_id, score in top_motifs if score > 0.02][:2]

    if not motif_labels:
        return f"Връзката между {work_a['title']} и {work_b['title']} е по-скоро слаба и идва от общ литературен фон, а не от ясно изразен водещ мотив."

    dominant_a = MOTIF_BY_ID[work_a["motif_profile"]["dominant_motif"]]["label"].lower()
    dominant_b = MOTIF_BY_ID[work_b["motif_profile"]["dominant_motif"]]["label"].lower()

    if weight >= 0.62:
        return (
            f"Връзката е силна заради мотивите за {join_labels(motif_labels)}, като {work_a['title']} и {work_b['title']} се срещат най-ясно през {join_labels(motif_phrases)}."
        )
    if weight >= 0.38:
        return (
            f"Творбите корелират най-вече в полето на {join_labels(motif_labels)}, но {work_a['title']} го развива по-близо до {dominant_a}, а {work_b['title']} - по-близо до {dominant_b}."
        )
    return (
        f"Връзката е по-слаба и минава главно през {join_labels(motif_labels)}, макар че {work_a['title']} и {work_b['title']} ги разглеждат в различен контекст."
    )


def build_edges(works: list[dict], tfidf_vectors: dict[int, dict[str, float]]) -> list[dict]:
    edges = []
    works_by_id = {work["id"]: work for work in works}
    for work_a, work_b in itertools.combinations(works, 2):
        motif_vec_a = work_a["motif_profile"]["scores"]
        motif_vec_b = work_b["motif_profile"]["scores"]

        motif_cos = cosine_similarity(motif_vec_a, motif_vec_b)
        text_cos = cosine_similarity(tfidf_vectors[work_a["id"]], tfidf_vectors[work_b["id"]])

        shared_motifs = []
        for motif in MOTIFS:
            motif_id = motif["id"]
            overlap = min(motif_vec_a[motif_id], motif_vec_b[motif_id])
            shared_motifs.append((motif_id, overlap))
        shared_motifs.sort(key=lambda item: item[1], reverse=True)

        overlap_bonus = sum(score for _, score in shared_motifs[:3])
        overlap_feature = min(1.0, overlap_bonus / 0.5)
        weight = max(0.0, min(1.0, motif_cos * 0.55 + text_cos * 0.20 + overlap_feature * 0.25))

        primary_motif = shared_motifs[0][0]
        edge = {
            "source": work_a["id"],
            "target": work_b["id"],
            "source_title": work_a["title"],
            "target_title": work_b["title"],
            "weight": round(weight, 4),
            "motif_cosine": round(motif_cos, 4),
            "text_cosine": round(text_cos, 4),
            "primary_motif": primary_motif,
            "top_motifs": [
                {
                    "id": motif_id,
                    "label": MOTIF_BY_ID[motif_id]["label"],
                    "score": round(score, 4),
                    "color": MOTIF_BY_ID[motif_id]["color"],
                }
                for motif_id, score in shared_motifs[:4]
            ],
        }
        edge["reason"] = build_reason(work_a, work_b, shared_motifs[:3], weight)
        edges.append(edge)

    edges.sort(key=lambda edge: edge["weight"], reverse=True)
    return edges


def build_layout(works: list[dict], edges: list[dict]) -> tuple[dict[str, tuple[float, float]], dict[int, tuple[float, float]]]:
    motif_anchors = {}
    radius = 360.0
    center_x = 0.0
    center_y = 0.0
    motif_count = len(MOTIFS)
    for index, motif in enumerate(MOTIFS):
        angle = -math.pi / 2 + (2 * math.pi * index / motif_count)
        motif_anchors[motif["id"]] = (center_x + radius * math.cos(angle), center_y + radius * math.sin(angle))

    random.seed(42)
    positions = {}
    velocities = {}
    targets = {}
    for work in works:
        scores = work["motif_profile"]["scores"]
        total = sum(scores.values()) or 1.0
        tx = sum(motif_anchors[motif_id][0] * score for motif_id, score in scores.items()) / total
        ty = sum(motif_anchors[motif_id][1] * score for motif_id, score in scores.items()) / total
        dominance = work["motif_profile"]["dominance"]
        scale = 0.65 + dominance * 0.75
        tx *= scale
        ty *= scale
        targets[work["id"]] = (tx, ty)
        positions[work["id"]] = (
            tx + random.uniform(-25, 25),
            ty + random.uniform(-25, 25),
        )
        velocities[work["id"]] = (0.0, 0.0)

    adjacency = {}
    for edge in edges:
        adjacency.setdefault(edge["source"], []).append(edge)
        adjacency.setdefault(edge["target"], []).append(edge)

    work_ids = [work["id"] for work in works]

    for _ in range(420):
        forces = {work_id: [0.0, 0.0] for work_id in work_ids}

        for idx, work_id_a in enumerate(work_ids):
            ax, ay = positions[work_id_a]
            for work_id_b in work_ids[idx + 1 :]:
                bx, by = positions[work_id_b]
                dx = ax - bx
                dy = ay - by
                distance_sq = dx * dx + dy * dy + 0.01
                distance = math.sqrt(distance_sq)
                repulsion = 1250.0 / distance_sq
                fx = repulsion * dx / distance
                fy = repulsion * dy / distance
                forces[work_id_a][0] += fx
                forces[work_id_a][1] += fy
                forces[work_id_b][0] -= fx
                forces[work_id_b][1] -= fy

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            sx, sy = positions[source]
            tx, ty = positions[target]
            dx = tx - sx
            dy = ty - sy
            distance = math.sqrt(dx * dx + dy * dy) + 0.01
            desired = 260.0 - edge["weight"] * 180.0
            spring = (distance - desired) * 0.018 * (0.4 + edge["weight"])
            fx = spring * dx / distance
            fy = spring * dy / distance
            forces[source][0] += fx
            forces[source][1] += fy
            forces[target][0] -= fx
            forces[target][1] -= fy

        for work in works:
            work_id = work["id"]
            px, py = positions[work_id]
            tx, ty = targets[work_id]
            forces[work_id][0] += (tx - px) * 0.045
            forces[work_id][1] += (ty - py) * 0.045
            forces[work_id][0] += (0.0 - px) * 0.0015
            forces[work_id][1] += (0.0 - py) * 0.0015

        for work_id in work_ids:
            vx, vy = velocities[work_id]
            fx, fy = forces[work_id]
            vx = (vx + fx) * 0.82
            vy = (vy + fy) * 0.82
            px, py = positions[work_id]
            px += vx
            py += vy
            px = max(-520, min(520, px))
            py = max(-430, min(430, py))
            positions[work_id] = (px, py)
            velocities[work_id] = (vx, vy)

    return motif_anchors, positions


def write_database(works: list[dict], edges: list[dict]) -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.executescript(
        """
        CREATE TABLE works (
            id INTEGER PRIMARY KEY,
            folder TEXT NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            description TEXT NOT NULL,
            analysis TEXT NOT NULL,
            dominant_motif_id TEXT NOT NULL,
            dominant_motif_score REAL NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL
        );

        CREATE TABLE motifs (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            color TEXT NOT NULL,
            description TEXT NOT NULL,
            hover_phrase TEXT NOT NULL
        );

        CREATE TABLE work_motif_scores (
            work_id INTEGER NOT NULL,
            motif_id TEXT NOT NULL,
            score REAL NOT NULL,
            keyword_hits TEXT NOT NULL,
            PRIMARY KEY (work_id, motif_id),
            FOREIGN KEY (work_id) REFERENCES works (id),
            FOREIGN KEY (motif_id) REFERENCES motifs (id)
        );

        CREATE TABLE pair_links (
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            weight REAL NOT NULL,
            motif_cosine REAL NOT NULL,
            text_cosine REAL NOT NULL,
            primary_motif_id TEXT NOT NULL,
            top_motifs_json TEXT NOT NULL,
            reason TEXT NOT NULL,
            PRIMARY KEY (source_id, target_id),
            FOREIGN KEY (source_id) REFERENCES works (id),
            FOREIGN KEY (target_id) REFERENCES works (id),
            FOREIGN KEY (primary_motif_id) REFERENCES motifs (id)
        );
        """
    )

    cursor.executemany(
        "INSERT INTO motifs (id, label, color, description, hover_phrase) VALUES (?, ?, ?, ?, ?)",
        [
            (
                motif["id"],
                motif["label"],
                motif["color"],
                motif["description"],
                motif["hover_phrase"],
            )
            for motif in MOTIFS
        ],
    )

    cursor.executemany(
        """
        INSERT INTO works (
            id, folder, title, author, description, analysis,
            dominant_motif_id, dominant_motif_score, x, y
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                work["id"],
                work["folder"],
                work["title"],
                work["author"],
                work["description"],
                work["analysis"],
                work["motif_profile"]["dominant_motif"],
                round(work["motif_profile"]["scores"][work["motif_profile"]["dominant_motif"]], 6),
                work["x"],
                work["y"],
            )
            for work in works
        ],
    )

    score_rows = []
    for work in works:
        for motif in MOTIFS:
            motif_id = motif["id"]
            score_rows.append(
                (
                    work["id"],
                    motif_id,
                    round(work["motif_profile"]["scores"][motif_id], 6),
                    json.dumps(work["motif_profile"]["hits"][motif_id], ensure_ascii=False),
                )
            )
    cursor.executemany(
        "INSERT INTO work_motif_scores (work_id, motif_id, score, keyword_hits) VALUES (?, ?, ?, ?)",
        score_rows,
    )

    cursor.executemany(
        """
        INSERT INTO pair_links (
            source_id, target_id, weight, motif_cosine, text_cosine,
            primary_motif_id, top_motifs_json, reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                edge["source"],
                edge["target"],
                edge["weight"],
                edge["motif_cosine"],
                edge["text_cosine"],
                edge["primary_motif"],
                json.dumps(edge["top_motifs"], ensure_ascii=False),
                edge["reason"],
            )
            for edge in edges
        ],
    )

    connection.commit()
    connection.close()


def write_csvs(works: list[dict], edges: list[dict]) -> None:
    with WORKS_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "id",
                "folder",
                "title",
                "author",
                "dominant_motif",
                "dominant_score",
                "x",
                "y",
                "description",
            ]
        )
        for work in works:
            writer.writerow(
                [
                    work["id"],
                    work["folder"],
                    work["title"],
                    work["author"],
                    MOTIF_BY_ID[work["motif_profile"]["dominant_motif"]]["label"],
                    round(work["motif_profile"]["scores"][work["motif_profile"]["dominant_motif"]], 4),
                    work["x"],
                    work["y"],
                    work["description"],
                ]
            )

    with WORK_MOTIFS_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["work_id", "title", "motif_id", "motif_label", "score", "keyword_hits"])
        for work in works:
            for motif in MOTIFS:
                motif_id = motif["id"]
                writer.writerow(
                    [
                        work["id"],
                        work["title"],
                        motif_id,
                        motif["label"],
                        round(work["motif_profile"]["scores"][motif_id], 4),
                        ", ".join(work["motif_profile"]["hits"][motif_id]),
                    ]
                )

    with EDGES_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "source_id",
                "source_title",
                "target_id",
                "target_title",
                "weight",
                "primary_motif",
                "top_motifs",
                "reason",
            ]
        )
        for edge in edges:
            writer.writerow(
                [
                    edge["source"],
                    edge["source_title"],
                    edge["target"],
                    edge["target_title"],
                    edge["weight"],
                    MOTIF_BY_ID[edge["primary_motif"]]["label"],
                    "; ".join(f"{item['label']} ({item['score']})" for item in edge["top_motifs"]),
                    edge["reason"],
                ]
            )


def write_motifs_markdown() -> None:
    lines = ["# Главни мотиви", ""]
    for motif in MOTIFS:
        lines.append(f"- {motif['label']} (`{motif['color']}`): {motif['description']}")
    MOTIFS_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_graph_payload(works: list[dict], edges: list[dict], motif_anchors: dict[str, tuple[float, float]]) -> dict:
    works_payload = []
    for work in works:
        sorted_motifs = sorted(
            (
                {
                    "id": motif_id,
                    "label": MOTIF_BY_ID[motif_id]["label"],
                    "score": round(score, 4),
                    "color": MOTIF_BY_ID[motif_id]["color"],
                }
                for motif_id, score in work["motif_profile"]["scores"].items()
            ),
            key=lambda item: item["score"],
            reverse=True,
        )
        works_payload.append(
            {
                "id": work["id"],
                "title": work["title"],
                "author": work["author"],
                "label": f"{work['id']:02d}. {work['title']}",
                "description": work["description"],
                "analysis": work["analysis"],
                "dominant_motif": work["motif_profile"]["dominant_motif"],
                "dominant_label": MOTIF_BY_ID[work["motif_profile"]["dominant_motif"]]["label"],
                "dominance": round(work["motif_profile"]["dominance"], 4),
                "color": MOTIF_BY_ID[work["motif_profile"]["dominant_motif"]]["color"],
                "x": work["x"],
                "y": work["y"],
                "radius": round(10 + 18 * work["motif_profile"]["dominance"], 2),
                "motifs": sorted_motifs,
            }
        )

    payload = {
        "meta": {
            "work_count": len(works),
            "edge_count": len(edges),
            "undirected_pairs": len(edges),
            "layout": {
                "type": "motif-anchored-force-layout",
                "description": "Възлите започват от претеглен център на мотивите, после се преместват от сили на отблъскване, привличане по ребрата и връщане към доминиращите мотивни анкери.",
            },
        },
        "motifs": [
            {
                "id": motif["id"],
                "label": motif["label"],
                "color": motif["color"],
                "description": motif["description"],
                "hover_phrase": motif["hover_phrase"],
                "anchor": {"x": round(motif_anchors[motif["id"]][0], 2), "y": round(motif_anchors[motif["id"]][1], 2)},
            }
            for motif in MOTIFS
        ],
        "works": works_payload,
        "edges": edges,
    }
    return payload


def build_html(graph_data: dict) -> str:
    data_json = json.dumps(graph_data, ensure_ascii=False).replace("</script>", "<\\/script>")
    return f"""<!doctype html>
<html lang="bg">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BEL Knowledge Graph</title>
  <style>
    :root {{
      --bg: #fbf7ef;
      --panel: rgba(255, 252, 246, 0.88);
      --ink: #1f1a17;
      --muted: #6d625b;
      --line: rgba(63, 53, 46, 0.12);
      --shadow: 0 18px 48px rgba(67, 52, 36, 0.14);
      --font-display: Georgia, "Times New Roman", serif;
      --font-ui: "Avenir Next", "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--font-ui);
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(255, 214, 10, 0.18), transparent 24%),
        radial-gradient(circle at bottom right, rgba(0, 184, 212, 0.16), transparent 22%),
        linear-gradient(160deg, #fdf7ef 0%, #f7f2ea 40%, #f3ede6 100%);
      min-height: 100vh;
    }}
    .shell {{
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr) 360px;
      gap: 18px;
      padding: 18px;
      min-height: 100vh;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }}
    .left, .right {{ padding: 18px; overflow: auto; }}
    .center {{ padding: 10px; position: relative; overflow: hidden; }}
    h1, h2, h3 {{ font-family: var(--font-display); margin: 0 0 10px; }}
    h1 {{ font-size: 28px; line-height: 1.1; }}
    h2 {{ font-size: 18px; }}
    p, li, label, input, select, button {{ font-size: 14px; line-height: 1.45; }}
    .muted {{ color: var(--muted); }}
    .stat {{ margin: 4px 0; font-size: 13px; color: var(--muted); }}
    .controls {{ display: grid; gap: 14px; margin: 18px 0 22px; }}
    .control {{ display: grid; gap: 8px; }}
    input[type="search"], select, input[type="range"] {{ width: 100%; }}
    input[type="search"], select {{
      border: 1px solid rgba(63, 53, 46, 0.14);
      background: rgba(255,255,255,0.85);
      border-radius: 12px;
      padding: 10px 12px;
      font: inherit;
      color: inherit;
    }}
    input[type="range"] {{ accent-color: #1e88e5; }}
    .legend {{ display: grid; gap: 8px; }}
    .legend-item {{ display: grid; grid-template-columns: 14px minmax(0, 1fr); gap: 10px; align-items: start; }}
    .legend-swatch {{ width: 14px; height: 14px; border-radius: 999px; margin-top: 3px; }}
    .legend-item strong {{ display: block; font-size: 13px; }}
    .legend-item span {{ display: block; font-size: 12px; color: var(--muted); }}
    .canvas-wrap {{
      position: absolute;
      inset: 10px;
      border-radius: 18px;
      background:
        radial-gradient(circle at center, rgba(255,255,255,0.78), rgba(255,255,255,0.48)),
        linear-gradient(180deg, rgba(255,255,255,0.68), rgba(248,243,235,0.9));
      border: 1px solid var(--line);
      overflow: hidden;
    }}
    svg {{ width: 100%; height: 100%; display: block; }}
    .edge {{ stroke-linecap: round; transition: opacity 0.2s ease; }}
    .edge.dimmed {{ opacity: 0.06 !important; }}
    .node-label {{ font: 12px var(--font-ui); fill: rgba(33, 27, 23, 0.86); pointer-events: none; }}
    .motif-label {{ font: 12px var(--font-ui); fill: rgba(70, 58, 50, 0.72); letter-spacing: 0.03em; }}
    .node {{ cursor: pointer; transition: opacity 0.2s ease; }}
    .node.dimmed {{ opacity: 0.16; }}
    .tooltip {{
      position: absolute;
      max-width: 360px;
      pointer-events: none;
      background: rgba(35, 28, 24, 0.92);
      color: #fffaf4;
      padding: 10px 12px;
      border-radius: 12px;
      box-shadow: 0 18px 50px rgba(0,0,0,0.24);
      font-size: 12px;
      line-height: 1.45;
      opacity: 0;
      transform: translateY(6px);
      transition: opacity 0.16s ease, transform 0.16s ease;
      z-index: 5;
    }}
    .tooltip.visible {{ opacity: 1; transform: translateY(0); }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }}
    .chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.72);
      border: 1px solid rgba(63,53,46,0.12);
      font-size: 12px;
    }}
    .chip-dot {{ width: 10px; height: 10px; border-radius: 999px; }}
    .connections {{ display: grid; gap: 8px; margin-top: 16px; }}
    .connection {{
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(255,255,255,0.7);
      border: 1px solid rgba(63,53,46,0.1);
    }}
    .connection strong {{ display: block; font-size: 13px; margin-bottom: 4px; }}
    .connection span {{ display: block; font-size: 12px; color: var(--muted); }}
    .empty {{ color: var(--muted); font-size: 13px; }}
    @media (max-width: 1320px) {{
      .shell {{ grid-template-columns: 280px minmax(0, 1fr); }}
      .right {{ grid-column: 1 / -1; min-height: 320px; }}
    }}
    @media (max-width: 980px) {{
      .shell {{ grid-template-columns: 1fr; }}
      .center {{ min-height: 72vh; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <aside class="panel left">
      <h1>BEL Graph</h1>
      <p class="muted">29 произведения, 406 връзки и 12 главни мотива в една мотивно-анкерирана карта.</p>
      <div class="stat" id="stats-text"></div>
      <div class="controls">
        <div class="control">
          <label for="search">Търсене на произведение</label>
          <input id="search" type="search" placeholder="Напр. Паисий, Ноев ковчег...">
        </div>
        <div class="control">
          <label for="motif-filter">Филтър по мотив</label>
          <select id="motif-filter"></select>
        </div>
        <div class="control">
          <label for="weight-filter">Минимална сила на връзката: <strong id="weight-value"></strong></label>
          <input id="weight-filter" type="range" min="0" max="1" step="0.01" value="0.28">
        </div>
      </div>
      <h2>Главни мотиви</h2>
      <div id="legend" class="legend"></div>
    </aside>

    <main class="panel center">
      <div class="canvas-wrap">
        <svg id="graph" viewBox="-620 -500 1240 1000" preserveAspectRatio="xMidYMid meet">
          <g id="motif-layer"></g>
          <g id="edge-layer"></g>
          <g id="node-layer"></g>
          <g id="label-layer"></g>
        </svg>
      </div>
      <div id="tooltip" class="tooltip"></div>
    </main>

    <aside class="panel right">
      <h2 id="detail-title">Избери произведение</h2>
      <p id="detail-meta" class="muted">Щракни върху възел, за да видиш описание, мотивен профил и най-силни връзки.</p>
      <div id="detail-description"></div>
      <div id="detail-chips" class="chips"></div>
      <div id="detail-analysis" class="muted"></div>
      <h3 style="margin-top: 18px;">Най-силни връзки</h3>
      <div id="connections" class="connections"><div class="empty">Още няма избран възел.</div></div>
    </aside>
  </div>

  <script id="graph-data" type="application/json">{data_json}</script>
  <script>
    const graphData = JSON.parse(document.getElementById('graph-data').textContent);
    const motifFilter = document.getElementById('motif-filter');
    const weightFilter = document.getElementById('weight-filter');
    const weightValue = document.getElementById('weight-value');
    const searchInput = document.getElementById('search');
    const statsText = document.getElementById('stats-text');
    const legend = document.getElementById('legend');
    const motifLayer = document.getElementById('motif-layer');
    const edgeLayer = document.getElementById('edge-layer');
    const nodeLayer = document.getElementById('node-layer');
    const labelLayer = document.getElementById('label-layer');
    const tooltip = document.getElementById('tooltip');

    const detailTitle = document.getElementById('detail-title');
    const detailMeta = document.getElementById('detail-meta');
    const detailDescription = document.getElementById('detail-description');
    const detailChips = document.getElementById('detail-chips');
    const detailAnalysis = document.getElementById('detail-analysis');
    const connectionsBox = document.getElementById('connections');

    const works = graphData.works;
    const worksById = new Map(works.map(work => [work.id, work]));
    const edges = graphData.edges;
    const selectedState = {{ workId: null }};

    statsText.textContent = `${{graphData.meta.work_count}} произведения · ${{graphData.meta.edge_count}} пълни двойки · мотивно-анкериран force layout`;

    motifFilter.innerHTML = '<option value="all">Всички мотиви</option>' + graphData.motifs.map(motif => `<option value="${{motif.id}}">${{motif.label}}</option>`).join('');
    weightValue.textContent = Number(weightFilter.value).toFixed(2);

    legend.innerHTML = graphData.motifs.map(motif => `
      <div class="legend-item">
        <div class="legend-swatch" style="background:${{motif.color}}"></div>
        <div>
          <strong>${{motif.label}}</strong>
          <span>${{motif.description}}</span>
        </div>
      </div>
    `).join('');

    motifLayer.innerHTML = graphData.motifs.map(motif => `
      <g>
        <circle cx="${{motif.anchor.x}}" cy="${{motif.anchor.y}}" r="6" fill="${{motif.color}}" fill-opacity="0.25"></circle>
        <text class="motif-label" x="${{motif.anchor.x}}" y="${{motif.anchor.y - 14}}" text-anchor="middle">${{motif.label}}</text>
      </g>
    `).join('');

    const edgeElements = edges.map(edge => {{
      const primary = graphData.motifs.find(motif => motif.id === edge.primary_motif);
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('class', 'edge');
      line.dataset.source = edge.source;
      line.dataset.target = edge.target;
      line.dataset.primaryMotif = edge.primary_motif;
      line.dataset.weight = edge.weight;
      line.setAttribute('stroke', primary.color);
      line.setAttribute('stroke-opacity', String(0.08 + edge.weight * 0.66));
      line.setAttribute('stroke-width', String(0.8 + edge.weight * 6.5));
      const source = worksById.get(edge.source);
      const target = worksById.get(edge.target);
      line.setAttribute('x1', source.x);
      line.setAttribute('y1', source.y);
      line.setAttribute('x2', target.x);
      line.setAttribute('y2', target.y);
      line.addEventListener('mousemove', event => showTooltip(event, `<strong>${{source.title}}</strong> ↔ <strong>${{target.title}}</strong><br>${{edge.reason}}`));
      line.addEventListener('mouseleave', hideTooltip);
      edgeLayer.appendChild(line);
      return {{ edge, element: line }};
    }});

    const nodeElements = works.map(work => {{
      const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      group.setAttribute('class', 'node');
      group.dataset.id = work.id;

      const halo = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      halo.setAttribute('cx', work.x);
      halo.setAttribute('cy', work.y);
      halo.setAttribute('r', work.radius + 6);
      halo.setAttribute('fill', work.color);
      halo.setAttribute('fill-opacity', '0.12');
      group.appendChild(halo);

      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', work.x);
      circle.setAttribute('cy', work.y);
      circle.setAttribute('r', work.radius);
      circle.setAttribute('fill', work.color);
      circle.setAttribute('stroke', 'rgba(38, 29, 23, 0.55)');
      circle.setAttribute('stroke-width', '1.4');
      group.appendChild(circle);

      group.addEventListener('mousemove', event => showTooltip(event, `<strong>${{work.title}}</strong><br>${{work.author}}<br>Доминиращ мотив: ${{work.dominant_label}}`));
      group.addEventListener('mouseleave', hideTooltip);
      group.addEventListener('click', () => selectWork(work.id));
      nodeLayer.appendChild(group);

      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('class', 'node-label');
      label.setAttribute('x', work.x);
      label.setAttribute('y', work.y + work.radius + 16);
      label.setAttribute('text-anchor', 'middle');
      label.textContent = work.title;
      labelLayer.appendChild(label);

      return {{ work, group, circle, label }};
    }});

    function formatMotifScore(score) {{
      return `${{(score * 100).toFixed(1)}}%`;
    }}

    function selectWork(workId) {{
      selectedState.workId = workId;
      const work = worksById.get(workId);
      if (!work) return;

      detailTitle.textContent = `${{String(work.id).padStart(2, '0')}}. ${{work.title}}`;
      detailMeta.textContent = `${{work.author}} · Доминиращ мотив: ${{work.dominant_label}} · Интензитет: ${{formatMotifScore(work.dominance)}}`;
      detailDescription.innerHTML = `<p>${{work.description}}</p>`;
      detailChips.innerHTML = work.motifs.slice(0, 6).map(motif => `
        <div class="chip">
          <span class="chip-dot" style="background:${{motif.color}}"></span>
          <span>${{motif.label}} · ${{formatMotifScore(motif.score)}}</span>
        </div>
      `).join('');
      detailAnalysis.innerHTML = `<p>${{work.analysis}}</p>`;

      const related = edges
        .filter(edge => edge.source === workId || edge.target === workId)
        .sort((a, b) => b.weight - a.weight)
        .slice(0, 8);

      if (!related.length) {{
        connectionsBox.innerHTML = '<div class="empty">Няма достатъчно данни за връзки.</div>';
      }} else {{
        connectionsBox.innerHTML = related.map(edge => {{
          const otherId = edge.source === workId ? edge.target : edge.source;
          const other = worksById.get(otherId);
          return `
            <div class="connection">
              <strong>${{other.title}}</strong>
              <span>Сила: ${{edge.weight.toFixed(2)}} · Водещ мотив: ${{edge.top_motifs[0].label}}</span>
              <span>${{edge.reason}}</span>
            </div>
          `;
        }}).join('');
      }}

      nodeElements.forEach(item => {{
        item.circle.setAttribute('stroke-width', item.work.id === workId ? '3.6' : '1.4');
        item.circle.setAttribute('stroke', item.work.id === workId ? '#111' : 'rgba(38, 29, 23, 0.55)');
      }});
    }}

    function showTooltip(event, content) {{
      tooltip.innerHTML = content;
      tooltip.classList.add('visible');
      const bounds = tooltip.parentElement.getBoundingClientRect();
      tooltip.style.left = `${{event.clientX - bounds.left + 16}}px`;
      tooltip.style.top = `${{event.clientY - bounds.top + 16}}px`;
    }}

    function hideTooltip() {{
      tooltip.classList.remove('visible');
    }}

    function updateGraph() {{
      const search = searchInput.value.trim().toLowerCase();
      const motifId = motifFilter.value;
      const minWeight = Number(weightFilter.value);
      weightValue.textContent = minWeight.toFixed(2);

      const visibleWorks = new Set();
      works.forEach(work => {{
        const searchOk = !search || work.title.toLowerCase().includes(search) || work.author.toLowerCase().includes(search);
        const motifOk = motifId === 'all' || work.motifs.some(motif => motif.id === motifId && motif.score >= 0.14);
        if (searchOk && motifOk) visibleWorks.add(work.id);
      }});

      edgeElements.forEach(({{ edge, element }}) => {{
        const edgeMotifOk = motifId === 'all' || edge.top_motifs.some(motif => motif.id === motifId && motif.score >= 0.03);
        const visible = edge.weight >= minWeight && edgeMotifOk && visibleWorks.has(edge.source) && visibleWorks.has(edge.target);
        element.style.display = visible ? 'block' : 'none';
        element.classList.toggle('dimmed', selectedState.workId && !(edge.source === selectedState.workId || edge.target === selectedState.workId));
      }});

      nodeElements.forEach(({{ work, group, label }}) => {{
        const visible = visibleWorks.has(work.id);
        group.style.display = visible ? 'block' : 'none';
        label.style.display = visible ? 'block' : 'none';
        const dimmed = selectedState.workId && selectedState.workId !== work.id;
        group.classList.toggle('dimmed', dimmed);
        label.style.opacity = dimmed ? '0.25' : '0.92';
      }});
    }}

    motifFilter.addEventListener('change', updateGraph);
    weightFilter.addEventListener('input', updateGraph);
    searchInput.addEventListener('input', updateGraph);

    selectWork(1);
    updateGraph();
  </script>
</body>
</html>
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    work_dirs = sorted(
        [path for path in ROOT.iterdir() if path.is_dir() and re.match(r"^\d+\. ", path.name) and (path / "opisanie.txt").exists()],
        key=lambda path: int(path.name.split(".", 1)[0]),
    )

    works = [parse_work(folder) for folder in work_dirs]
    for work in works:
        work["motif_profile"] = score_motifs(work)

    tfidf_vectors = build_tfidf_vectors(works)
    edges = build_edges(works, tfidf_vectors)
    motif_anchors, positions = build_layout(works, edges)

    for work in works:
        x, y = positions[work["id"]]
        work["x"] = round(x, 2)
        work["y"] = round(y, 2)

    write_database(works, edges)
    write_csvs(works, edges)
    write_motifs_markdown()

    graph_payload = build_graph_payload(works, edges, motif_anchors)
    JSON_PATH.write_text(json.dumps(graph_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    HTML_PATH.write_text(build_html(graph_payload), encoding="utf-8")

    print(f"Generated graph data for {len(works)} works and {len(edges)} undirected edges.")
    print(f"Database: {DB_PATH}")
    print(f"HTML: {HTML_PATH}")


if __name__ == "__main__":
    main()
