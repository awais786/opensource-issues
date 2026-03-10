import json

d = json.load(open("data/repos.json"))

preferred = [
    "django_core", "rest_api", "auth_security", "database_orm",
    "testing", "task_queues", "py_core", "py_web", "py_tools",
    "logging_monitoring", "ecommerce"
]
all_cats = list(d["categories"].keys())

print("=== YOUR PREFERRED CATEGORIES ===")
pref_count = 0
for cat in preferred:
    if cat in d["categories"]:
        repos = d["categories"][cat]["repos"]
        pref_count += len(repos)
        label = d["categories"][cat]["label"]
        eco = d["categories"][cat].get("ecosystem", "?")
        print(f"  {cat} ({label}, {eco}) - {len(repos)} repos")
    else:
        print(f"  {cat}: *** NOT FOUND ***")

total = sum(len(c["repos"]) for c in d["categories"].values())
print(f"\nTotal preferred repos: {pref_count}")
print(f"Total repos in hub: {total}")
print(f"Coverage: {pref_count}/{total} = {100*pref_count/total:.0f}%")

print("\n=== CATEGORIES YOU SKIP ===")
for cat in all_cats:
    if cat not in preferred:
        c = d["categories"][cat]
        eco = c.get("ecosystem", "?")
        print(f"  {cat} ({c['label']}, {eco}) - {len(c['repos'])} repos")

# Check skill-to-category alignment
print("\n=== SKILL ALIGNMENT CHECK ===")
skills = {
    "Python":          ["py_core", "py_web", "py_tools", "py_packaging"],
    "Django ORM":      ["django_core", "database_orm"],
    "DRF":             ["rest_api"],
    "Celery":          ["task_queues"],
    "pytest":          ["testing"],
    "Auth/Perms":      ["auth_security"],
}
for skill, cats in skills.items():
    in_pref = [c for c in cats if c in preferred]
    missing = [c for c in cats if c not in preferred and c in all_cats]
    status = "OK" if not missing else f"MISSING: {missing}"
    print(f"  {skill:15s} -> covers {in_pref}, {status}")

print("\n=== SKIPPED CATEGORIES THAT MATCH YOUR SKILLS ===")
skill_adjacent = {
    "graphql":       "You know DRF - GraphQL is just another API layer (Graphene-Django, Strawberry)",
    "py_packaging":  "You know Python - packaging is pure Python (setuptools, flit, hatch)",
    "search":        "You know Django - search is Django backend work (Haystack, Elasticsearch-DSL)",
    "i18n_geo":      "You know Django - i18n/geo is Django middleware + ORM (django-modeltranslation)",
    "storage_files": "You know Django - file storage is Django backend (django-storages, whitenoise)",
}
for cat, reason in skill_adjacent.items():
    if cat in all_cats and cat not in preferred:
        n = len(d["categories"][cat]["repos"])
        print(f"  {cat} ({n} repos): {reason}")

