import yaml

with open("config/profile.yaml", "r", encoding="utf-8") as file:
    profile = yaml.safe_load(file)

print("Job Agent Profile Loaded")
print("=" * 40)

print("Roles:")
for role in profile["roles"]:
    print(f"  - {role}")

print("\nLocations:")
for location in profile["locations"]:
    print(f"  - {location}")

print("\nHigh Priority Skills:")
for skill in profile["high_priority_skills"]:
    print(f"  - {skill}")