import pandas as pd
import json

# ------------------ AG NEWS ------------------
ag = pd.read_csv("../dataset/train.csv")

ag = ag.rename(columns={
    "Class Index": "label",
    "Title": "title",
    "Description": "description"
})

ag["text"] = ag["title"].astype(str) + " " + ag["description"].astype(str)

ag_map = {
    1: "Important",  # World
    2: "Friends",    # Sports
    3: "Work",       # Business
    4: "Office"      # Sci/Tech
}

ag["category"] = ag["label"].map(ag_map)
ag = ag[["text", "category"]]


# ------------------ SMS SPAM ------------------
sms = pd.read_csv("../dataset/spam.csv", encoding="latin-1")

sms = sms.rename(columns={"v1": "label", "v2": "text"})

sms_map = {
    "ham": "Personal",
    "spam": "Other"
}

sms["category"] = sms["label"].map(sms_map)
sms = sms[["text", "category"]]


# ------------------ CLINC150 JSON ------------------
with open("../dataset/clinc150.json", "r", encoding="utf-8") as f:
    clinc = json.load(f)

def map_intent(intent):
    intent = intent.lower()

    if any(k in intent for k in ["appointment", "doctor", "medicine", "hospital"]):
        return "Medical"
    if any(k in intent for k in ["bill", "pay", "grocery", "rent", "utility"]):
        return "Household"
    if "family" in intent:
        return "Family"
    if any(k in intent for k in ["meeting", "email", "office", "schedule"]):
        return "Office"
    if any(k in intent for k in ["reminder", "urgent", "important"]):
        return "Important"
    if any(k in intent for k in ["profile", "personal", "hobby"]):
        return "Personal"
    if any(k in intent for k in ["friend", "party", "hangout"]):
        return "Friends"

    return "Other"

clinc_rows = []
for text, intent in clinc["train"]:
    clinc_rows.append({
        "text": text,
        "category": map_intent(intent)
    })

clinc_df = pd.DataFrame(clinc_rows)


# ------------------ MERGE ALL ------------------
final_df = pd.concat([ag, sms, clinc_df], ignore_index=True)
final_df = final_df.dropna()
final_df = final_df.sample(frac=1, random_state=42)

final_df.to_csv("../dataset/notes_dataset.csv", index=False)

print("Final dataset created")
print(final_df["category"].value_counts())
