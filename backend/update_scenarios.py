import re

with open("app/simulators/scenarios.py", "r") as f:
    content = f.read()

# 1. Update function signatures
content = re.sub(
    r'def get_([a-z_]+)\(base_time: datetime, scenario_id: str\) -> List\[Dict\[str, Any\]\]:',
    r'def get_\1(base_time: datetime, scenario_id: str, customer_profile: Dict[str, Any]) -> List[Dict[str, Any]]:',
    content
)

# 2. Update user_id assignments
content = re.sub(
    r'"user_id": "usr_[a-z]+",',
    r'"user_id": user_id,',
    content
)
content = re.sub(
    r'user_id = "usr_[a-z]+"',
    r'user_id = customer_profile["customer_id"]',
    content
)

# Insert user_id = customer_profile["customer_id"] into get_impossible_travel and get_new_device
# which didn't have user_id assigned to a variable.
# For get_impossible_travel:
content = content.replace(
    '''    total_steps = 2
    events = []

    # 1. London Login''',
    '''    total_steps = 2
    events = []
    user_id = customer_profile["customer_id"]

    # 1. London Login'''
)

# For get_new_device:
content = content.replace(
    '''    total_steps = 1
    events = []

    events.append({''',
    '''    total_steps = 1
    events = []
    user_id = customer_profile["customer_id"]

    events.append({'''
)

# 3. Add customer_profile to simulation payload
# We look for "expected_detection": [...] and append ,"customer_profile": customer_profile after it.
content = re.sub(
    r'("expected_detection": \[.*?\])\n',
    r'\1,\n                "customer_profile": customer_profile\n',
    content
)

with open("app/simulators/scenarios.py", "w") as f:
    f.write(content)
print("Updated scenarios.py")
