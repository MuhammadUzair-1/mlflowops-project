"""Generate varied synthetic task-priority data for MLflow training."""

import os
import random

from sqlalchemy import create_engine, text

random.seed(42)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://tasks:tasks@localhost:5432/tasks",
)

SUBJECTS = [
    "login service", "checkout process", "payment API", "email delivery",
    "analytics dashboard", "search service", "user profile", "billing system",
    "cache service", "PDF export", "notification worker", "authentication",
    "database migration", "CSV import", "admin portal", "mobile application",
    "reporting service", "customer onboarding", "inventory system",
    "file upload service",
]

TITLES = [
    "Investigate {subject}",
    "Review the latest report about {subject}",
    "Follow up on a request concerning {subject}",
    "Resolve an issue in {subject}",
    "Assess recent changes to {subject}",
    "Check the reported behaviour of {subject}",
    "Work on the next improvements to {subject}",
    "Analyse feedback related to {subject}",
]

IMPACT_TEXT = {
    1: ["one internal user is affected", "a minor inconvenience for one person"],
    2: ["a small group of users is affected", "some users have reported difficulties"],
    3: ["several teams are affected", "a noticeable number of users are affected"],
    4: ["many customers cannot complete their work", "a major customer workflow is affected"],
    5: ["the service is unavailable to almost everyone", "multiple customer operations have stopped"],
}

URGENCY_TEXT = {
    1: ["there is no immediate deadline", "the request can wait"],
    2: ["it would be useful to address this soon", "there is no pressure to finish immediately"],
    3: ["the team would like an update this week", "this should be considered in the current sprint"],
    4: ["the issue needs attention within the next few hours", "the team expects a response today"],
    5: ["the response is needed immediately", "delaying action could cause further disruption"],
}

DEADLINE_TEXT = {
    1: ["the next review is several weeks away", "there is no fixed delivery date"],
    2: ["the target date is next week", "the deadline is within a few days"],
    3: ["the work is expected within 24 hours", "the next release is approaching"],
    4: ["the deadline is within a few hours", "the next deployment is imminent"],
    5: ["the deadline has already been missed", "the issue is affecting today's operations"],
}

WORKAROUND_TEXT = {
    True: ["a temporary workaround is available", "users can continue with an alternative process"],
    False: ["there is currently no practical workaround", "users cannot complete the affected operation another way"],
}


def generate_rows():
    rows = []

    for subject in SUBJECTS:
        for _ in range(30):
            impact = random.randint(1, 5)
            urgency = random.randint(1, 5)
            deadline_pressure = random.randint(1, 5)
            workaround = random.choice([True, False])

            score = (
                0.45 * impact
                + 0.35 * urgency
                + 0.20 * deadline_pressure
                - (0.7 if workaround else 0)
            )

            if score >= 3.7:
                priority = "high"
            elif score >= 2.6:
                priority = "medium"
            else:
                priority = "low"

            title = random.choice(TITLES).format(subject=subject)

            details = [
                random.choice(IMPACT_TEXT[impact]),
                random.choice(URGENCY_TEXT[urgency]),
                random.choice(DEADLINE_TEXT[deadline_pressure]),
                random.choice(WORKAROUND_TEXT[workaround]),
            ]
            random.shuffle(details)

            description = ". ".join(details) + "."

            rows.append({
                "subject_group": subject,
                "title": title,
                "description": description,
                "priority": priority,
            })

    random.shuffle(rows)
    return rows


def main():
    data = generate_rows()
    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ml_training_data (
                id SERIAL PRIMARY KEY,
                subject_group VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                description TEXT,
                priority VARCHAR NOT NULL
            )
        """))

        conn.execute(text("TRUNCATE TABLE ml_training_data RESTART IDENTITY"))

        conn.execute(text("""
            INSERT INTO ml_training_data
                (subject_group, title, description, priority)
            VALUES
                (:subject_group, :title, :description, :priority)
        """), data)

        counts = conn.execute(text("""
            SELECT priority, COUNT(*)
            FROM ml_training_data
            GROUP BY priority
            ORDER BY priority
        """)).fetchall()

    print(f"Generated {len(data)} training examples.")
    print("Class distribution:")
    for priority, count in counts:
        print(f"  {priority}: {count}")


if __name__ == "__main__":
    main()
