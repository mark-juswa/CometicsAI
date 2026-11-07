from kaggle_secrets import UserSecretsClient

client = UserSecretsClient()
checks = {"AI_BACKEND_API_KEY": 32, "AI_REMOTE_API_KEY": 24, "GEMINI_API_KEY": 1}
ready = True
for name, minimum in checks.items():
    try:
        value = client.get_secret(name) or ""
        passed = len(value) >= minimum
        print(name + ": " + ("PASS" if passed else f"TOO SHORT / EMPTY (minimum {minimum} characters)"))
    except Exception:
        passed = False
        print(name + ": NOT ACCESSIBLE — enable it for this notebook")
    ready = ready and passed
if not ready:
    raise RuntimeError("Fix the failing secrets in Add-ons > Secrets, then rerun this check.")
print("All startup secret checks pass. Run Cell 2.")
