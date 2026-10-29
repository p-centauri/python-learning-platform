from .content import catalog
from .database import SessionLocal
from .models import CurriculumVersion, Lesson, Module, Track


def seed(db):
    data = catalog()
    db.merge(CurriculumVersion(id=data["version"], title="Forge / Founding curriculum"))
    db.flush()
    for position, track in enumerate(data["tracks"]):
        db.merge(
            Track(
                id=track["id"],
                version_id=data["version"],
                title=track["title"],
                description=track["description"],
                position=position,
            )
        )
    db.flush()
    for position, module in enumerate(data["modules"]):
        db.merge(
            Module(id=module["id"], track_id=module["track_id"], title=module["title"], position=position)
        )
    db.flush()
    for lesson in data["lessons"]:
        db.merge(
            Lesson(
                id=lesson["id"],
                module_id=lesson["module_id"],
                title=lesson["title"],
                skill=lesson["skill"],
                minutes=lesson["minutes"],
                content_path=lesson["path"],
            )
        )
    db.flush()


if __name__ == "__main__":
    with SessionLocal.begin() as db:
        seed(db)
    print("Curriculum seeded successfully.")
