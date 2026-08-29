#!/usr/bin/env python3
"""Add 20 new templates to apps.json and update app template fields."""
import json, pathlib

ROOT = pathlib.Path(__file__).parent
f = ROOT / "apps.json"
d = json.loads(f.read_text())

# Add template fields to apps that now have primary templates
app_template_map = {
    "settura": "ibs-food-diary-printable",
    "refluxlog": "acid-reflux-diary-printable",
    "nervelog": "neuropathy-symptom-log",
    "pawlog": "pet-vaccination-record",
    "plantlog": "plant-watering-schedule",
    "readlog": "reading-log-printable",
    "coralog": "reef-tank-parameter-log",
    "boardcut": "cut-list-template",
}
for app_key, tpl_slug in app_template_map.items():
    d["apps"][app_key]["template"] = tpl_slug

# 20 new templates
new_templates = {
    "ibs-food-diary-printable": {
        "app": "settura",
        "h1": "Free Printable IBS Food Diary (PDF)",
        "title": "Free Printable IBS Food Diary PDF — Meal & Symptom Log",
        "desc": "A free one-page printable IBS food diary. Log meals, symptoms, stress, and bowel changes daily to find your personal trigger foods — then bring a real record to your gastroenterologist.",
        "answer": "This is a free, one-page printable IBS food diary in PDF format. Each row is one day: meals (with FODMAP notes), symptom severity, bowel type on the Bristol scale, stress level, and any new foods tried. IBS symptoms rarely point to a single cause — a dated food-and-symptom log is how you start to find your pattern. Not medical advice.",
        "columns": ["Date", "Meals (note high-FODMAP foods)", "Bowel (Bristol scale)", "Bloating (0–10)", "Pain (0–10)", "Stress (0–10)", "Notes"],
        "col_widths": [9, 28, 13, 9, 8, 8, 25],
        "howto": [
            "Print the PDF — one page covers about three weeks.",
            "Log each day's meals, circling or noting any high-FODMAP foods — onion, garlic, wheat, dairy, and certain fruits are common examples.",
            "Record your bowel type using the Bristol Stool Scale (1–7) and rate bloating and pain from 0–10.",
            "Note your stress level — IBS and stress are closely linked, and stress is often overlooked in food-only diaries.",
            "After two or three weeks, bring the filled sheets to your gastroenterologist or dietitian."
        ],
        "howto_names": ["Print the PDF", "Log meals and FODMAP suspects", "Record bowel type and severity", "Note stress", "Bring it to your appointment"],
        "faq": [
            ["Is this IBS diary really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["What is the Bristol Stool Scale?", "The Bristol Stool Scale rates stool form from 1 (hard, separate lumps) to 7 (watery, no solid pieces). Types 3–4 are considered normal. Recording your type alongside meals gives your doctor and dietitian concrete data rather than vague descriptions."],
            ["Should I do a strict low-FODMAP elimination first?", "That's a question for your gastroenterologist or a registered dietitian specializing in IBS — elimination diets need professional guidance to be done correctly. This diary supports that process by giving you a dated record; it doesn't replace the clinical guidance."],
            ["Is there an app version of this diary?", "Yes — Settura for iPhone logs meals, symptoms, stress, and bowel changes and shows which foods appear most often before your worse days. The core app is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Name", "Started"]
    },
    "gut-symptom-tracker": {
        "app": "settura",
        "h1": "Free Printable Gut Symptom Tracker (PDF)",
        "title": "Free Printable Gut Symptom Tracker PDF — Daily IBS Log",
        "desc": "A free one-page printable gut symptom tracker. Record daily bloating, pain, bowel habits, and possible triggers — a concrete record for your gastroenterologist instead of trying to remember weeks later.",
        "answer": "This is a free, one-page printable gut symptom tracker in PDF format. Each row covers one day: overall gut symptom severity, specific symptoms present (bloating, cramps, urgency, nausea), bowel frequency and type, and anything that might explain the day — meals, stress, sleep, or medications. Not medical advice.",
        "columns": ["Date", "Severity (0–10)", "Symptoms present", "Bowel freq.", "Bristol type", "Possible factors", "Notes"],
        "col_widths": [9, 10, 20, 9, 9, 29, 14],
        "howto": [
            "Print the PDF — one page covers about three weeks.",
            "Each evening, rate your overall gut severity from 0–10 and check the symptoms that were present: bloating, cramps, urgency, nausea.",
            "Record how many bowel movements you had and the approximate Bristol type for the predominant one.",
            "Note anything that might explain the day — a stressful event, poor sleep, a new food, a missed medication dose.",
            "After two to three weeks, look for the pattern: the same factor appearing before your worse days. Bring the log to your appointment."
        ],
        "howto_names": ["Print the PDF", "Rate severity and check symptoms", "Record bowel frequency and type", "Note possible factors", "Look for the pattern"],
        "faq": [
            ["Is this tracker really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["Which symptoms should I track?", "Track whichever gut symptoms are most disruptive for you. The sheet covers the most commonly reported IBS symptoms — bloating, cramping, urgency, and nausea — but the notes column handles anything not listed."],
            ["Can I use this for conditions other than IBS?", "Yes. The sheet is designed for IBS but works for any gut condition where symptoms vary day to day — SIBO, IBD flare monitoring, or post-surgery recovery. Always follow your doctor's guidance for your specific condition."],
            ["Is there an app version?", "Yes — Settura for iPhone logs gut symptoms, meals, and stress and shows the patterns over time. Core is free, no account needed, data stays on your device."]
        ],
        "pdf_fields": ["Name", "Condition being tracked"]
    },
    "low-fodmap-food-log": {
        "app": "settura",
        "h1": "Free Printable Low FODMAP Food Log (PDF)",
        "title": "Free Printable Low FODMAP Food Log PDF — IBS Elimination Diary",
        "desc": "A free one-page printable low FODMAP food log. Track what you eat, FODMAP load, and IBS symptoms during an elimination or reintroduction phase — bring a real data set to your dietitian.",
        "answer": "This is a free, one-page printable low FODMAP food log in PDF format. Each row is one meal: date, meal type, foods eaten, estimated FODMAP load (low, medium, high), and symptoms in the following hours. Use during elimination to confirm symptom relief and during reintroduction to identify which FODMAP groups trigger your symptoms. Work with a dietitian registered in FODMAP protocols — this sheet supports that process but doesn't replace clinical guidance. Not medical advice.",
        "columns": ["Date", "Meal", "Foods eaten", "FODMAP load", "Symptoms", "Severity (0–10)", "Notes"],
        "col_widths": [9, 9, 30, 12, 16, 10, 14],
        "howto": [
            "Print the PDF — use one page per week during the elimination or reintroduction phase.",
            "For each meal, list what you ate and estimate the FODMAP load: low (safe-list items), medium (borderline), or high (known high-FODMAP).",
            "In the Symptoms column, note any gut reaction that appeared in the two to four hours following the meal.",
            "During reintroduction, test one FODMAP group at a time over three days — the log makes it clear which days triggered reactions.",
            "Bring the completed log to your dietitian; it provides the data needed to confirm your personal FODMAP tolerances."
        ],
        "howto_names": ["Print the PDF", "List foods and FODMAP load", "Note symptoms after each meal", "Track one FODMAP group at a time", "Bring it to your dietitian"],
        "faq": [
            ["Is this log really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["What is the low FODMAP diet?", "FODMAP stands for fermentable oligosaccharides, disaccharides, monosaccharides, and polyols — types of carbohydrates that can trigger IBS symptoms in sensitive individuals. The low FODMAP protocol, developed at Monash University, has the strongest evidence base for IBS symptom reduction. Always work with a qualified dietitian."],
            ["Do I need to know exact FODMAP amounts?", "Not for a paper log. Estimating low, medium, or high is enough to identify patterns. If you want precise portion-level FODMAP data, the Monash University FODMAP app is the reference standard."],
            ["Is there an iPhone app version?", "Yes — Settura for iPhone logs meals, symptoms, and stress and shows which foods appear most often before your worse days. The core app is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Name", "Phase (elimination / reintroduction)"]
    },
    "acid-reflux-diary-printable": {
        "app": "refluxlog",
        "h1": "Free Printable Acid Reflux Diary (PDF)",
        "title": "Free Printable Acid Reflux Diary PDF — GERD Episode Log",
        "desc": "A free one-page printable acid reflux diary. Record every episode with meals, timing, body position, and severity — find the foods and habits that reliably trigger your GERD symptoms.",
        "answer": "This is a free, one-page printable acid reflux and GERD diary in PDF format. Each row is one episode: date and time, what you ate in the prior two hours, body position when symptoms started (upright, reclined, lying), severity from 0–10, and how long symptoms lasted. Reflux patterns — certain foods, late meals, lying down after eating — often aren't obvious until you see them written down. Not medical advice.",
        "columns": ["Date", "Time", "Meal (2h before)", "Position", "Severity (0–10)", "Duration", "Notes"],
        "col_widths": [9, 8, 26, 12, 9, 9, 27],
        "howto": [
            "Print the PDF — one page covers about three weeks of episodes.",
            "After each significant episode, log the date and time while it's fresh — memory fades quickly.",
            "In the Meal column, write what you ate and drank in the two hours before symptoms started.",
            "Note body position when symptoms started: upright, recently reclined, or lying flat — position is often underreported and highly relevant.",
            "After two to three weeks, look for patterns: certain foods, late-night meals, or specific positions. Bring the log to your doctor."
        ],
        "howto_names": ["Print the PDF", "Log episodes promptly", "Record meals in the prior 2 hours", "Note body position", "Look for patterns"],
        "faq": [
            ["Is this diary really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["What foods commonly trigger acid reflux?", "Commonly discussed triggers include coffee, citrus, tomato-based foods, alcohol, spicy food, chocolate, and fatty meals — but individual responses vary considerably. That's exactly why a personal diary is more actionable than a universal list."],
            ["Does lying down after meals really make reflux worse?", "It's one of the most consistently reported aggravating factors — gravity helps keep stomach acid down when you're upright. The diary includes a position column precisely because it's a variable many people don't think to track until they see it in their own data."],
            ["Is there an app version of this diary?", "Yes — RefluxLog for iPhone logs episodes, meals, and positions and shows patterns over time. The core app is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Name", "Started"]
    },
    "heartburn-trigger-log": {
        "app": "refluxlog",
        "h1": "Free Printable Heartburn Trigger Log (PDF)",
        "title": "Free Printable Heartburn Trigger Log PDF — GERD Food Diary",
        "desc": "A free one-page printable heartburn trigger log. Track the foods, drinks, timing, and lifestyle factors that cause your acid reflux — spot your personal pattern before your next doctor visit.",
        "answer": "This is a free, one-page printable heartburn and acid reflux trigger log in PDF format. One row per day: foods and drinks consumed (flagging common suspects — coffee, citrus, tomato, alcohol, spicy food), last meal time, whether symptoms occurred, time of symptoms, and severity. The goal is to make your personal triggers visible — not to follow a universal list. Not medical advice.",
        "columns": ["Date", "Foods & drinks (flag suspects)", "Last meal time", "Symptoms (Y/N)", "Time of symptoms", "Severity (0–10)", "Notes"],
        "col_widths": [9, 26, 10, 10, 11, 9, 25],
        "howto": [
            "Print the PDF and keep it somewhere visible — near where you eat or on the fridge.",
            "Each day, note what you ate and drank, marking any common GERD suspects with a circle or asterisk.",
            "Record the time of your last meal — eating within two to three hours of lying down is a well-documented aggravator.",
            "If symptoms occur, note the time and rate severity from 0–10.",
            "After two to three weeks, look for which foods, times, or combinations appear before your symptomatic days. Bring the log to your doctor."
        ],
        "howto_names": ["Print the PDF", "Log foods and flag suspects", "Record last meal time", "Note symptoms and severity", "Look for your pattern"],
        "faq": [
            ["Is this log really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["Is heartburn the same as acid reflux?", "They're related but not identical. Acid reflux is the physical event — stomach acid moving into the esophagus. Heartburn is the burning sensation it often causes. GERD is a chronic condition defined by frequent, troublesome reflux. A diary tracks the symptom; diagnosis is your doctor's job."],
            ["Should I stop coffee and spicy food immediately?", "That's a conversation with your doctor. A diary helps you find your actual triggers rather than eliminating everything based on general advice — some people tolerate coffee fine; others have triggers that aren't on any standard list."],
            ["Is there an app version?", "Yes — RefluxLog for iPhone logs episodes, meals, and patterns and shows which factors appear most often before your worse days. Core is free, no account needed, data stays on your device."]
        ],
        "pdf_fields": ["Name", "Started"]
    },
    "neuropathy-symptom-log": {
        "app": "nervelog",
        "h1": "Free Printable Neuropathy Symptom Log (PDF)",
        "title": "Free Printable Neuropathy Symptom Log PDF — Nerve Pain Tracker",
        "desc": "A free one-page printable neuropathy symptom log. Track burning, tingling, numbness, and weakness by location and severity — give your neurologist a real picture of how your symptoms change over time.",
        "answer": "This is a free, one-page printable neuropathy symptom log in PDF format. Each row is one day: primary symptoms present (burning, tingling, numbness, shooting pain), location (feet, legs, hands, other), severity (0–10), any aggravating or relieving factors observed, and sleep quality. Neuropathy symptoms fluctuate — a weekly pattern often reveals more than any single clinic appointment can. Not medical advice.",
        "columns": ["Date", "Symptoms", "Location", "Severity (0–10)", "Aggravated by", "Relieved by", "Sleep (0–10)"],
        "col_widths": [9, 20, 14, 10, 16, 16, 15],
        "howto": [
            "Print the PDF — one page covers about three weeks.",
            "Each day, check the symptoms present: burning, tingling, numbness, shooting pain, or weakness.",
            "Note the location — feet, lower legs, hands, or other — and rate the overall severity from 0–10.",
            "In the Aggravated by column, note anything that made symptoms worse: standing, walking, heat, cold, tight shoes, or poor sleep.",
            "In the Relieved by column, note what helped: rest, elevation, ice, heat, medication. Bring the filled log to your neurologist."
        ],
        "howto_names": ["Print the PDF", "Check symptoms present", "Note location and severity", "Record aggravating factors", "Record relieving factors"],
        "faq": [
            ["Is this log really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["What causes neuropathy symptoms to vary day to day?", "Blood sugar levels (for diabetic neuropathy), activity, temperature, sleep quality, and medication timing can all influence daily symptom intensity. Recording these factors alongside severity helps your neurologist identify which variables are driving your fluctuations."],
            ["Should I log on days with no symptoms?", "Yes — logging a 0-severity day is as informative as logging a bad one. Days without symptoms, tracked against what you did differently, often reveal the most useful patterns."],
            ["Is there an app version?", "Yes — NerveLog for iPhone logs symptoms, location, and factors and shows patterns over time. Core is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Name", "Started"]
    },
    "nerve-pain-diary": {
        "app": "nervelog",
        "h1": "Free Printable Nerve Pain Diary (PDF)",
        "title": "Free Printable Nerve Pain Diary PDF — Neuropathy Episode Log",
        "desc": "A free one-page printable nerve pain diary. Record pain episodes with location, type, duration, and triggers — a dated log helps your neurologist track changes in your neuropathy over time.",
        "answer": "This is a free, one-page printable nerve pain diary in PDF format. Each row records one significant episode: when it started, where in the body, the type of sensation (burning, shooting, pins-and-needles, numbness, weakness), how long it lasted, and any activity or factor that may have triggered or worsened it. Not medical advice.",
        "columns": ["Date & time", "Location", "Type of sensation", "Severity (0–10)", "Duration", "Activity / trigger", "Medication taken"],
        "col_widths": [12, 14, 16, 10, 9, 22, 17],
        "howto": [
            "Print the PDF and keep it accessible — near your medications or in the room where episodes most often occur.",
            "When an episode starts, log the date, time, and location as soon as you can — memory of onset details fades quickly.",
            "Circle or write the type of sensation: burning, shooting, pins-and-needles, numbness, or weakness.",
            "Rate severity (0–10) and note how long it lasted once it subsides.",
            "Write what you were doing when it started or what seemed to make it worse. Bring the completed diary to your neurologist."
        ],
        "howto_names": ["Print the PDF", "Log onset details promptly", "Identify the sensation type", "Rate severity and duration", "Note activity and triggers"],
        "faq": [
            ["Is this diary really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["What types of neuropathy is this diary useful for?", "Any peripheral neuropathy — diabetic, idiopathic, Charcot-Marie-Tooth, chemotherapy-induced, or otherwise. The sheet tracks symptoms rather than cause, so it works regardless of the underlying diagnosis."],
            ["Should I track every sensation or only severe ones?", "That's your call, but most neurologists prefer more data over less. Even mild episodes that don't interrupt your day can reveal a pattern — especially if they cluster around a specific time, activity, or medication schedule."],
            ["Is there an app version?", "Yes — NerveLog for iPhone logs neuropathy symptoms, location, and factors and shows which patterns emerge over time. Core is free, no account needed, data stays on your device."]
        ],
        "pdf_fields": ["Name", "Diagnosis / condition"]
    },
    "pet-vaccination-record": {
        "app": "pawlog",
        "h1": "Free Printable Pet Vaccination Record (PDF)",
        "title": "Free Printable Pet Vaccination Record PDF — Dog & Cat Vaccine Log",
        "desc": "A free one-page printable pet vaccination record. Log every vaccine with date, lot number, clinic, and next due date for your dog or cat — the record you'll need for boarding, grooming, and vet visits.",
        "answer": "This is a free, one-page printable pet vaccination record in PDF format. Each row is one vaccine: the vaccine name (rabies, DHPP, bordetella, lepto, feline FVRCP, etc.), date given, lot number, administering vet or clinic, and the next due date. Boarding kennels, groomers, and dog parks routinely ask for this — having it organized in advance saves time and prevents missed boosters. Not veterinary advice.",
        "columns": ["Vaccine", "Date given", "Lot #", "Vet / clinic", "Next due", "Notes"],
        "col_widths": [22, 11, 11, 22, 11, 23],
        "howto": [
            "Print the PDF — one page tracks a full lifetime vaccination history for a single pet.",
            "After each vet visit, fill in the vaccine name, the date given, and the lot number (found on the clinic's paperwork or the vaccine label).",
            "Write the administering vet or clinic so you can call them if you ever need to verify the record.",
            "Fill in the next due date — most core vaccines are annual or triennial. A future due date written down is one you're unlikely to miss.",
            "Bring the filled card to every vet visit, boarding check-in, and grooming appointment."
        ],
        "howto_names": ["Print the PDF", "Log each vaccine after the visit", "Record the lot number and clinic", "Write the next due date", "Bring it to every appointment"],
        "faq": [
            ["Is this record really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["What vaccines do dogs and cats need?", "Core vaccines for dogs are generally considered to be rabies and DHPP (distemper, hepatitis, parvovirus, parainfluenza). Core vaccines for cats are typically rabies and FVRCP (feline viral rhinotracheitis, calicivirus, panleukopenia). Non-core vaccines like bordetella and leptospirosis depend on lifestyle. Your vet sets the schedule — this sheet just records it."],
            ["Does this replace the official vet certificate?", "No. Many boarding kennels require the original clinic record or a vet-signed certificate, especially for rabies. This sheet is a personal organizer and backup reference, not a substitute for official documentation."],
            ["Is there an app version?", "Yes — PawLog for iPhone tracks vet visits, vaccines, medications, and weight for your dog or cat. Core is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Pet name", "Breed & DOB"]
    },
    "dog-health-log": {
        "app": "pawlog",
        "h1": "Free Printable Dog & Cat Health Log (PDF)",
        "title": "Free Printable Pet Health Log PDF — Dog & Cat Vet Record",
        "desc": "A free one-page printable dog and cat health log. Record vet visits, symptoms, medications, and weight in one place — the kind of organized history that helps your vet give better care.",
        "answer": "This is a free, one-page printable dog and cat health log in PDF format. Each row is one event: date, weight, what happened (vet visit, observed symptom, medication change), any observations about appetite, energy, coat, or digestion, and the vet's response or next steps. A complete health history is especially valuable at senior checkups or when your pet sees a new or specialist vet. Not veterinary advice.",
        "columns": ["Date", "Weight", "Event type", "Observations", "Vet response / plan", "Meds changed?"],
        "col_widths": [10, 9, 18, 25, 28, 10],
        "howto": [
            "Print the PDF and keep it in your pet's file alongside vaccination records and vet invoices.",
            "Log every vet visit — even routine checkups — with the date, weight, and what was discussed or done.",
            "When you notice a symptom at home — limping, changes in appetite or energy, unusual discharge, vomiting — log it with a date, even if you don't go to the vet right away.",
            "If medication is started or changed, note it in the last column so the timeline is clear.",
            "Bring the log to every appointment — vets often ask about previous symptoms or weight trends that aren't in the clinic system."
        ],
        "howto_names": ["Print the PDF", "Log every vet visit", "Record home observations", "Note medication changes", "Bring it to every appointment"],
        "faq": [
            ["Is this log really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["Should I log routine checkups even when nothing is wrong?", "Definitely. Weight trends and normal-baseline observations at routine visits are exactly what help a vet detect early problems later — when they see a weight drop over two checkups, a written baseline makes the trend obvious."],
            ["What if I have multiple pets?", "Print one page per pet and keep them in labeled folders or a binder. The sheet has a field at the top for pet name and breed."],
            ["Is there an app version?", "Yes — PawLog for iPhone tracks vet visits, vaccines, medications, and weight for dogs and cats. Core is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Pet name", "Breed & DOB"]
    },
    "pet-medication-tracker": {
        "app": "pawlog",
        "h1": "Free Printable Pet Medication Tracker (PDF)",
        "title": "Free Printable Pet Medication Tracker PDF — Dog & Cat Med Log",
        "desc": "A free one-page printable pet medication tracker. Log every medication with dose, schedule, and refill date for your dog or cat — never miss a dose or run out at the wrong time.",
        "answer": "This is a free, one-page printable pet medication tracker in PDF format. Top section lists current medications: name, dose, frequency, start date, and refill or expiry date. Lower section logs each dose given with a date, time, and who administered it. Pets on multiple medications — for allergies, thyroid, heart, pain, or parasites — benefit the most from a written schedule, especially when more than one person cares for the same animal. Not veterinary advice.",
        "columns": ["Medication", "Dose", "Frequency", "Given by", "Date & time", "Notes"],
        "col_widths": [20, 12, 14, 14, 16, 24],
        "howto": [
            "Print the PDF and post it near where you store the medications.",
            "In the top section, list every current medication: name, dose, how often it's given, and when the supply runs out.",
            "Each time you give a dose, fill a row in the log section: who gave it and when — this prevents accidental double-dosing when two people share pet care.",
            "Check the refill dates weekly — running out of a heart or thyroid medication is a genuine emergency.",
            "Bring the sheet to every vet visit and any emergency clinic visit."
        ],
        "howto_names": ["Print and post near medications", "List current medications", "Log each dose given", "Check refill dates weekly", "Bring it to vet visits"],
        "faq": [
            ["Is this tracker really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["Why does it matter who gave the dose?", "Accidental double-dosing is a real risk in multi-person households — one person thinks the other gave the pill, and the pet gets double the dose. A simple sign-off column eliminates this."],
            ["What medications should I track?", "Everything prescribed or recommended by your vet: flea, tick, and heartworm preventatives; antibiotics; thyroid, heart, or joint medications; pain relievers; supplements. Over-the-counter items count too — vets need a complete picture."],
            ["Is there an app version?", "Yes — PawLog for iPhone tracks medications, vet visits, vaccines, and weight for dogs and cats. Core is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Pet name", "Vet clinic & phone"]
    },
    "plant-watering-schedule": {
        "app": "plantlog",
        "h1": "Free Printable Plant Watering Schedule (PDF)",
        "title": "Free Printable Plant Watering Schedule PDF — Houseplant Tracker",
        "desc": "A free one-page printable plant watering schedule. List every houseplant with its watering frequency, last watered date, and notes — never wonder which plant is overdue or overwatered again.",
        "answer": "This is a free, one-page printable plant watering schedule in PDF format. Each row is one plant: name, location in the home, watering frequency (every X days), last watered date, next due date, and notes on soil preference, light, and fertilizer schedule. Overwatering kills more houseplants than underwatering — a written schedule is the fastest way to stop guessing and start growing.",
        "columns": ["Plant name", "Location", "Water every", "Last watered", "Next due", "Soil / light", "Notes"],
        "col_widths": [18, 13, 10, 12, 10, 18, 19],
        "howto": [
            "Print the PDF and keep it near your plant shelf or posted on the fridge.",
            "Fill in every plant: name, the room or spot it lives in, and how often it should be watered.",
            "After you water a plant, update the Last watered date and calculate Next due by adding the watering interval.",
            "Use the Soil / light column for quick care notes — succulent mix, indirect light, bottom-watering only — so anyone watering your plants has the key info.",
            "Review the sheet weekly: anything with a Next due date in the past is overdue."
        ],
        "howto_names": ["Print the PDF", "List every plant", "Update after each watering", "Add soil and light notes", "Review weekly"],
        "faq": [
            ["Is this schedule really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["How do I know how often to water each plant?", "The general rule: check the soil before watering. If the top inch is still moist, wait. Species-specific guidelines are starting points — your home's humidity and light will shift the real number."],
            ["Can someone else water my plants using this sheet?", "That's exactly what it's designed for. The sheet has all the key information in one place so a plant-sitter or housemate doesn't need to guess or Google every species."],
            ["Is there an app version?", "Yes — PlantLog for iPhone tracks watering, fertilizing, and repotting with customizable reminders so nothing gets missed. Core is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Name", "Date started"]
    },
    "houseplant-care-log": {
        "app": "plantlog",
        "h1": "Free Printable Houseplant Care Log (PDF)",
        "title": "Free Printable Houseplant Care Log PDF — Plant Watering & Fertilizing",
        "desc": "A free one-page printable houseplant care log. Track watering, fertilizing, repotting, and observations for every plant — a record that helps you stop guessing and start noticing what actually works.",
        "answer": "This is a free, one-page printable houseplant care log in PDF format. Each row is one care event for one plant: date, plant name, what was done (water, fertilize, repot, prune, treat for pests), how much or what product was used, any observations (new growth, yellowing, drooping, pests spotted), and the next scheduled action. Plants don't come with error messages — a written log is how you build the pattern that makes you a better plant keeper.",
        "columns": ["Date", "Plant", "Care done", "Amount / product", "Observations", "Next action"],
        "col_widths": [10, 18, 18, 16, 24, 14],
        "howto": [
            "Print the PDF and keep it near your watering can or plant shelf.",
            "Each time you do anything to a plant — water, fertilize, prune, repot, treat for pests — log it with the date and plant name.",
            "In the Amount / product column, write how much water, which fertilizer and dilution, what pest treatment, or what size pot.",
            "In the Observations column, note anything you see: new growth, yellowing leaves, drooping, pests, or root-bound signs.",
            "In the Next action column, write what the plant needs next and approximately when — this becomes your informal schedule."
        ],
        "howto_names": ["Print the PDF", "Log every care event", "Note amounts and products", "Record what you observe", "Write the next planned action"],
        "faq": [
            ["Is this log really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["How detailed do my observations need to be?", "Short is fine. 'New leaf unfurling' or 'bottom 2 leaves yellowing' is enough. The value isn't in literary detail — it's in having a dated record you can look back on when something goes wrong or right."],
            ["Should I log every single watering?", "If you want a complete record, yes. If the sheet feels overwhelming, log water only when something unusual happens and log everything else (fertilize, repot, treat) every time."],
            ["Is there an app version?", "Yes — PlantLog for iPhone tracks all care events with reminders and shows your care history at a glance. Core is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Name", "Date started"]
    },
    "reading-log-printable": {
        "app": "readlog",
        "h1": "Free Printable Reading Log (PDF)",
        "title": "Free Printable Reading Log PDF — Book Tracker & Reading Record",
        "desc": "A free one-page printable reading log. Record every book with author, dates, pages, rating, and a note — a clean reading list that builds into a record of your year in books.",
        "answer": "This is a free, one-page printable reading log in PDF format. Each row is one book: title, author, genre, start date, finish date, number of pages, rating (1–5), and a one-line note. It fits about 20 books per page — enough for most readers for a full year, or a semester list.",
        "columns": ["Title", "Author", "Genre", "Started", "Finished", "Pages", "Rating", "Note"],
        "col_widths": [22, 16, 10, 9, 9, 7, 7, 20],
        "howto": [
            "Print the PDF and keep it in your current read or on your nightstand.",
            "When you start a book, fill in the title, author, genre, and start date.",
            "When you finish, fill in the date, page count, and your rating from 1–5.",
            "Write a one-line note — a favorite quote, what you thought of it, who you'd recommend it to. A year later, that one line is often the whole memory.",
            "At the end of the year, count the rows — your annual reading total is already there."
        ],
        "howto_names": ["Print the PDF", "Fill in details when you start", "Complete the entry when you finish", "Write a one-line note", "Count your yearly total"],
        "faq": [
            ["Is this log really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["What if I read mostly e-books or audiobooks?", "The sheet works for any format — just write the page count from the book's listing if you're reading an e-book, or leave pages blank for audiobooks and note the runtime in the Notes column instead."],
            ["Can I use this for a classroom reading list?", "Yes. Teachers use reading logs like this for independent reading programs — one sheet per student, or a class-wide sheet with one row per student. The genre column helps track reading diversity."],
            ["Is there an app version?", "Yes — ReadLog for iPhone logs books, quotes, and reading stats and generates shareable recap cards. Core is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Name", "Year"]
    },
    "book-tracker-template": {
        "app": "readlog",
        "h1": "Free Printable Book Tracker Template (PDF)",
        "title": "Free Printable Book Tracker Template PDF — Reading Challenge Log",
        "desc": "A free one-page printable book tracker. Log books read this year with author, genre, format, and rating — ideal for annual reading challenges, classroom logs, or anyone who wants a clean record of what they've read.",
        "answer": "This is a free, one-page printable book tracker template in PDF format. Each row records one book: title, author, genre or category, format (print, e-book, audiobook), date finished, star rating (1–5), and whether it counts toward a reading challenge category. Use it for a personal annual challenge, a classroom list, a book club record, or just to see what you've actually read this year.",
        "columns": ["Title", "Author", "Genre", "Format", "Date finished", "Rating", "Challenge cat."],
        "col_widths": [26, 18, 12, 10, 12, 8, 14],
        "howto": [
            "Print the PDF at the start of a reading challenge or the new year.",
            "List each book as you finish it — title, author, genre (fiction, mystery, memoir, sci-fi, etc.), and the format you used.",
            "Rate it 1–5 and note the date you finished.",
            "If you're working through a reading challenge with categories, fill in the matching category in the last column.",
            "At year's end, count rows and note which categories you hit or missed."
        ],
        "howto_names": ["Print at the start of your challenge", "Log each book as you finish", "Rate and date it", "Note the challenge category", "Review at year's end"],
        "faq": [
            ["Is this template really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["Which reading challenges work with this tracker?", "Any challenge that uses categories — PopSugar Reading Challenge, Read Harder, Goodreads annual challenge, library summer reading programs. The last column is intentionally blank so you can write your own category labels."],
            ["What if I read a book but didn't finish it?", "That's your call. Many readers log DNFs (did-not-finish) with a note — 'DNF at 40%' — because it's useful information for future you and for recommendations. Others only log completed reads. The sheet works either way."],
            ["Is there an app version?", "Yes — ReadLog for iPhone tracks books, quotes, and reading stats with shareable year-in-review cards. Core is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Name", "Year / challenge"]
    },
    "reef-tank-parameter-log": {
        "app": "coralog",
        "h1": "Free Printable Reef Tank Parameter Log (PDF)",
        "title": "Free Printable Reef Tank Parameter Log PDF — Coral & Saltwater Tracker",
        "desc": "A free one-page printable reef tank parameter log. Record salinity, pH, alkalinity, calcium, magnesium, nitrate, and phosphate with test dates — see your parameters drift before your coral does.",
        "answer": "This is a free, one-page printable reef tank parameter log in PDF format. Each row is one test session: date, salinity (SG or ppt), pH, alkalinity (dKH), calcium (ppm), magnesium (ppm), nitrate (ppm), phosphate (ppm), and notes. Parameters rarely fail all at once — weekly testing with a written record lets you catch which value is drifting before it causes coral bleaching, RTN, or a livestock crash. Not veterinary advice.",
        "columns": ["Date", "Salinity", "pH", "Alk (dKH)", "Ca (ppm)", "Mg (ppm)", "NO3", "PO4", "Notes"],
        "col_widths": [10, 9, 7, 10, 9, 9, 8, 7, 31],
        "howto": [
            "Print the PDF and keep it near your test kit station.",
            "Run your parameter tests and log each value in the corresponding column — a full test session takes one row.",
            "In the Notes column, record any dosing you added after testing: two-part, kalkwasser, calcium reactor output, or carbon dosing.",
            "After a few weeks, scan the columns vertically — alkalinity is the most volatile and often the first to show a drift pattern.",
            "Bring the log to your local reef shop if you're troubleshooting a coral problem; a parameter trend is far more informative than a single test result."
        ],
        "howto_names": ["Print and keep near your test station", "Log all parameters in one row", "Note any dosing added", "Scan columns for drift patterns", "Share the log when troubleshooting"],
        "faq": [
            ["Is this log really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["How often should I test a reef tank?", "Most reef-keepers test alkalinity two to three times per week (it's consumed fastest), calcium and magnesium weekly, and nitrate and phosphate weekly to biweekly depending on livestock load. Salinity and pH can be monitored continuously with probes, but periodic manual verification is still useful for calibration checks."],
            ["What are the target ranges for reef parameters?", "Common targets: salinity 1.025–1.026 SG, pH 8.1–8.3, alkalinity 8–9 dKH, calcium 400–450 ppm, magnesium 1250–1350 ppm, nitrate 1–10 ppm for mixed reefs, phosphate 0.02–0.05 ppm. Actual targets depend on your specific system and livestock."],
            ["Is there an app version?", "Yes — Coralog for iPhone logs reef parameters, dosing, and livestock with trend charts and drift warnings. Core is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Tank name / size", "Started"]
    },
    "aquarium-water-quality-log": {
        "app": "coralog",
        "h1": "Free Printable Aquarium Water Quality Log (PDF)",
        "title": "Free Printable Aquarium Water Quality Log PDF — Fish Tank Parameter Tracker",
        "desc": "A free one-page printable aquarium water quality log. Track ammonia, nitrite, nitrate, pH, temperature, and hardness for any freshwater or saltwater tank — catch parameter problems before they hurt your fish.",
        "answer": "This is a free, one-page printable aquarium water quality log in PDF format. Each row is one test session: date, water temperature, pH, ammonia (ppm), nitrite (ppm), nitrate (ppm), and general hardness (GH). Works for freshwater, planted, and saltwater tanks. Water chemistry changes gradually and silently — a written log is how experienced fish-keepers catch problems before livestock is lost. Not veterinary advice.",
        "columns": ["Date", "Temp", "pH", "Ammonia", "Nitrite", "Nitrate", "Hardness (GH)", "Notes"],
        "col_widths": [10, 8, 7, 12, 10, 10, 13, 30],
        "howto": [
            "Print the PDF and keep it near your testing area or stuck to the side of the aquarium cabinet.",
            "Run your water tests and log each result in the corresponding column — one test session per row.",
            "In the Notes column, record any water change done: volume replaced, conditioner used, or any treatment added.",
            "Keep an eye on ammonia and nitrite — in a cycling tank or after adding fish, these are the danger columns. Both should read zero in an established tank.",
            "If a fish shows stress or illness, look back at the previous two weeks of logs — a pattern almost always precedes a problem."
        ],
        "howto_names": ["Print and post near your tank", "Log each test session", "Note water changes and treatments", "Watch ammonia and nitrite", "Review history when problems arise"],
        "faq": [
            ["Is this log really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["How often should I test my aquarium water?", "For a cycling tank: daily or every other day for ammonia and nitrite. For an established stable tank: weekly pH, nitrate, and temperature; monthly for the rest. High-bioload tanks and planted tanks with CO2 injection need more frequent monitoring."],
            ["What are safe ammonia and nitrite levels?", "Any detectable ammonia or nitrite in an established tank is a problem — both should read 0 ppm. Nitrate up to 20 ppm is generally tolerated by most fish; under 5 ppm is preferred for sensitive species and planted tanks."],
            ["Is there an app version?", "Yes — Coralog for iPhone logs aquarium and reef parameters with trend charts and alerts. Core is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Tank name / size", "Set up date"]
    },
    "cut-list-template": {
        "app": "boardcut",
        "h1": "Free Printable Cut List Template (PDF)",
        "title": "Free Printable Cut List Template PDF — Woodworking Parts List",
        "desc": "A free one-page printable cut list template. Record every part with dimensions, material, grain direction, and quantity — the paper version of what every woodworking project starts with.",
        "answer": "This is a free, one-page printable cut list template in PDF format. Each row is one part: part name, material (plywood, solid wood, MDF), width, length, thickness, quantity, grain direction, and notes (edge banding, joinery type, saw notes). Organizing a cut list before you go to the saw — even on paper — eliminates costly rip-cuts you can't undo and makes the most of every sheet.",
        "columns": ["Part name", "Material", "W (in)", "L (in)", "T (in)", "Qty", "Grain", "Notes"],
        "col_widths": [22, 16, 7, 7, 7, 7, 9, 25],
        "howto": [
            "Print the PDF before you start cutting — one page handles most small to medium projects.",
            "List every part the project requires, one row per piece.",
            "Fill in the material (plywood species, MDF, solid wood species and board) and dimensions: width, length, and thickness.",
            "Mark grain direction as parallel or perpendicular to the long edge — this matters for strength and appearance on visible faces.",
            "Sort the list by material and size before cutting: all same-thickness plywood parts together, then solid wood, then trim pieces."
        ],
        "howto_names": ["Print before cutting", "List every part", "Record material and dimensions", "Mark grain direction", "Sort before cutting"],
        "faq": [
            ["Is this template really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["Do I need a cut list for small projects?", "For anything with more than four or five parts, a written cut list pays for itself the first time it prevents a measuring mistake. It also lets you calculate how many sheets of plywood you need before buying."],
            ["How do I decide grain direction?", "On structural pieces hidden from view, grain direction doesn't matter much. On visible faces — cabinet doors, tabletops, drawer fronts — grain direction affects both appearance and, in solid wood, expansion and contraction across the grain. The general rule: run grain along the long dimension for panels."],
            ["Is there an app version?", "Yes — Boardcut for iPhone optimizes your cut list into a cutting diagram that minimizes waste. Planning is free with no piece limit; exporting a PDF or CSV unlocks for $12.99 once."]
        ],
        "pdf_fields": ["Project name", "Date"]
    },
    "woodworking-cut-list": {
        "app": "boardcut",
        "h1": "Free Printable Woodworking Cut List for Sheet Goods (PDF)",
        "title": "Free Printable Woodworking Cut List PDF — Sheet Goods Layout",
        "desc": "A free one-page printable woodworking cut list designed for plywood and sheet goods. A parts table plus a blank 4×8 grid for hand-sketching your layout — waste less material before the first cut.",
        "answer": "This is a free, one-page printable woodworking cut list for sheet goods in PDF format. Two sections: a parts table (part name, dimensions, quantity, grain direction) and a blank 4×8 sheet grid where you sketch your layout by hand. Even a rough hand-drawn layout catches the obvious waste before you start cutting. Use one page per sheet of plywood, MDF, or melamine.",
        "columns": ["Part", "W (in)", "L (in)", "T (in)", "Qty", "Grain (Y/N)", "Nested?", "Notes"],
        "col_widths": [22, 8, 8, 8, 7, 11, 10, 26],
        "howto": [
            "Print one page per sheet of plywood or panel material you plan to cut.",
            "List every part you need from this sheet in the table: name, width, length, thickness, and quantity.",
            "Mark grain direction Yes or No — whether you need grain to run parallel to the long dimension of the part.",
            "Use the blank 4×8 grid below the table to sketch a rough layout: draw rectangles to represent each part. A hand-drawn layout catches obvious waste before you commit at the saw.",
            "Transfer the layout to the actual sheet with a pencil and straightedge before cutting."
        ],
        "howto_names": ["Print one page per sheet", "List all parts for this sheet", "Note grain requirements", "Sketch the layout on the grid", "Transfer to the real sheet"],
        "faq": [
            ["Is this template really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["Why hand-sketch a layout when software can do it?", "For small projects, drawing it takes two minutes. The value isn't precision — it's the moment when you realize your original plan wastes an entire strip that could yield two more parts. A pencil catches this in seconds."],
            ["What's the grid scale?", "The grid is for rough proportional sketching only — it's not to exact scale. If you need a precise nested layout, the Boardcut app computes the optimal arrangement and shows you exactly where to mark each cut."],
            ["Is there an app version?", "Yes — Boardcut for iPhone takes your parts list and computes an optimized cut diagram. Planning is free with no piece limit; exporting a PDF or CSV unlocks for $12.99 once."]
        ],
        "pdf_fields": ["Project name", "Sheet material & size"]
    },
    "mileage-log-printable": {
        "app": "motorlog",
        "h1": "Free Printable Mileage Log (PDF)",
        "title": "Free Printable Mileage Log PDF — IRS Business Mileage Tracker",
        "desc": "A free one-page printable mileage log. Record every business trip with date, destination, miles, and purpose — the IRS-compliant format needed to claim the standard mileage deduction.",
        "answer": "This is a free, one-page printable mileage log in PDF format for business mileage deduction records. Each row is one trip: date, starting odometer, ending odometer, total miles, destination, and business purpose. The IRS standard mileage rate requires a contemporaneous record — written at or near the time of the trip — that shows the date, miles, destination, and business purpose. This log satisfies those requirements.",
        "columns": ["Date", "Start odometer", "End odometer", "Miles", "Destination", "Business purpose", "YTD total"],
        "col_widths": [9, 12, 11, 7, 16, 29, 16],
        "howto": [
            "Print the PDF and keep it in your vehicle — glove box, center console, or visor clip.",
            "At the start of every business trip, write the date and starting odometer.",
            "At the end of the trip, write the ending odometer and calculate miles: end minus start.",
            "Write the destination and the business purpose — 'Client meeting: Acme Corp' or 'Supply run: Home Depot, job site materials.'",
            "At the end of each row, add the trip miles to the YTD total. This running total is what you report on Schedule C or your expense system."
        ],
        "howto_names": ["Keep it in the vehicle", "Log start odometer", "Log end odometer and miles", "Write destination and purpose", "Maintain the YTD total"],
        "faq": [
            ["Is this log really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["What qualifies as a business mile?", "Driving between work locations, to client sites, to meetings, or for business errands generally qualifies. Commuting from home to your regular place of business generally does not. Consult a tax professional for your specific situation — IRS Publication 463 covers transportation expense rules."],
            ["Does the IRS require odometer readings?", "The IRS requires records showing the miles driven, the date, the destination, and the business purpose. Odometer readings are the most reliable way to substantiate miles if records are ever examined — they're recommended even if not technically mandatory."],
            ["Is there an app version?", "Yes — MotorLog for iPhone tracks business trips, fill-ups, and service records with automatic mileage calculation and PDF export. Core is free, no account needed, data stays on your device."]
        ],
        "pdf_fields": ["Vehicle", "Tax year"]
    },
    "chronic-pain-log": {
        "app": "nervelog",
        "h1": "Free Printable Chronic Pain Log (PDF)",
        "title": "Free Printable Chronic Pain Log PDF — Daily Pain Tracker",
        "desc": "A free one-page printable chronic pain log. Record daily pain location, severity, duration, and factors for any chronic pain condition — a dated record gives your doctor and pain management team real data to work with.",
        "answer": "This is a free, one-page printable chronic pain log in PDF format. Each row is one day: pain severity (0–10), primary location, pain type (aching, burning, stabbing, throbbing), duration, aggravating factors, relieving factors, and how pain affected your ability to function. For any chronic pain condition — neuropathy, fibromyalgia, arthritis, back pain, CRPS — a daily written log reveals patterns that appointment-based recall cannot. Not medical advice.",
        "columns": ["Date", "Severity (0–10)", "Location", "Type", "Duration", "Aggravated by", "Relieved by / Function"],
        "col_widths": [9, 10, 14, 12, 9, 22, 24],
        "howto": [
            "Print the PDF — one page covers about three weeks of daily entries.",
            "Each day, rate your overall pain severity from 0–10, even on good days. A zero is valuable data.",
            "Note the primary location and pain type — these often change and the change is clinically meaningful.",
            "Record anything that seemed to make pain worse: activity, weather, poor sleep, stress, or certain movements.",
            "Note what helped: rest, heat, ice, medication, physical therapy. In the final column, briefly rate how pain limited your function."
        ],
        "howto_names": ["Print the PDF", "Rate severity daily", "Note location and type", "Record aggravating factors", "Record relieving factors and function"],
        "faq": [
            ["Is this log really free?", "Yes. The PDF is free to download and print — no sign-up, no email."],
            ["Should I log every day even when pain is low?", "Yes — and especially on good days. Low-pain days often share identifiable factors (good sleep, reduced stress, certain activities avoided) that are as clinically valuable as the high-pain days. A complete log is far more informative than one that only records bad days."],
            ["Can I use this for fibromyalgia, CRPS, or back pain?", "This sheet is designed to be condition-agnostic — it tracks the dimensions of pain that are relevant across conditions. The location, type, and aggravating-factor columns can be adapted with whatever terminology is relevant to your diagnosis."],
            ["Is there an app version?", "Yes — NerveLog for iPhone tracks neuropathy symptoms, pain levels, and factors and shows patterns over time. Core is free, no account needed, and your data stays on your device."]
        ],
        "pdf_fields": ["Name", "Condition being tracked"]
    }
}

d["templates"].update(new_templates)

out = json.dumps(d, ensure_ascii=False, indent=2)
f.write_text(out)

# verify
loaded = json.loads(out)
print(f"templates: {len(loaded['templates'])} (expected 30)")
print(f"apps with template field: {sum(1 for a in loaded['apps'].values() if 'template' in a)}")
print("JSON valid: OK")
