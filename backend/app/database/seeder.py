"""
Database seeder: wipes all data and re-populates Customers, TrustedDevices,
and simulated SecurityEvents for demo / development use.
"""
import sys
import logging
import random
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.customer import Customer, TrustedDevice, LoginHistory
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.models.investigation import Investigation
from app.models.detection_run import DetectionRun
from app.simulators.event_generator import main as run_simulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Seeder")

# ── Customer roster ──────────────────────────────────────────────────────────
CUSTOMERS = [
    {"first": "Aarav",     "last": "Sharma",    "cust_id": "CUST1001"},
    {"first": "Priya",     "last": "Patel",     "cust_id": "CUST1002"},
    {"first": "Rohan",     "last": "Mehta",     "cust_id": "CUST1003"},
    {"first": "Ananya",    "last": "Gupta",     "cust_id": "CUST1004"},
    {"first": "Arjun",     "last": "Nair",      "cust_id": "CUST1005"},
    {"first": "Neha",      "last": "Verma",     "cust_id": "CUST1006"},
    {"first": "Rahul",     "last": "Kapoor",    "cust_id": "CUST1007"},
    {"first": "Sneha",     "last": "Joshi",     "cust_id": "CUST1008"},
    {"first": "Vikram",    "last": "Singh",     "cust_id": "CUST1009"},
    {"first": "Kavya",     "last": "Reddy",     "cust_id": "CUST1010"},
    {"first": "Aditya",    "last": "Desai",     "cust_id": "CUST1011"},
    {"first": "Ishita",    "last": "Roy",       "cust_id": "CUST1012"},
    {"first": "Karan",     "last": "Malhotra",  "cust_id": "CUST1013"},
    {"first": "Meera",     "last": "Iyer",      "cust_id": "CUST1014"},
    {"first": "Siddharth", "last": "Rao",       "cust_id": "CUST1015"},
    {"first": "Pooja",     "last": "Kulkarni",  "cust_id": "CUST1016"},
    {"first": "Nikhil",    "last": "Jain",      "cust_id": "CUST1017"},
    {"first": "Aditi",     "last": "Shah",      "cust_id": "CUST1018"},
    {"first": "Varun",     "last": "Chawla",    "cust_id": "CUST1019"},
    {"first": "Riya",      "last": "Banerjee",  "cust_id": "CUST1020"},
]

# Possible trusted device templates
DEVICE_POOL = [
    {"name": "Windows Laptop",  "os": "Windows 11", "browser": "Chrome",  "tag": "LAPTOP"},
    {"name": "MacBook Pro",     "os": "macOS",      "browser": "Chrome",  "tag": "MAC"},
    {"name": "Android Phone",   "os": "Android",    "browser": "Chrome",  "tag": "MOBILE"},
    {"name": "iPhone",          "os": "iOS",        "browser": "Safari",  "tag": "IPHONE"},
    {"name": "Windows Desktop", "os": "Windows 10", "browser": "Edge",    "tag": "DESKTOP"},
    {"name": "Linux Laptop",    "os": "Ubuntu",     "browser": "Firefox", "tag": "LINUX"},
]

def _random_account() -> str:
    return str(random.randint(100_000_000_000, 999_999_999_999))


def wipe_database(db: Session) -> None:
    logger.info("Wiping existing data …")
    for model in [Investigation, Alert, SecurityEvent, DetectionRun,
                  LoginHistory, TrustedDevice, Customer]:
        db.query(model).delete()
    db.commit()
    logger.info("Database wiped.")


def seed_customers(db: Session) -> None:
    """Seed 20 customers, each with unique password and 1-2 trusted devices."""
    for c in CUSTOMERS:
        first = c["first"]
        last = c["last"]
        cust_id = c["cust_id"]
        password = f"{first}@123"
        email = f"{first.lower()}.{last.lower()}@bankdemo.com"
        account_number = _random_account()

        customer = Customer(
            customer_id=cust_id,
            full_name=f"{first} {last}",
            password=password,
            email=email,
            account_number=account_number,
        )
        db.add(customer)

        # Assign 1-2 distinct trusted devices per customer
        chosen = random.sample(DEVICE_POOL, k=random.choice([1, 2]))
        for tmpl in chosen:
            db.add(TrustedDevice(
                customer_id=cust_id,
                device_id=f"DEV-{first.upper()}-{tmpl['tag']}",
                device_name=tmpl["name"],
                browser=tmpl["browser"],
                operating_system=tmpl["os"],
            ))

    db.commit()
    logger.info(f"Seeded {len(CUSTOMERS)} customers with trusted devices.")


def run_reseed() -> None:
    db = SessionLocal()
    from app.database.session import engine
    from app.database.base_class import Base
    Base.metadata.create_all(bind=engine)
    try:
        wipe_database(db)
        seed_customers(db)
    except Exception as exc:
        logger.error(f"Seed error: {exc}")
        db.rollback()
        return
    finally:
        db.close()

    # Kick off a small batch of simulated events so the dashboard has data
    logger.info("Generating simulated events …")
    orig_argv = sys.argv
    sys.argv = ["event_generator.py", "--count", "3", "--interval", "0.2"]
    try:
        run_simulator()
    except SystemExit:
        pass
    except Exception as exc:
        logger.error(f"Simulator error: {exc}")
    finally:
        sys.argv = orig_argv

    # Print summary
    db = SessionLocal()
    try:
        from app.models.customer import Customer as C, TrustedDevice as TD
        from app.models.security_event import SecurityEvent as SE
        from app.models.alert import Alert as A

        print("\n" + "=" * 45)
        print("  SEED VERIFICATION REPORT")
        print("=" * 45)
        print(f"  Customers:       {db.query(C).count()}")
        print(f"  Trusted Devices: {db.query(TD).count()}")
        print(f"  Events:          {db.query(SE).count()}")
        print(f"  Alerts:          {db.query(A).count()}")
        print("=" * 45)
        print("\n  Demo Credentials (sample)")
        print("  " + "-" * 41)
        for c in CUSTOMERS[:5]:
            print(f"  {c['cust_id']}  {c['first']} {c['last']}  ->  {c['first']}@123")
        print("  ... (all 20 follow the same FirstName@123 pattern)")
        print()
    finally:
        db.close()


if __name__ == "__main__":
    run_reseed()
