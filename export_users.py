def export_users():
    try:
        with open("users.txt", "r") as f:
            print("===== USERS.TXT FAYLDAGI USER ID LAR =====")
            print(f.read())
    except FileNotFoundError:
        print("❌ users.txt topilmadi.")

export_users()
