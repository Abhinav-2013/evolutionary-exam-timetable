from __future__ import annotations

import argparse
import csv
import json
import random
import time
from datetime import date, timedelta
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

BRANCHES = {
    "CS": "Core CSE",
    "AM": "AI & ML",
    "AD": "AI & Data Science",
    "CB": "CS & Business Systems",
    "IS": "Information Science",
    "CI": "CS & IoT",
}

# Synthetic proposed subjects, per branch and semester. Common subjects are
# intentionally shared, so their enrollment and conflict graph are realistic.
COMMON = {
    3: ["Statistics and Discrete Mathematics", "Computer Organization and Architecture",
        "Object Oriented Java Programming", "Logic Design", "Database Management Systems",
        "Data Structures", "Unix Shell Programming", "Full Stack Web Development"],
    4: ["Linear Algebra and Optimization", "Cryptography", "Theoretical Foundations of Computation",
        "Operating Systems", "Analysis and Design of Algorithms", "Software Engineering",
        "Universal Human Values", "Mobile Application Development"],
    5: ["Object Oriented Modelling", "Data Exploration and Visualization", "Artificial Intelligence",
        "Computer Networks", "Environmental Studies", "Bio-Inspired Systems",
        "Automated Software Testing", "Mini Project"],
    6: ["Cloud Computing", "Big Data Analytics", "Machine Learning",
        "Research Methodology and IPR", "Open Elective", "Major Project Phase 1"],
    7: ["Network Programming", "Management and Entrepreneurship", "Open Elective",
        "Major Project Phase 2", "Indian Knowledge Systems"],
    8: ["Open Elective", "Internship"],
}
SPECIAL = {
    "AM": {3: "Probability and Statistical Methods", 4: "Machine Learning Foundations",
           5: "Deep Learning", 6: "Computer Vision", 7: "Natural Language Processing", 8: "Neural Networks"},
    "AD": {3: "Data Science Foundations", 4: "Data Analytics", 5: "Data Mining",
           6: "Data Engineering", 7: "Big Data Systems", 8: "Data Science Applications"},
    "CB": {3: "Business Fundamentals and Analytics", 4: "Business Information Systems",
           5: "Enterprise Resource Planning", 6: "Business Intelligence", 7: "Digital Business Strategy", 8: "Business Analytics"},
    "IS": {3: "Web Application Development", 4: "Systems Design and Modeling",
           5: "Information Retrieval", 6: "Data Warehousing", 7: "Cloud and Web Services", 8: "Information Security"},
    "CI": {3: "Digital Systems and Embedded Basics", 4: "Microcontrollers and Interfacing",
           5: "Embedded Systems Design", 6: "Internet of Things", 7: "Wireless Sensor Networks", 8: "IoT Security"},
    "CS": {3: "Computer Science Laboratory", 4: "Computer Systems Lab",
           5: "Compiler Design", 6: "Advanced Data Structures", 7: "Software Architecture", 8: "Network Security"},
}
SEMESTERS = range(3, 9)
ROOMS = list(range(201, 221)) + list(range(401, 421))
ROOM_CAPACITY = 60


@dataclass
class Exam:
    key: str
    title: str
    semester: int
    students: list[int]


def parse_sizes(raw: str | None, total: int) -> dict[str, int]:
    if raw:
        result = {}
        for item in raw.split(","):
            branch, count = item.split("=", 1)
            result[branch.strip().upper()] = int(count)
        if set(result) != set(BRANCHES):
            raise ValueError("Provide sizes for exactly CS,AM,AD,CB,IS,CI")
        return result
    if total < 6:
        raise ValueError("At least six students are needed for six branches")
    # Core CSE receives one third; distribute the remainder evenly.
    core = max(1, total // 3)
    rest, remainder = divmod(total - core, 5)
    sizes = {"CS": core}
    for i, branch in enumerate(("AM", "AD", "CB", "IS", "CI")):
        sizes[branch] = rest + (1 if i < remainder else 0)
    return sizes


def build_data(sizes: dict[str, int]) -> tuple[list[str], list[Exam], list[str]]:
    students: list[str] = []
    student_branch: list[str] = []
    student_sem: list[int] = []
    branch_indices: dict[tuple[str, int], list[int]] = defaultdict(list)
    for branch, count in sizes.items():
        for n in range(1, count + 1):
            idx = len(students)
            students.append(f"1BM23{branch}{n:03d}")
            student_branch.append(branch)
            student_sem.append(3 + (n - 1) % 6)
            branch_indices[(branch, student_sem[-1])].append(idx)

    # Shared courses combine same-semester students across all branches.
    exams: list[Exam] = []
    for sem in SEMESTERS:
        titles_to_students: dict[str, set[int]] = defaultdict(set)
        for branch in BRANCHES:
            titles = COMMON[sem] + [SPECIAL[branch][sem]]
            indices = branch_indices[(branch, sem)]
            for title in titles:
                titles_to_students[title].update(indices)
        for title, enrolled in titles_to_students.items():
            key = f"S{sem:02d}-{title}"
            exams.append(Exam(key, title, sem, sorted(enrolled)))
    return students, exams, student_branch


def conflicts(exams: list[Exam], student_count: int) -> list[set[int]]:
    by_student: list[list[int]] = [[] for _ in range(student_count)]
    for i, exam in enumerate(exams):
        for student in exam.students:
            by_student[student].append(i)
    graph = [set() for _ in exams]
    for enrolled_exams in by_student:
        for p, a in enumerate(enrolled_exams):
            for b in enrolled_exams[p + 1:]:
                graph[a].add(b)
                graph[b].add(a)
    return graph


def repair(candidate: list[int], exams: list[Exam], graph: list[set[int]], sessions: int, rng: random.Random) -> list[int]:
    """Repair student conflicts and per-session hall-capacity overloads."""
    result = candidate[:]
    order = sorted(range(len(result)), key=lambda i: (-len(graph[i]), i))
    for i in order:
        used = {result[j] for j in graph[i] if j != i and result[j] >= 0}
        if result[i] in used:
            available = [s for s in range(sessions) if s not in used]
            result[i] = rng.choice(available) if available else rng.randrange(sessions)
    hall_limit = len(ROOMS)
    room_demand = [max(1, (len(ex.students) + ROOM_CAPACITY - 1) // ROOM_CAPACITY) for ex in exams]
    # Move the least-connected exams until each session can be housed.
    for _ in range(len(exams) * sessions):
        loads = [sum(room_demand[i] for i, slot in enumerate(result) if slot == s) for s in range(sessions)]
        overloaded = next((s for s, load in enumerate(loads) if load > hall_limit), None)
        if overloaded is None:
            break
        movable = [i for i, slot in enumerate(result) if slot == overloaded]
        rng.shuffle(movable)
        movable.sort(key=lambda i: (len(graph[i]), -room_demand[i]))
        moved = False
        for i in movable:
            targets = [s for s in range(sessions) if loads[s] + room_demand[i] <= hall_limit and
                       all(result[j] != s for j in graph[i])]
            if targets:
                result[i] = min(targets, key=lambda s: loads[s])
                moved = True
                break
        if not moved:
            break
    return result


def score(candidate: list[int], exams: list[Exam], graph: list[set[int]], sessions: int) -> tuple[int, dict]:
    clashes = sum(1 for i, neighbors in enumerate(graph) for j in neighbors if j > i and candidate[i] == candidate[j])
    by_student: dict[int, list[int]] = defaultdict(list)
    for i, exam in enumerate(exams):
        for student in exam.students:
            by_student[student].append(candidate[i])
    back_to_back = 0
    for assigned in by_student.values():
        slots = sorted(assigned)
        back_to_back += sum(1 for a, b in zip(slots, slots[1:]) if b == a + 1)
    loads = [sum(len(ex.students) for i, ex in enumerate(exams) if candidate[i] == s) for s in range(sessions)]
    room_demand = [max(1, (len(ex.students) + ROOM_CAPACITY - 1) // ROOM_CAPACITY) for ex in exams]
    hall_loads = [sum(room_demand[i] for i in range(len(exams)) if candidate[i] == s) for s in range(sessions)]
    room_overflow = sum(max(0, n - len(ROOMS)) for n in hall_loads)
    mean = sum(loads) / sessions
    imbalance = sum((x - mean) ** 2 for x in loads) // max(1, sessions)
    total = clashes * 1_000_000 + room_overflow * 1_000_000 + back_to_back * 100 + imbalance
    return total, {"hard_conflicts": clashes, "room_overflow": room_overflow, "back_to_back_pairs": back_to_back, "load_imbalance": imbalance, "session_loads": loads, "halls_used_per_session": hall_loads}


def mutate(x: list[int], sessions: int, rng: random.Random) -> list[int]:
    y = x[:]
    count = 1 if len(y) < 2 else rng.randint(1, max(1, len(y) // 15))
    for _ in range(count):
        i = rng.randrange(len(y))
        if rng.random() < 0.35:
            j = rng.randrange(len(y))
            y[i], y[j] = y[j], y[i]
        else:
            y[i] = rng.randrange(sessions)
    return y


def run_ga(exams, graph, sessions, pop_size, generations, rng):
    pop = [[rng.randrange(sessions) for _ in exams] for _ in range(pop_size)]
    pop = [repair(x, exams, graph, sessions, rng) for x in pop]
    best = None
    for _ in range(generations):
        pop.sort(key=lambda x: score(x, exams, graph, sessions)[0])
        if best is None or score(pop[0], exams, graph, sessions)[0] < score(best, exams, graph, sessions)[0]: best = pop[0][:]
        new = pop[:max(1, pop_size // 10)]
        while len(new) < pop_size:
            a, b = rng.choice(pop[:max(2, pop_size // 2)]), rng.choice(pop[:max(2, pop_size // 2)])
            child = [a[i] if rng.random() < .5 else b[i] for i in range(len(exams))]
            if rng.random() < .8: child = mutate(child, sessions, rng)
            new.append(repair(child, exams, graph, sessions, rng))
        pop = new
    return best


def run_es(exams, graph, sessions, pop_size, generations, rng):
    mu = max(2, pop_size // 2)
    pop = [repair([rng.randrange(sessions) for _ in exams], exams, graph, sessions, rng) for _ in range(mu)]
    for _ in range(generations):
        children = [repair(mutate(rng.choice(pop), sessions, rng), exams, graph, sessions, rng) for _ in range(pop_size - mu)]
        pop = sorted(pop + children, key=lambda x: score(x, exams, graph, sessions)[0])[:mu]
    return min(pop, key=lambda x: score(x, exams, graph, sessions)[0])


def run_ep(exams, graph, sessions, pop_size, generations, rng):
    pop = [repair([rng.randrange(sessions) for _ in exams], exams, graph, sessions, rng) for _ in range(pop_size)]
    for _ in range(generations):
        children = [repair(mutate(x, sessions, rng), exams, graph, sessions, rng) for x in pop]
        pool = pop + children
        wins = [0] * len(pool)
        fitness = [score(x, exams, graph, sessions)[0] for x in pool]
        for i in range(len(pool)):
            for _ in range(5):
                j = rng.randrange(len(pool))
                if fitness[i] < fitness[j]: wins[i] += 1
                elif fitness[i] > fitness[j]: wins[j] += 1
        pop = [pool[i] for i in sorted(range(len(pool)), key=lambda k: (-wins[k], fitness[k]))[:pop_size]]
    return min(pop, key=lambda x: score(x, exams, graph, sessions)[0])


ALGORITHMS: dict[str, Callable] = {"GA": run_ga, "ES": run_es, "EP": run_ep}


def assign_rooms(candidate: list[int], exams: list[Exam], sessions: int) -> dict[int, list[str]]:
    assignment: dict[int, list[str]] = {}
    for s in range(sessions):
        room_pos = 0
        for i, exam in enumerate(exams):
            if candidate[i] != s: continue
            needed = max(1, (len(exam.students) + ROOM_CAPACITY - 1) // ROOM_CAPACITY)
            assigned = ROOMS[room_pos:room_pos + needed]
            assignment[i] = [str(r) for r in assigned]
            room_pos += needed
    return assignment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--students", type=int, default=1800)
    parser.add_argument("--branch-sizes", help="Comma-separated branch=count, e.g. CS=600,AM=240,AD=240,CB=240,IS=240,CI=240")
    parser.add_argument("--sessions", type=int, default=12)
    parser.add_argument("--population", type=int, default=50)
    parser.add_argument("--generations", type=int, default=60)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--start-date", default="2026-11-06")
    parser.add_argument("--end-date", default="2026-11-11")
    parser.add_argument("--output", default="output")
    args = parser.parse_args()
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)
    if end_date < start_date:
        raise ValueError("End date must be on or after start date")
    exam_dates = []
    day = start_date
    while day <= end_date:
        if day.weekday() < 5:
            exam_dates.append(day)
        day += timedelta(days=1)
    if not exam_dates:
        raise ValueError("Selected range must include at least one weekday")
    args.sessions = len(exam_dates) * 2
    sizes = parse_sizes(args.branch_sizes, args.students)
    students, exams, _ = build_data(sizes)
    semester_exam_counts = defaultdict(int)
    for exam in exams:
        semester_exam_counts[exam.semester] += 1
    minimum_sessions = max(semester_exam_counts.values())
    if args.sessions < minimum_sessions:
        raise ValueError(f"Selected window provides {args.sessions} sessions, but at least {minimum_sessions} are needed to avoid same-semester student clashes. Choose a longer date range.")
    graph = conflicts(exams, len(students))
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    best_name, best_x, best_score = None, None, None
    for name, algorithm in ALGORITHMS.items():
        rng = random.Random(args.seed)
        start = time.perf_counter()
        candidate = algorithm(exams, graph, args.sessions, args.population, args.generations, rng)
        elapsed = time.perf_counter() - start
        value, detail = score(candidate, exams, graph, args.sessions)
        results.append({"algorithm": name, "fitness": value, **detail, "runtime_seconds": round(elapsed, 3)})
        if best_score is None or (detail["hard_conflicts"], detail["room_overflow"], detail["back_to_back_pairs"], detail["load_imbalance"]) < best_score:
            best_name, best_x, best_score = name, candidate, (detail["hard_conflicts"], detail["room_overflow"], detail["back_to_back_pairs"], detail["load_imbalance"])

    rooms = assign_rooms(best_x, exams, args.sessions)
    with (out / "timetable.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["session", "date", "weekday", "time", "semester", "course", "enrollment", "rooms", "synthetic_student_usns"])
        for i, exam in enumerate(exams):
            slot = best_x[i]
            exam_day = exam_dates[slot // 2]
            time_label = "08:00 AM to 09:30 AM" if slot % 2 == 0 else "12:00 PM to 01:30 PM"
            writer.writerow([slot + 1, exam_day.isoformat(), exam_day.strftime("%A"), time_label, exam.semester, exam.title, len(exam.students), ";".join(rooms.get(i, [])), ";".join(students[s] for s in exam.students)])
    with (out / "algorithm_comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader(); writer.writerows(results)
    summary = {"best_algorithm": best_name, "best_fitness": score(best_x, exams, graph, args.sessions)[0], "students": len(students), "branch_sizes": sizes,
               "exams": len(exams), "sessions": args.sessions, "rooms_per_session": len(ROOMS), "room_capacity": ROOM_CAPACITY,
               "population": args.population, "generations": args.generations, "seed": args.seed, "comparison": results}
    summary["start_date"] = start_date.isoformat()
    summary["end_date"] = end_date.isoformat()
    summary["exam_dates"] = [d.isoformat() for d in exam_dates]
    (out / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"\nTimetable and comparison saved in: {out.resolve()}")


if __name__ == "__main__":
    main()
