import re

with open("app/simulators/event_generator.py", "r") as f:
    content = f.read()

# Add imports if not present
if "import random" not in content:
    content = content.replace("import httpx\n", "import httpx\nimport random\nfrom app.database.session import SessionLocal\nfrom app.models.customer import Customer\n")

# Modify run_scenario signature
content = content.replace(
    "def run_scenario(scenario_name: str, target_url: str, interval: float) -> bool:",
    "def run_scenario(scenario_name: str, target_url: str, interval: float, customer_profile: dict) -> bool:"
)

# Modify generator_func call
content = content.replace(
    "events = generator_func(base_time, scenario_id)",
    "events = generator_func(base_time, scenario_id, customer_profile)"
)

# Modify main function to fetch customers and pass to run_scenario
main_mod = """
    logger.info(f"Selected scenario: {args.scenario}")
    logger.info(f"Execution count: {args.count if args.count > 0 else 'Infinite'}")
    
    logger.info("Fetching customers from database...")
    db = SessionLocal()
    customers_db = db.query(Customer).all()
    db.close()
    
    if not customers_db:
        logger.error("No customers found in the database. Please run the seeder first.")
        sys.exit(1)
        
    customer_profiles = [
        {
            "customer_id": c.customer_id,
            "full_name": c.full_name,
            "email": c.email,
            "account_number": c.account_number
        }
        for c in customers_db
    ]
    
    scenarios_to_run = list(SCENARIOS_MAP.keys())
"""
content = content.replace(
    """    logger.info(f"Selected scenario: {args.scenario}")
    logger.info(f"Execution count: {args.count if args.count > 0 else 'Infinite'}")
    
    scenarios_to_run = list(SCENARIOS_MAP.keys())""",
    main_mod
)

# Update run_scenario call in main
content = content.replace(
    """                success = run_scenario(
                    scenario_name=scenario_name,
                    target_url=args.url,
                    interval=args.interval
                )""",
    """                customer_profile = random.choice(customer_profiles)
                success = run_scenario(
                    scenario_name=scenario_name,
                    target_url=args.url,
                    interval=args.interval,
                    customer_profile=customer_profile
                )"""
)

with open("app/simulators/event_generator.py", "w") as f:
    f.write(content)
print("Updated event_generator.py")
