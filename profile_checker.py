# profile_checker.py

# Define good and bad account criteria (can be extended)
GOOD_ACCOUNTS = [
    "https://www.facebook.com/faithfulfansite",
    "https://www.facebook.com/someothergoodaccount",
    "https://www.facebook.com/Shayarikidayri"
]

BAD_ACCOUNTS = [
    "https://www.facebook.com/spamaccount",
    "https://www.facebook.com/fakeprofile"
]

def is_good_account(profile_url):

    if profile_url in GOOD_ACCOUNTS:
        return True
    elif profile_url in BAD_ACCOUNTS:
        return False
    else:
        # Default to bad if not explicitly listed
        return "not in list"

# Example Usage
# print(is_good_account("https://www.facebook.com/faithfulfansite"))  # True
