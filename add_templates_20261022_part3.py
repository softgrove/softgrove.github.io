#!/usr/bin/env python3
"""2026-10-22 part 3: one new template each for Skinote, GoutLog, MotorLog, PawLog, Banneton, Combwise,
and the plywood-cut-calculator guide opening rework (URL unchanged)."""
import json, pathlib

ROOT = pathlib.Path(__file__).parent
f = ROOT / "apps.json"
d = json.loads(f.read_text())

FREE_FAQ = ["Is this sheet really free?", "Yes. The PDF is free to download and print — no sign-up, no email, no watermark."]

OTHERS = {
    # ------------------------------------------------------------ Skinote
    "eczema-itch-diary": {
        "app": "skinote",
        "h1": "Free Printable Itch Diary (PDF) — Eczema Itch & Scratch Log",
        "title": "Free Printable Itch Diary PDF — Eczema Itch Severity & Scratch Log",
        "desc": "A free one-page printable itch diary for eczema and other itchy skin conditions. Rate itch 0–10 by time of day, note where it was, what you were doing, scratching and lost sleep — a record to bring to your dermatologist. Not medical advice.",
        "answer": "This is a free, one-page printable itch diary in PDF format. Each row is one itch episode or one time slot: the date, time of day, itch intensity from 0 to 10, where on the body, whether you scratched and how much sleep it cost, and what was happening at the time — heat, sweat, fabric, a bath, stress. Flare trackers record the skin; this sheet records the symptom that actually disrupts your day and night, which is the thing a dermatologist most often asks about and the thing patients find hardest to describe from memory. It is a record-keeping aid, not medical advice.",
        "columns": ["Date", "Time of day", "Itch (0–10)", "Where", "Scratched / sleep lost", "What was happening", "Notes"],
        "col_widths": [9, 11, 9, 15, 17, 22, 17],
        "sections": [
            {"h2": "Why log itch separately from flares",
             "body": ["Visible eczema and itch do not always move together. Itch often spikes in the evening and at night, after exercise, or during stressful weeks, while the skin looks the same. A diary that only records how the skin looked misses the pattern. Scoring itch on a simple 0–10 scale at a few fixed points — morning, afternoon, evening, night — turns 'it has been bad lately' into a line your dermatologist can read, and shows whether a change in routine actually helped.",
                      "Record the context without judging it. 'Wool sweater', 'hot shower', 'gym', 'deadline', 'new detergent' are observations. Over two or three weeks, the ones that keep appearing beside high scores are worth discussing with your clinician; the sheet does not decide what they mean."]},
        ],
        "reference": [
            {"h2": "Scoring and what to note",
             "intro": "Anchors for the 0–10 column, and the context most people find worth writing down. Use whatever words fit — consistency matters more than the exact number.",
             "columns": ["Score", "What it feels like", "Context worth noting"],
             "rows": [["0", "No itch", "—"],
                      ["1–3", "Noticeable but easy to ignore; no scratching needed", "Time of day, what you were wearing"],
                      ["4–6", "Hard to ignore; you scratch or rub, can still concentrate", "Heat, sweat, fabric, bathing, a new product"],
                      ["7–9", "Dominates attention; scratching is hard to stop; disturbs sleep", "Stress, illness, missed routine, sleep lost (hours)"],
                      ["10", "Worst imaginable; cannot sleep or function", "Everything above — and tell your clinician"]],
             "note": "Scales like this are commonly used in dermatology for patient-reported itch; your clinician may prefer a specific one. The sheet works with any of them."},
        ],
        "howto": ["Print the PDF and keep it by the bed — night is when itch is usually worst and least remembered.",
                  "Score itch 0–10 at fixed points (morning, afternoon, evening, bedtime) and whenever an episode stands out.",
                  "Note where on the body it was and whether you scratched, and estimate sleep lost in hours.",
                  "In What was happening, write the plain facts: heat, sweat, wool, hot shower, stress, new detergent, missed moisturizer.",
                  "After two to three weeks, bring the sheets to your dermatologist appointment."],
        "howto_names": ["Print the PDF", "Score itch at fixed times", "Record location and scratching", "Note the context", "Bring it to your appointment"],
        "faq": [FREE_FAQ,
                ["Is this a medical form?", "No. It is a personal record sheet to help you describe symptoms accurately. It does not diagnose, and it does not replace advice from a dermatologist or doctor."],
                ["How often should I fill it in?", "A few fixed times a day works better than 'whenever it itches', because it captures the quiet days too. Add extra rows for episodes that stand out."],
                ["Should I log itch if my skin looks clear?", "Yes — that is one of the most useful things the sheet records. Itch without visible flare is common and worth telling your clinician about."],
                ["Is there an app version?", "Yes — Skinote for iPhone logs flares, itch, triggers, and routine, and shows which factors cluster before your worse days. Core is free, no account needed, and your data stays on your device."]],
        "pdf_fields": ["Name", "Started"],
    },
    # ------------------------------------------------------------ GoutLog
    "gout-medication-log": {
        "app": "goutlog",
        "h1": "Free Printable Gout Medication Log (PDF) — Daily Dose & Uric Acid Record",
        "title": "Free Printable Gout Medication Log PDF — Dose Taken, Uric Acid & Flare Record",
        "desc": "A free one-page printable gout medication log. Record each day's medication and dose, time taken, uric acid results when tested, and whether a flare occurred — the adherence record your doctor needs when adjusting treatment. Not medical advice.",
        "answer": "This is a free, one-page printable gout medication log in PDF format. Each row is one day: the medication and dose, the time you took it, a tick that it was taken, any uric acid test result, whether you had a flare, and notes on side effects or missed doses. Urate-lowering treatment is adjusted on exactly two things — your blood results and whether you actually took the tablets — and both are easy to misremember across a three-month gap between appointments. This sheet is the record; it does not give medical advice or suggest doses.",
        "columns": ["Date", "Medication & dose", "Time", "Taken ✓", "Uric acid (if tested)", "Flare today?", "Notes / side effects"],
        "col_widths": [10, 20, 8, 8, 15, 11, 28],
        "sections": [
            {"h2": "What to record, and why it matters",
             "body": ["Doctors titrate gout medication to a uric acid target they set for you, checking blood levels every few weeks early on and then less often. A missed dose here and there is normal; what matters is that the record is honest, because an unexplained high result with a perfect tick column leads to a dose change that may not be needed. Write the target your clinician gave you in the header so every result on the sheet can be read against it.",
                      "Flares can occur in the first months after starting or changing urate-lowering treatment; that is a known pattern, not necessarily a sign the medication is failing. Logging flares alongside doses lets your clinician see the timing. If you are also prescribed a medication to take at the start of a flare, record that in the same row so the sequence is clear."],
             "bullets": ["Never change or stop a dose based on this sheet — bring it to the person who prescribed it.",
                         "Record side effects with dates; 'stomach upset after evening dose, 3 days' is more useful than 'felt off'.",
                         "Keep lab result printouts with the sheet; the sheet is a summary, not the source."]},
        ],
        "howto": ["Print the PDF — one page covers about three weeks — and keep it with your tablets.",
                  "Write the medication name and dose exactly as on the label, and the time you take it each day.",
                  "Tick Taken as you take it. Leave it blank on missed days rather than filling in later.",
                  "When you get a uric acid result, write the number and unit in that day's row; write your clinician's target in the header.",
                  "Mark flare days and note the joint, and bring the sheets to your next appointment."],
        "howto_names": ["Print the PDF", "Record medication and dose", "Tick each dose taken", "Add uric acid results", "Mark flares and bring it along"],
        "faq": [FREE_FAQ,
                ["Does this sheet tell me what dose to take?", "No. It only records what your clinician prescribed and what you took. Dose decisions belong to the prescriber, using your results and this record."],
                ["How often is uric acid tested?", "That is decided by your clinician — often every few weeks while a dose is being adjusted, then every several months once stable. Record whatever results you receive, with the unit (mg/dL or µmol/L)."],
                ["I had a flare after starting treatment. Should I stop?", "Talk to your prescriber before changing anything. Flares in the early months of urate-lowering treatment are a recognized pattern, and the log helps them see the timing."],
                ["Is there an app version?", "Yes — GoutLog for iPhone records doses, uric acid results, flares, and triggers, and charts levels over time against your target. Core is free, no account needed, and your data stays on your device."]],
        "pdf_fields": ["Name", "Target uric acid (from your doctor)"],
    },
    # ------------------------------------------------------------ MotorLog
    "tire-pressure-rotation-log": {
        "app": "motorlog",
        "h1": "Free Printable Tire Pressure & Rotation Log (PDF)",
        "title": "Free Printable Tire Pressure Log PDF — PSI, Tread Depth & Rotation Record",
        "desc": "A free one-page printable tire pressure and rotation log. Record all four tire pressures, tread depth, and rotations by date and odometer — plus where to find the correct PSI, tread depth guidance, and typical rotation intervals.",
        "answer": "This is a free, one-page printable tire log in PDF format. Each row is one check: date, odometer, the cold pressure of all four tires, tread depth or a rotation tick, and notes such as a slow leak or uneven wear. Tire pressure is the maintenance item with the biggest effect on fuel economy and safety and the smallest chance of being written down — a monthly row on this sheet shows which tire keeps losing air, when the last rotation was, and how fast the tread is going.",
        "columns": ["Date", "Odometer", "FL psi", "FR psi", "RL psi", "RR psi", "Tread / rotation", "Notes"],
        "col_widths": [10, 11, 8, 8, 8, 8, 17, 30],
        "sections": [
            {"h2": "How to check pressure so the numbers mean something",
             "body": ["Check cold — before driving, or after the car has sat for a few hours. Driving warms the tires and raises the reading by several psi, which is why a gas-station check after a highway run always looks fine. Use the pressure on the placard inside the driver's door jamb (or the owner's manual), not the 'max press' moulded on the tire sidewall; that number is the tire's limit, not the car's specification. Front and rear are sometimes different, which is why the sheet has four columns.",
                      "A tire that is consistently a few psi lower than its neighbors in the log is the one with the slow leak — a nail, a corroded wheel rim, or a valve stem. That pattern is invisible without a dated record, and it is the most common thing this sheet catches."]},
        ],
        "reference": [
            {"h2": "Reference values",
             "intro": "General guidance commonly given by tire makers and safety agencies. Your owner's manual and the door-jamb placard take priority.",
             "columns": ["Item", "Guidance", "Notes"],
             "rows": [["Correct pressure", "Door-jamb placard or owner's manual", "Not the sidewall maximum; front and rear may differ"],
                      ["Check interval", "Monthly, and before long trips", "Pressure drops roughly 1 psi per 10°F fall in temperature"],
                      ["Rotation interval", "Commonly every 5,000–8,000 miles (8,000–13,000 km), or with each oil change", "Follow the manual; some AWD vehicles are stricter"],
                      ["Tread depth — new", "Typically 10/32″ to 11/32″ for passenger tires", "Varies by tire type"],
                      ["Tread depth — replace soon", "4/32″ is a common wet-grip recommendation", "Penny/quarter tests approximate this"],
                      ["Tread depth — legal minimum", "2/32″ in most US states; 1.6 mm in the UK/EU", "Wear bars appear at this depth"]],
             "note": "Uneven wear across the four tread readings points to alignment, pressure, or rotation issues — note the pattern (inner edge, outer edge, center) in the Notes column."},
        ],
        "howto": ["Print the PDF and keep it in the glovebox with the tire gauge.",
                  "Once a month, before driving, check all four tires and write the pressures in the FL/FR/RL/RR columns with the odometer reading.",
                  "Adjust to the placard pressure and note how much each tire needed — a tire that always needs air is leaking.",
                  "Every few months, measure tread depth with a gauge at the inner, center, and outer tread and write the lowest reading.",
                  "When tires are rotated, write 'rotated' with the pattern used (front-to-back, cross) so the next one can be planned from the odometer."],
        "howto_names": ["Print the PDF", "Log pressures monthly", "Note tires that need air", "Measure tread depth", "Record each rotation"],
        "faq": [FREE_FAQ,
                ["What tire pressure should I use?", "The one on the placard inside the driver's door jamb or in the owner's manual, measured cold. The number on the tire sidewall is the maximum the tire can hold, not the recommended pressure for your car."],
                ["How often should tires be rotated?", "Many manufacturers suggest every 5,000 to 8,000 miles, or at each oil change; your manual is the authority. The log shows the odometer at the last rotation so you know when the next one is due."],
                ["Why does my tire pressure drop in winter?", "Air contracts as it cools — roughly 1 psi for every 10°F drop. A tire set correctly in September can be several psi low by December, which is why the sheet records the date alongside the readings."],
                ["Is there an app version?", "Yes — MotorLog for iPhone records tire pressure, rotations, service, and fuel by odometer and reminds you when the next rotation is due. Core is free, no account needed, and your data stays on your device."]],
        "pdf_fields": ["Vehicle", "Placard pressure (front / rear)"],
    },
    # ------------------------------------------------------------ PawLog
    "pet-weight-tracker": {
        "app": "pawlog",
        "h1": "Free Printable Pet Weight Tracker (PDF) — Dog & Cat Weight Log",
        "title": "Free Printable Pet Weight Tracker PDF — Dog & Cat Weight and Body Condition Log",
        "desc": "A free one-page printable pet weight tracker. Record your dog's or cat's weight, change since last time, body condition score, food portion, and activity — with a plain-words body condition guide and how often to weigh. Not veterinary advice.",
        "answer": "This is a free, one-page printable pet weight tracker in PDF format. Each row is one weigh-in: date, weight, change since the last entry, a 1–9 body condition score, what and how much your pet is eating, activity, and notes. Weight drifts slowly in pets — a pound on a cat is a lot, and it arrives one ounce at a time — so the sheet is built around the change column, which is where a problem shows first. Bring it to vet visits; the sheet records, your vet interprets.",
        "columns": ["Date", "Weight", "Change", "Body condition (1–9)", "Food / portion", "Activity", "Notes"],
        "col_widths": [10, 10, 9, 13, 20, 14, 24],
        "sections": [
            {"h2": "Weighing at home",
             "body": ["For cats and small dogs, weigh yourself on a bathroom scale, then weigh yourself holding the pet and subtract; it is good enough for tracking trend if you do it the same way each time. Large dogs are easier on the vet's walk-on scale — many clinics let you use it between visits. Weigh at the same time of day, before a meal, and write the weight in the same unit every time.",
                      "The Change column is the point of the sheet. A healthy adult pet's weight should hold roughly steady; a steady drift up or down over several entries, even by small amounts, is what to show your vet. Sudden loss with no change in food is worth a call rather than a wait."],
             "bullets": ["Puppies and kittens: weekly, because growth is fast and the vet will ask.",
                         "Healthy adults: about monthly.",
                         "Pets on a weight-management plan, seniors, or those with a medical condition: every one to two weeks, or as your vet asks."]},
        ],
        "reference": [
            {"h2": "Body condition score, in plain words",
             "intro": "Vets commonly use a 9-point body condition scale for dogs and cats. Ask your vet to show you how to score your own pet once — after that, you can track it at home.",
             "columns": ["Score", "Category", "What you see and feel"],
             "rows": [["1–3", "Underweight", "Ribs, spine, and hip bones easily seen; little or no fat cover; obvious waist and tuck"],
                      ["4–5", "Ideal", "Ribs easy to feel under a thin layer of fat but not visible; waist seen from above; belly tucks up from the side"],
                      ["6–7", "Overweight", "Ribs hard to feel under fat; waist barely visible or absent; belly starting to sag"],
                      ["8–9", "Obese", "Ribs cannot be felt under heavy fat; no waist; fat deposits on the back, base of tail, and abdomen"]],
             "note": "Coat length and breed shape make visual scoring unreliable — the feel of the ribs is the most consistent cue."},
        ],
        "howto": ["Print the PDF and keep it with the pet's vaccination record or on the fridge.",
                  "Weigh at the same time of day and in the same way each time, and write the weight and date.",
                  "Calculate the change from the previous row — that is the number to watch.",
                  "Score body condition from the table, and note the current food, portion size, and typical activity so changes can be explained.",
                  "Bring the sheet to every vet visit; mention any steady drift or sudden change."],
        "howto_names": ["Print the PDF", "Weigh consistently", "Track the change", "Score body condition", "Bring it to the vet"],
        "faq": [FREE_FAQ,
                ["What is a healthy weight for my dog or cat?", "It depends on breed, frame, and age, so there is no single number — body condition score is the better guide. Your vet can tell you the target for your pet; the sheet tracks progress toward it."],
                ["How much weight change is a concern?", "Any steady trend over several weigh-ins is worth mentioning to your vet, and unexplained loss of more than a few percent of body weight merits a call. The sheet does not set thresholds; your vet will."],
                ["Can I use this for other pets?", "Yes — rabbits, guinea pigs, and other small animals benefit even more from regular weighing because they hide illness. Use a kitchen scale and grams."],
                ["Is there an app version?", "Yes — PawLog for iPhone records weight, food, medication, and vet visits per pet and charts weight over time. Core is free, no account needed, and your data stays on your device."]],
        "pdf_fields": ["Pet", "Target weight (from your vet)"],
    },
    # ------------------------------------------------------------ Banneton
    "sourdough-starter-feeding-log": {
        "app": "banneton",
        "h1": "Free Printable Sourdough Starter Feeding Log (PDF)",
        "title": "Free Printable Sourdough Starter Feeding Log PDF — Ratio, Temperature & Peak Time",
        "desc": "A free one-page printable sourdough starter feeding log. Record each feed — date and time, ratio, flour, room temperature, time to peak, and how much it rose — with a table of common feeding ratios and what they do. No sign-up.",
        "answer": "This is a free, one-page printable sourdough starter feeding log in PDF format. Each row is one feeding: date and time, the ratio of starter to flour to water, which flour, the room temperature, how long it took to peak, how much it rose, and what it smelled and looked like. A starter is a schedule problem disguised as a baking problem — the same ratio peaks in four hours in July and nine in January — and the only way to know when yours will be ready is a record of what it did last time under the same conditions.",
        "columns": ["Date & time", "Ratio (S:F:W)", "Flour", "Room temp", "Time to peak", "Rise (×)", "Smell / look / notes"],
        "col_widths": [13, 11, 12, 9, 11, 8, 36],
        "sections": [
            {"h2": "What the log tells you after a week",
             "body": ["Peak time is the number bakers actually need: the window when the starter is at its strongest and should go into the dough. It depends on ratio, temperature, and flour, and the log pins down all three. After a week of entries at your kitchen's temperature you can predict peak within half an hour and plan a bake backward from it — feed at 9, mix at 2 — instead of hovering over the jar.",
                      "Rise is the health check. A starter that reliably doubles or more at peak is active; one that creeps to 1.5× and slumps may need warmer conditions, a few days of more frequent feeding, or a different flour. Smell belongs on the sheet too: yeasty and mildly sour at peak, sharper vinegar or acetone notes when it has gone past peak and is hungry."],
             "bullets": ["Mark the jar with a rubber band at the fed level so Rise (×) is a measurement, not an impression.",
                         "Log the temperature where the jar sits, not the thermostat — a windowsill and the top of the fridge can differ by 10°F.",
                         "Write the flour; whole wheat and rye ferment faster than white and change peak time."]},
        ],
        "reference": [
            {"h2": "Common feeding ratios and what they do",
             "intro": "Starter : flour : water by weight. Peak times are typical for a healthy starter around 75°F (24°C) and shift with temperature and flour — which is what the log is for.",
             "columns": ["Ratio", "Typical peak", "When bakers use it"],
             "rows": [["1:1:1", "About 4–6 hours", "Fast refresh before a bake; building a young starter; warm kitchens need two feeds a day"],
                      ["1:2:2", "About 6–8 hours", "Twice-daily maintenance; a bit more buffer than 1:1:1"],
                      ["1:3:3 to 1:5:5", "About 8–12 hours", "Overnight feed so the starter peaks in the morning; keeps acidity lower"],
                      ["1:10:10", "12 hours or more", "Very warm kitchens, or stretching feeds; taming an over-sour starter"],
                      ["Fridge storage", "—", "Feed, let it begin to rise, then refrigerate; refresh roughly weekly and give two or three room-temperature feeds before baking"]],
             "note": "Higher ratios (more fresh flour per gram of starter) take longer to peak and tend toward milder flavor; lower ratios are faster and more sour."},
        ],
        "howto": ["Print the PDF and keep it under the starter jar.",
                  "At each feed, write the time, the ratio by weight, the flour, and the temperature where the jar sits.",
                  "Put a rubber band at the fed level; when the dome starts to flatten, write the time to peak and the rise as a multiple.",
                  "Add a few words on smell and texture — yeasty, sour, acetone, soupy, stiff — so the row describes the starter and not just the clock.",
                  "Before a bake, find the most recent row at a similar temperature and plan the feed so the peak lands when you want to mix."],
        "howto_names": ["Print the PDF", "Record each feed", "Measure peak time and rise", "Note smell and texture", "Plan bakes from past peaks"],
        "faq": [FREE_FAQ,
                ["How often should I feed a sourdough starter?", "Kept at room temperature, usually once or twice a day depending on ratio and warmth; kept in the fridge, roughly weekly. The log shows how long your starter takes to peak and fall, which is the real answer to how often it needs feeding."],
                ["What does 1:1:1 mean?", "Equal weights of starter, flour, and water — for example 50 g starter, 50 g flour, 50 g water. The log records ratios by weight because volume measurements of flour are inconsistent."],
                ["My starter smells like nail polish remover. Is it dead?", "Almost certainly not. An acetone smell usually means it is hungry and has gone well past peak. Feed it at a higher ratio and log the next few feeds; the smell normally returns to yeasty-sour within a day or two."],
                ["Is there an app version?", "Yes — Banneton for iPhone logs starter feeds and bakes with timers for peak and proof, and keeps a hydration and temperature record per loaf. Core is free, no account needed, and your data stays on your device."]],
        "pdf_fields": ["Starter name", "Flour"],
    },
    # ------------------------------------------------------------ Combwise
    "hive-inspection-sheet": {
        "app": "combwise",
        "h1": "Free Printable Hive Inspection Sheet (PDF) — Beekeeping Record",
        "title": "Free Printable Hive Inspection Sheet PDF — Beekeeping Inspection Record & Checklist",
        "desc": "A free one-page printable hive inspection sheet. Record each inspection — date, hive, queen or eggs seen, brood pattern, stores, temperament, pests and mite counts, actions — with a checklist of what to look for and typical inspection timing.",
        "answer": "This is a free, one-page printable hive inspection sheet in PDF format. Each row is one inspection of one hive: date and conditions, whether you saw the queen or eggs, what the brood pattern looked like, honey and pollen stores, temperament, pests and varroa count, and what you did and plan to do next visit. Inspections are the heart of beekeeping records — the thing you notice at a hive is only useful if you can compare it with the last visit — and a one-line row per inspection is the format most beekeepers settle on. Blank columns are deliberate: a sheet that is fast to fill in at the hive gets filled in.",
        "columns": ["Date / weather", "Hive", "Queen / eggs", "Brood pattern", "Stores (honey / pollen)", "Temper", "Pests / mites", "Actions & next visit"],
        "col_widths": [11, 7, 11, 13, 14, 8, 13, 23],
        "sections": [
            {"h2": "When and how often to inspect",
             "body": ["During the active season most beekeepers open a hive every 7 to 10 days — often enough to catch swarm preparations, which take about that long from egg to capped queen cell, and seldom enough not to set the colony back. Inspect on a warm, calm, sunny day when foragers are out and the hive is calmer and emptier. In cold months, inspections are brief or skipped; heft the hive to judge stores instead and log that.",
                      "Keep the sheet short at the hive and add detail afterwards if needed. Eggs seen means the queen was present within the last three days even if you never saw her; that one tick replaces a long search. Write the varroa count from an alcohol wash or sugar roll as mites per 100 bees so visits are comparable — the varroa mite calculator on this site does the arithmetic."]},
        ],
        "reference": [
            {"h2": "What to check and what it usually means",
             "columns": ["Check", "Looks right", "Worth noting"],
             "rows": [["Queen / eggs", "Eggs standing upright in cells: queen laid within ~3 days", "No eggs or young larvae for two visits; multiple eggs per cell (laying workers)"],
                      ["Brood pattern", "Solid, compact capped brood with few empty cells", "Spotty pattern, sunken or perforated cappings, discolored larvae"],
                      ["Queen cells", "None, or a few play cups", "Charged swarm cells along frame bottoms; supersedure cells on the face"],
                      ["Stores", "Band of pollen and honey around the brood; frames of capped honey", "Light hive going into dearth or winter; no pollen"],
                      ["Space", "Bees covering most frames with room to expand", "Bearding and congestion (add space); too much empty space in a weak hive"],
                      ["Temperament", "Calm bees, little following", "Sudden defensiveness: queenless, dearth, robbing, or weather"],
                      ["Pests / disease", "Few hive beetles, no wax moth webbing, mite count low", "Rising mite count; deformed wings; beetles in numbers; foul smell"]],
             "note": "Thresholds and treatment choices vary by region and season — use your local association's guidance. The sheet records what you saw; it does not prescribe treatment."},
        ],
        "howto": ["Print the PDF — one sheet per hive, or one shared sheet for a small apiary — and keep it in the toolbox or on a clipboard.",
                  "Before opening, write the date, weather, and what you intend to check; after, fill the row while it is fresh.",
                  "Tick Queen or Eggs; note the brood pattern in a word or two (solid, spotty); estimate stores in frames.",
                  "Record mite counts as mites per 100 bees from a wash or roll, and any pests seen.",
                  "Finish with what you did (added a super, swapped frames) and what the next visit should check."],
        "howto_names": ["Print the PDF", "Note date and conditions", "Record queen, brood, stores", "Log mites and pests", "Write actions and next visit"],
        "faq": [FREE_FAQ,
                ["How often should I inspect a beehive?", "Roughly every 7 to 10 days during the active season, less often in cool weather and rarely in winter. The interval matters for swarm control — a capped queen cell can appear within about eight days of the egg being laid."],
                ["Do I need to find the queen every time?", "No. Eggs are proof the queen was laying within the last three days. Most experienced beekeepers look for eggs and young larvae and only search for the queen when they need to mark, move, or replace her."],
                ["How do I record a varroa count?", "As mites per 100 bees from an alcohol wash or sugar roll — a half cup of bees is about 300, so divide the mites found by three. The varroa mite calculator on this site does the conversion."],
                ["Is there an app version?", "Yes — Combwise for iPhone records inspections per hive, mite counts, treatments, and feeding, and reminds you when the next inspection is due. Core is free, no account needed, and your data stays on your device."]],
        "pdf_fields": ["Apiary", "Season"],
    },
}
d["templates"].update(OTHERS)
d["apps"]["banneton"]["template"] = "sourdough-starter-feeding-log"
d["apps"]["combwise"]["template"] = "hive-inspection-sheet"

# ---------------------------------------------------------------- guide rework
g = d["guides"]["plywood-cut-calculator"]
g["keyword"] = "plywood cut list calculator"
g["h1"] = "Plywood Cut List Calculator: How Many 4×8 Sheets Your Parts Need"
g["title"] = "Plywood Cut List Calculator — 4x8 Sheet Count, Kerf & Layout (Free)"
g["desc"] = "Free plywood cut list calculator: enter your parts, get the 4×8 sheet count and a cutting diagram. Plus the quick 32-square-foot estimate, and why kerf, trim, and grain make it undercount."
g["lede"] = "Enter your parts and get a sheet count with a cutting layout from the free cut list optimizer below. If you would rather estimate by hand first, this guide gives the quick area method and then the corrections that turn it into a number you can buy from."
g["answer"] = "Quick answer: a 4×8 sheet is 32 square feet, so total part area ÷ 32, rounded up, is the fewest sheets the job could possibly use. Real jobs need more — a saw kerf of about 1/8″ per cut, edge trim, grain direction, and rectangles that do not tile perfectly. The free calculator on this site places your actual parts on 48×96 stock with kerf and reports the sheet count, a cutting diagram, and yield. Use that number for the shopping list, not the area estimate."
g["quick_tool"] = {"path": "/tools/cut-list-optimizer/",
                   "label": "Open the free plywood cut list calculator",
                   "note": "Runs in your browser. Enter 48 × 96 stock, your parts, and kerf; free for up to 10 parts, nothing sent to a server."}
g["sections"].insert(0, {
    "h2": "Use the calculator for a 4×8 sheet",
    "body": ["Add one stock line of 48 × 96 inches — or 47½ × 95½ if you plan to trim the factory edges — and set the kerf to the width of your blade, typically 1/8″ (0.125) for a table saw or track saw. Enter each part as width × length × quantity, and lock the grain on any part whose face will show. The optimizer lays the parts out on as many sheets as they need and reports the count, the yield, and a diagram you can print or take to the saw.",
             "If the count is one sheet higher than you hoped, look at the diagram before buying: a part that is 1/8″ too wide to share a rip with its neighbor is the usual culprit, and trimming it, rotating it, or changing the cut order can bring the job back onto fewer sheets."],
    "bullets": ["Stock: 48 × 96 (nominal) or the measured size after edge trim",
                "Kerf: your blade's width, usually 0.125 in. — not zero",
                "Parts: finished size and quantity; add grain locks for visible faces",
                "Read: sheet count, yield, and the cutting diagram"]})
g["sections"][1]["h2"] = "Estimate by hand: the 32-square-foot method"
g["faq"].insert(0, ["Is there a free plywood cut list calculator?",
                    "Yes — the cut list optimizer on this site is free in the browser for up to 10 parts, kerf-aware, and produces a cutting diagram for 4×8 or any custom sheet size. The Boardcut app does the same on iPhone with no part limit."])
g["faq"].append(["How many 24×24 panels fit on a 4×8 sheet?",
                 "By area, eight. In practice, two 24″ panels plus one kerf need 48⅛″, which is wider than the sheet, so only one row of four fits unless you accept 23⅞″ panels or trim after cutting. That gap between area math and layout is exactly what the calculator catches."])
g["related_pages"] = [
    {"path": "/tools/cut-list-optimizer/", "title": "Cut list optimizer", "kind": "Free web tool"},
    {"path": "/templates/plywood-cutting-diagram/", "title": "Plywood Cutting Diagram Template", "kind": "Free printable PDF"},
    {"path": "/templates/cut-list-template/", "title": "Cut List Template", "kind": "Free printable PDF"},
]

f.write_text(json.dumps(d, ensure_ascii=False, indent=2))
print("part 3 written:", list(OTHERS), "+ guide reworked")
