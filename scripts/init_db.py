from smartcoat.storage.database.base import Base
from smartcoat.storage.database.models import (
    DecisionObjectRecord,
    EnterpriseEventRecord,
    KnowledgeObjectRecord,
)
from smartcoat.storage.database.session import engine


def main() -> None:
    _ = (KnowledgeObjectRecord, DecisionObjectRecord, EnterpriseEventRecord)
    Base.metadata.create_all(bind=engine)
    print("SmartCoat database initialized.")


if __name__ == "__main__":
    main()
