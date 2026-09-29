import os
import json
import random
import math
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

random.seed(42)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(DATA_DIR, "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)

# Select best available font
FONT_PATH = "C:/Windows/Fonts/Nirmala.ttc"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "C:/Windows/Fonts/arial.ttf"


def get_font(size: int, is_bold: bool = False):
    try:
        idx = 1 if is_bold and FONT_PATH.endswith(".ttc") else 0
        return ImageFont.truetype(FONT_PATH, size=size, index=idx)
    except Exception:
        try:
            return ImageFont.truetype(FONT_PATH, size=size)
        except Exception:
            return ImageFont.load_default()


def add_degradations(img: Image.Image, degradation_type: str, rng: random.Random) -> Image.Image:
    """Applies realistic physical land record degradations."""
    img = img.convert("RGBA")
    w, h = img.size

    if degradation_type == "faded_ink":
        # Low contrast, elevated brightness
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(0.55)
        bright = ImageEnhance.Brightness(img)
        img = bright.enhance(1.15)

    elif degradation_type == "blur":
        img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(1.2, 2.2)))

    elif degradation_type == "stains":
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        # Generate 3-5 organic stain blobs
        for _ in range(rng.randint(3, 5)):
            cx = rng.randint(50, w - 50)
            cy = rng.randint(50, h - 50)
            rad_x = rng.randint(40, 110)
            rad_y = rng.randint(30, 90)
            color = (rng.randint(160, 190), rng.randint(130, 160), rng.randint(90, 120), rng.randint(45, 95))
            draw.ellipse([cx - rad_x, cy - rad_y, cx + rad_x, cy + rad_y], fill=color)
        img = Image.alpha_composite(img, overlay)

    elif degradation_type == "torn_corner":
        draw = ImageDraw.Draw(img)
        corner_points = [(w, 0), (w - rng.randint(80, 140), 0), (w, rng.randint(80, 140))]
        draw.polygon(corner_points, fill=(245, 240, 230, 255))
        # Add jagged edge line
        draw.line([(w - 120, 0), (w - 70, 40), (w - 20, 90), (w, 130)], fill=(180, 170, 155, 255), width=2)

    elif degradation_type == "skew":
        angle = rng.uniform(-2.8, 2.8)
        img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(250, 248, 240, 255))

    elif degradation_type == "low_resolution":
        small = img.resize((w // 2, h // 2), resample=Image.BILINEAR)
        img = small.resize((w, h), resample=Image.NEAREST)

    elif degradation_type == "handwritten_overlay":
        draw = ImageDraw.Draw(img)
        font = get_font(18)
        note_y = rng.randint(h - 180, h - 80)
        draw.text((60, note_y), "नोंद प्रमाणित / Verified by Revenue Inspector 14/03/1998", fill=(20, 40, 110, 200), font=font)
        draw.line([(55, note_y + 24), (420, note_y + 26)], fill=(20, 40, 110, 180), width=2)

    return img.convert("RGB")


def apply_overwritten_digit_tampering(img: Image.Image, box: List[int]):
    """Simulates ink overwriting of a survey number digit."""
    draw = ImageDraw.Draw(img)
    x, y = box[0], box[1]
    # Draw original digit then heavy dark stroke over it
    font = get_font(26, is_bold=True)
    draw.text((x, y), "7", fill=(30, 30, 30), font=font)
    draw.line([(x + 2, y + 2), (x + 18, y + 26)], fill=(5, 5, 10), width=4)
    draw.text((x + 1, y), "9", fill=(0, 0, 0), font=font)


def apply_pasted_stamp_tampering(img: Image.Image, box: List[int]):
    """Simulates a pasted-in stamp/date with misaligned border and noise anomaly."""
    x, y, w, h = box[0], box[1], box[2], box[3]
    stamp_crop = Image.new("RGBA", (w, h), (235, 245, 235, 230))
    sdraw = ImageDraw.Draw(stamp_crop)
    sdraw.rectangle([0, 0, w - 1, h - 1], outline=(150, 60, 60, 255), width=2)
    sdraw.text((10, 8), "GOVT STAMP / FEB 2015", fill=(160, 30, 30, 240), font=get_font(14, is_bold=True))
    img.paste(stamp_crop, (x, y), stamp_crop)


def generate_dataset():
    records_metadata = []
    fault_distribution = {
        3: "shares_not_summing_to_1",
        7: "mutation_dated_before_registration",
        11: "sale_area_exceeding_holding",
        14: "owner_acting_after_death",
        18: "duplicate_survey_conflict",
        22: "overwritten_digits",
        25: "pasted_stamp_tampering",
        27: "shares_not_summing_to_1",
        29: "missing_na_conversion_order",
    }

    villages_by_lang = {
        "hindi": [
            ("Bargadi", "Bakshi Ka Talab", "Lucknow", "Uttar Pradesh", "बड़गड़ी", "बख्शी का तालाब", "लखनऊ"),
            ("Asthi", "Bakshi Ka Talab", "Lucknow", "Uttar Pradesh", "अस्थी", "बख्शी का तालाब", "लखनऊ"),
            ("Sindhora", "Pindra", "Varanasi", "Uttar Pradesh", "सिंधोरा", "पिंडरा", "वाराणसी"),
            ("Khagaul", "Danapur", "Patna", "Bihar", "खगौल", "दानापुर", "पटना")
        ],
        "marathi": [
            ("Wagholi", "Haveli", "Pune", "Maharashtra", "वाघोली", "हवेली", "पुणे"),
            ("Pirangut", "Mulshi", "Pune", "Maharashtra", "पिरंगुट", "मुळशी", "पुणे"),
            ("Kharadi", "Haveli", "Pune", "Maharashtra", "खराडी", "हवेली", "पुणे"),
            ("Chakan", "Khed", "Pune", "Maharashtra", "चाकण", "खेड", "पुणे")
        ],
        "english": [
            ("Wagholi", "Haveli", "Pune", "Maharashtra"),
            ("Bargadi", "Bakshi Ka Talab", "Lucknow", "Uttar Pradesh"),
            ("Pirangut", "Mulshi", "Pune", "Maharashtra"),
            ("Khagaul", "Danapur", "Patna", "Bihar")
        ]
    }

    first_names_hi = ["रामेश्वर", "सुरेश", "राजेश", "कमला", "अशोक", "दिनेश", "महेश", "सुनीता"]
    last_names_hi = ["शर्मा", "वर्मा", "सिंह", "यादव", "गुप्ता", "मिश्रा", "पांडेय", "चौहान"]
    first_names_mr = ["रमेश", "ज्ञानेश्वर", "दत्तात्रेय", "बाबूराव", "विठ्ठल", "सुभाष", "आनंद", "सुप्रिया"]
    last_names_mr = ["पाटील", "देशमुख", "पवार", "कुलकर्णी", "शिंदे", "जाधव", "चव्हाण", "मोरे"]
    first_names_en = ["Ramesh", "Suresh", "Rajesh", "Ganesh", "Ashok", "Kiran", "Dattatraya", "Sunita"]
    last_names_en = ["Patil", "Deshmukh", "Sharma", "Verma", "Pawar", "Kulkarni", "Singh", "Yadav"]

    doc_types = ["khatauni_7_12", "mutation_register", "sale_deed"]
    degradations = ["none", "faded_ink", "blur", "stains", "torn_corner", "skew", "low_resolution", "handwritten_overlay"]

    for i in range(1, 31):
        rng = random.Random(42 + i)
        fault_type = fault_distribution.get(i, None)
        has_fault = fault_type is not None

        if i <= 10:
            lang = "hindi"
            doc_type = doc_types[(i - 1) % 3]
            v_info = rng.choice(villages_by_lang["hindi"])
            v_en, t_en, d_en, s_en, v_reg, t_reg, d_reg = v_info
            owner1 = f"{rng.choice(first_names_hi)} {rng.choice(last_names_hi)}"
            owner2 = f"{rng.choice(first_names_hi)} {rng.choice(last_names_hi)}"
            father1 = f"{rng.choice(first_names_hi)} {rng.choice(last_names_hi)}"
            area_unit = "bigha"
            area_val = round(rng.uniform(1.0, 3.5), 2)
            land_class = "सिंचित (Chahi)"
        elif i <= 20:
            lang = "marathi"
            doc_type = doc_types[(i - 11) % 3]
            v_info = rng.choice(villages_by_lang["marathi"])
            v_en, t_en, d_en, s_en, v_reg, t_reg, d_reg = v_info
            owner1 = f"{rng.choice(first_names_mr)} {rng.choice(last_names_mr)}"
            owner2 = f"{rng.choice(first_names_mr)} {rng.choice(last_names_mr)}"
            father1 = f"{rng.choice(first_names_mr)} {rng.choice(last_names_mr)}"
            area_unit = "guntha"
            area_val = round(rng.uniform(15.0, 60.0), 1)
            land_class = "जिरायत (Jirayat)"
        else:
            lang = "english"
            doc_type = doc_types[(i - 21) % 3]
            v_en, t_en, d_en, s_en = rng.choice(villages_by_lang["english"])
            v_reg, t_reg, d_reg = v_en, t_en, d_en
            owner1 = f"{rng.choice(first_names_en)} {rng.choice(last_names_en)}"
            owner2 = f"{rng.choice(first_names_en)} {rng.choice(last_names_en)}"
            father1 = f"{rng.choice(first_names_en)} {rng.choice(last_names_en)}"
            area_unit = "acre"
            area_val = round(rng.uniform(1.2, 4.0), 2)
            land_class = "irrigated"

        survey_no = f"{100 + i}" if fault_type != "duplicate_survey_conflict" else "101"
        khata_no = f"{50 + (i * 3)}"
        reg_no = f"REG-2021-{3000 + i}"
        reg_date = f"2021-0{rng.randint(3, 8)}-{rng.randint(10, 28)}"
        mut_no = f"M-{800 + i}"
        mut_date = f"2021-09-{rng.randint(10, 28)}"

        # Compute shares
        if fault_type == "shares_not_summing_to_1":
            share1, share2 = (0.4, 0.4) if i == 3 else (0.6, 0.6)
            share_raw1, share_raw2 = ("2/5", "2/5") if i == 3 else ("3/5", "3/5")
        else:
            share1, share2 = 0.5, 0.5
            share_raw1, share_raw2 = "1/2", "1/2"

        # Temporal fault
        if fault_type == "mutation_dated_before_registration":
            mut_date = "2020-02-15"
            reg_date = "2020-08-20"

        # Area fault
        holding_area_sqm = round(area_val * (2529.29 if area_unit == "bigha" else 101.17 if area_unit == "guntha" else 4046.86), 2)
        transferred_area = holding_area_sqm * 1.5 if fault_type == "sale_area_exceeding_holding" else round(holding_area_sqm * 0.5, 2)

        # Deceased fault
        is_deceased = fault_type == "owner_acting_after_death"
        date_of_death = "2019-03-10" if is_deceased else None

        # NA Conversion fault
        if fault_type == "missing_na_conversion_order":
            land_class = "commercial non_agricultural"

        # Generate Document Canvas (A4 aspect: 1200 x 1650)
        img = Image.new("RGB", (1200, 1650), color=(252, 250, 242))
        draw = ImageDraw.Draw(img)

        # Draw vintage parchment borders
        draw.rectangle([40, 40, 1160, 1610], outline=(120, 100, 80), width=3)
        draw.rectangle([46, 46, 1154, 1604], outline=(180, 160, 140), width=1)

        # Header Titles
        f_title = get_font(32, is_bold=True)
        f_sub = get_font(20, is_bold=True)
        f_body = get_font(18)
        f_table = get_font(16)

        if lang == "hindi":
            hdr1 = "उत्तर प्रदेश राजस्व परिषद / Department of Revenue"
            hdr2 = "प्रारूप ४५ (खतौनी नकल / Khatauni Extract)" if doc_type == "khatauni_7_12" else "नामांतरण पंजी (Mutation Register)" if doc_type == "mutation_register" else "बैनामा सारांश (Sale Deed Summary)"
        elif lang == "marathi":
            hdr1 = "महाराष्ट्र शासन महसूल विभाग / Revenue Dept. Maharashtra"
            hdr2 = "गाव नमुना ७/१२ (अधिकार अभिलेख पत्रक)" if doc_type == "khatauni_7_12" else "गाव नमुना ६ (फेरफार नोंदवही / Mutation)" if doc_type == "mutation_register" else "खरेदीखत सारांश (Sale Deed)"
        else:
            hdr1 = "Government of India - Department of Land Resources"
            hdr2 = "Record of Rights (Khatauni Extract)" if doc_type == "khatauni_7_12" else "Land Mutation Register Entry" if doc_type == "mutation_register" else "Registered Conveyance Deed Summary"

        draw.text((600, 80), hdr1, fill=(20, 30, 80), font=f_title, anchor="mt")
        draw.text((600, 130), hdr2, fill=(100, 30, 20), font=f_sub, anchor="mt")
        draw.line([(80, 175), (1120, 175)], fill=(120, 100, 80), width=2)

        # Top Metadata Grid
        curr_y = 200
        row1_text = f"District / जिल्हा / ज़िला: {d_reg} ({d_en})  |  Tehsil / तालुका / तहसील: {t_reg} ({t_en})"
        row2_text = f"Village / गाव / ग्राम: {v_reg} ({v_en})  |  State: {s_en}"
        row3_text = f"Survey/Khasra/गट क्र.: {survey_no}  |  Khata/खाते क्र.: {khata_no}  |  Land Class: {land_class}"
        draw.text((80, curr_y), row1_text, fill=(30, 30, 30), font=f_body)
        draw.text((80, curr_y + 35), row2_text, fill=(30, 30, 30), font=f_body)
        draw.text((80, curr_y + 70), row3_text, fill=(30, 30, 30), font=f_body)
        curr_y += 130

        # Table Header
        draw.rectangle([80, curr_y, 1120, curr_y + 45], fill=(235, 230, 218), outline=(100, 90, 80), width=2)
        th_font = get_font(17, is_bold=True)
        draw.text((100, curr_y + 12), "Sr.", fill=(10, 10, 10), font=th_font)
        draw.text((160, curr_y + 12), "Owner / खातेदार / जमीनदार", fill=(10, 10, 10), font=th_font)
        draw.text((500, curr_y + 12), "Father/Spouse", fill=(10, 10, 10), font=th_font)
        draw.text((780, curr_y + 12), "Share / हिस्सा", fill=(10, 10, 10), font=th_font)
        draw.text((950, curr_y + 12), "Area / क्षेत्रफळ", fill=(10, 10, 10), font=th_font)
        curr_y += 45

        # Row 1
        draw.rectangle([80, curr_y, 1120, curr_y + 50], outline=(150, 140, 130), width=1)
        draw.text((100, curr_y + 14), "1", fill=(20, 20, 20), font=f_table)
        draw.text((160, curr_y + 14), owner1 + (" (मृत्यु नोंद)" if is_deceased else ""), fill=(20, 20, 20), font=f_table)
        draw.text((500, curr_y + 14), father1, fill=(20, 20, 20), font=f_table)
        draw.text((780, curr_y + 14), f"{share_raw1} ({share1})", fill=(20, 20, 20), font=f_table)
        draw.text((950, curr_y + 14), f"{area_val} {area_unit}", fill=(20, 20, 20), font=f_table)
        curr_y += 50

        # Row 2
        draw.rectangle([80, curr_y, 1120, curr_y + 50], outline=(150, 140, 130), width=1)
        draw.text((100, curr_y + 14), "2", fill=(20, 20, 20), font=f_table)
        draw.text((160, curr_y + 14), owner2, fill=(20, 20, 20), font=f_table)
        draw.text((500, curr_y + 14), "Late Shri S. Rao", fill=(20, 20, 20), font=f_table)
        draw.text((780, curr_y + 14), f"{share_raw2} ({share2})", fill=(20, 20, 20), font=f_table)
        draw.text((950, curr_y + 14), f"{area_val} {area_unit}", fill=(20, 20, 20), font=f_table)
        curr_y += 75

        # Mutation & Transaction Details Box
        draw.rectangle([80, curr_y, 1120, curr_y + 260], fill=(248, 246, 238), outline=(120, 110, 100), width=1)
        draw.text((100, curr_y + 15), "नक्कल / नोंदणी व फेरफार तपशील (Transaction & Mutation Record):", fill=(40, 30, 20), font=th_font)
        m_lines = [
            f"• Mutation No. / फेरफार क्र.: {mut_no}   |   Mutation Date: {mut_date}",
            f"• Registration No.: {reg_no}   |   Deed Registration Date: {reg_date}",
            f"• Transferor (From): {owner1}   --->   Transferee (To): {owner2}",
            f"• Transferred Extent: {transferred_area} sq m (Holding: {holding_area_sqm} sq m)",
            f"• Revenue Order Ref: REV/SDO/{t_en.upper()}/2021/894" if fault_type != "missing_na_conversion_order" else "• NA Conversion: Applied (Order pending / no reference)",
            f"• ULPIN / Bhu-Aadhaar: 27HA100100{100+i:04d}"
        ]
        for m_idx, ml in enumerate(m_lines):
            draw.text((110, curr_y + 55 + (m_idx * 32)), ml, fill=(40, 40, 40), font=f_table)
        curr_y += 290

        # Official Stamps & Seals
        draw.rectangle([80, curr_y, 450, curr_y + 140], outline=(70, 90, 140), width=2)
        draw.text((100, curr_y + 15), "तलाठी / Revenue Inspector Seal", fill=(70, 90, 140), font=th_font)
        draw.text((100, curr_y + 50), f"Digital RoR Certified Copy\nDate: {reg_date}\nSub-Division: {t_en}", fill=(50, 70, 120), font=f_table)

        draw.rectangle([750, curr_y, 1120, curr_y + 140], outline=(140, 60, 60), width=2)
        draw.text((770, curr_y + 15), "तहसीलदार कार्यालय / Tehsildar Seal", fill=(140, 60, 60), font=th_font)
        draw.text((770, curr_y + 50), "Certified & Verified Record\nUnder Section 148 Land Revenue Code", fill=(120, 40, 40), font=f_table)

        # Apply Injected Visual Tampering
        if fault_type == "overwritten_digits":
            apply_overwritten_digit_tampering(img, [340, 270])
        elif fault_type == "pasted_stamp_tampering":
            apply_pasted_stamp_tampering(img, [500, curr_y + 10, 220, 100])

        # Apply Physical Degradation
        deg_type = degradations[(i - 1) % len(degradations)]
        final_img = add_degradations(img, deg_type, rng)

        # Save Image
        img_filename = f"record_{i:02d}.png"
        img_path = os.path.join(SAMPLES_DIR, img_filename)
        final_img.save(img_path, "PNG")

        # Compile Ground Truth Entry
        gt_entry = {
            "id": f"BHU-REC-{i:03d}",
            "filename": img_filename,
            "language": lang,
            "document_type": doc_type,
            "degradation": deg_type,
            "has_fault": has_fault,
            "injected_fault": fault_type,
            "ground_truth": {
                "state": s_en,
                "district": d_en,
                "tehsil": t_en,
                "village": v_en,
                "survey_no": survey_no,
                "khata_no": khata_no,
                "land_classification": "non_agricultural" if "commercial" in land_class else "irrigated" if "सिंचित" in land_class or "irrigated" in land_class else "unirrigated_dry",
                "plot_area": {
                    "value": area_val,
                    "unit": area_unit,
                    "area_sqm": holding_area_sqm,
                    "area_hectares": round(holding_area_sqm / 10000.0, 4)
                },
                "owners": [
                    {"name": owner1, "share": share1, "is_deceased": is_deceased, "date_of_death": date_of_death},
                    {"name": owner2, "share": share2, "is_deceased": False}
                ],
                "mutation": {
                    "mutation_no": mut_no,
                    "mutation_date": mut_date,
                    "registration_date": reg_date,
                    "transferred_area_sqm": transferred_area,
                    "holding_area_sqm": holding_area_sqm
                },
                "registration": {
                    "reg_no": reg_no,
                    "reg_date": reg_date
                },
                "ulpin": f"27HA100100{100+i:04d}"
            }
        }
        records_metadata.append(gt_entry)

    # Save Ground Truth JSON
    gt_path = os.path.join(DATA_DIR, "ground_truth.json")
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump({"total_records": len(records_metadata), "records": records_metadata}, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {len(records_metadata)} land record samples and ground_truth.json!")


if __name__ == "__main__":
    generate_dataset()
