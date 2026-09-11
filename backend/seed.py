import uuid
from datetime import datetime, timedelta
from database import get_db

def seed():
    conn = get_db()
    cursor = conn.cursor()

    # Clear existing data safely
    tables = [
        "audit_logs", "weather_records", "support_tickets", "notifications",
        "slot_redirections", "payments", "j_forms", "unloading_records",
        "unloading_bays", "quality_inspections", "weighments", "queue_entries",
        "gate_checkins", "token_status_history", "slot_bookings",
        "procurement_slots", "farmer_documents", "land_records",
        "farmer_profiles", "crops", "seasons", "centers", "sessions",
        "otp_sessions", "users"
    ]
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")

    # 1. Centers
    centers = [
        ("CTR-KRN", "Karnal Procurement Hub", "Karnal", "Haryana", 29.6857, 76.9905, 300, 3, 5, 1),
        ("CTR-KHN", "Khanna Grain Mandi Hub", "Ludhiana", "Punjab", 30.7068, 76.2201, 350, 4, 6, 1),
        ("CTR-BHP", "Bhopal Central Mandi", "Bhopal", "Madhya Pradesh", 23.2599, 77.4126, 280, 2, 4, 1),
        ("CTR-KTA", "Kota Bhamashah Mandi", "Kota", "Rajasthan", 25.1834, 75.8648, 320, 3, 5, 1),
        ("CTR-NZB", "Nizamabad Agricultural Hub", "Nizamabad", "Telangana", 18.6725, 78.0941, 260, 2, 4, 1),
        ("CTR-PNP", "Panipat Procurement Hub", "Panipat", "Haryana", 29.3909, 76.9635, 300, 2, 4, 1),
        ("CTR-SNP", "Sonipat Center", "Sonipat", "Haryana", 28.9931, 77.0151, 260, 2, 4, 1),
        ("CTR-RTK", "Rohtak Mandi Center", "Rohtak", "Haryana", 28.8955, 76.6066, 280, 2, 4, 1)
    ]
    cursor.executemany("""
    INSERT INTO centers (id, name, district, state, latitude, longitude, daily_capacity, weighbridges, unloading_bays, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, centers)

    # 2. Seasons & Crops
    season_id = "SSN-RABI-2026"
    cursor.execute("INSERT INTO seasons (id, name, year, is_active) VALUES (?, ?, ?, ?)", (season_id, "रबी विपणन वर्ष 2026-27 (Rabi 2026)", 2026, 1))

    crops = [
        ("CRP-WHT", "Wheat", "गेहूं", season_id, 2275.00, 12.0, 25.0),
        ("CRP-PDY", "Paddy", "धान", season_id, 2320.00, 17.0, 30.0),
        ("CRP-MST", "Mustard", "सरसों", season_id, 5650.00, 8.0, 15.0),
        ("CRP-GRM", "Gram", "चना", season_id, 5440.00, 10.0, 18.0),
        ("CRP-MAZ", "Maize", "मक्का", season_id, 2090.00, 14.0, 25.0)
    ]
    cursor.executemany("""
    INSERT INTO crops (id, name, hindi_name, season_id, msp_rate, max_moisture, max_quota_per_acre)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, crops)

    # 3. Users (Farmers, Officers, Admin)
    users = [
        # Farmer 1
        ("USR-FARMER-01", "9876543210", "राम कुमार (Ram Kumar)", "FARMER", None, None),
        # Farmer 2
        ("USR-FARMER-02", "9876543211", "गुरप्रीत सिंह (Gurpreet Singh)", "FARMER", None, None),
        # Farmer 3
        ("USR-FARMER-03", "9876543212", "सुरेश वर्मा (Suresh Verma)", "FARMER", None, None),
        # Farmer 4 (Pending KYC)
        ("USR-FARMER-04", "9876543213", "अमित पटेल (Amit Patel)", "FARMER", None, None),
        # Officers
        ("USR-OFFICER-01", "9998887771", "A. Sharma", "OFFICER", "Ministry of Consumer Affairs, Food and Public Distribution", "OFF-HR-701"),
        ("USR-OFFICER-02", "9998887772", "R. K. Meena", "OFFICER", "Department of Agriculture", "OFF-RJ-502"),
        # Admin
        ("USR-ADMIN-01", "9999999999", "State Procurement Director", "ADMIN", "Ministry of Consumer Affairs, Food and Public Distribution", "ADM-GOI-001")
    ]
    cursor.executemany("""
    INSERT INTO users (id, mobile, name, role, department, official_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """, users)

    # 4. Farmer Profiles
    farmers = [
        (
            "FARMER-01", "USR-FARMER-01", "FID-HR-2026-001", "BAARI-2026-101001",
            "राम कुमार", "श्री रामेश्वर", "1978-05-12", "पुरुष", "सामान्य",
            "Aadhaar", "XXXX-XXXX-7429", "ग्राम तरावड़ी, डाकघर नीलोखेड़ी",
            "हरियाणा", "Karnal", "Nilokheri", "Taraori", "owner",
            "XXXXXX4820", "SBIN0001234", "APPROVED", "भूमि अभिलेख एवं आधार सत्यापित", "USR-OFFICER-01", "2026-08-15 10:30:00"
        ),
        (
            "FARMER-02", "USR-FARMER-02", "FID-PB-2026-002", "BAARI-2026-101002",
            "गुरप्रीत सिंह", "श्री हरजिंदर सिंह", "1983-11-20", "पुरुष", "सामान्य",
            "Aadhaar", "XXXX-XXXX-8910", "गांव खन्ना कलां, तहसील खन्ना",
            "पंजाब", "Ludhiana", "Khanna", "Khanna Kalan", "tenant",
            "XXXXXX7741", "PUNB0045678", "APPROVED", "किरायेदारी समझौता व खाता सत्यापित", "USR-OFFICER-01", "2026-08-16 11:45:00"
        ),
        (
            "FARMER-03", "USR-FARMER-03", "FID-MP-2026-003", "BAARI-2026-101003",
            "सुरेश वर्मा", "श्री मदनलाल", "1989-02-14", "पुरुष", "OBC",
            "Aadhaar", "XXXX-XXXX-3341", "ग्राम बैरसिया, जिला भोपाल",
            "मध्य प्रदेश", "Bhopal", "Berasia", "Berasia Khas", "owner",
            "XXXXXX9012", "BARB0BERASI", "APPROVED", "खसरा 142/1 सत्यापित", "USR-OFFICER-02", "2026-08-18 14:15:00"
        ),
        (
            "FARMER-04", "USR-FARMER-04", None, "BAARI-2026-101004",
            "अमित पटेल", "श्री कांतिलाल पटेल", "1992-07-28", "पुरुष", "सामान्य",
            "Aadhaar", "XXXX-XXXX-6512", "ग्राम सुल्तानपुर, तहसील दिगोद",
            "राजस्थान", "Kota", "Digod", "Sultanpur", "sharecropper",
            "XXXXXX3154", "BKID0001122", "PENDING", None, None, None
        )
    ]
    cursor.executemany("""
    INSERT INTO farmer_profiles (
        id, user_id, farmer_id, application_id, full_name, guardian_name,
        dob, gender, category, identity_type, identity_number, address,
        state, district, tehsil, village, cultivation_type, bank_account,
        ifsc_code, verification_status, verification_remarks, verified_by, verified_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, farmers)

    # 5. Land Records
    land_records = [
        ("LND-01", "FARMER-01", "248/1, 248/2", "KH-881", 4.5, 4.0, 3.5, 0.5, "Wheat", "ट्यूबवेल", 20, "उच्च उत्पादक सिंचित भूमि"),
        ("LND-02", "FARMER-02", "112/5", "KH-420", 3.0, 2.8, 2.5, 0.3, "Wheat", "नहर", 15, "किरायेदारी भूमि 5 वर्ष लीज"),
        ("LND-03", "FARMER-03", "94/2", "KH-619", 5.0, 4.5, 3.8, 0.7, "Gram", "बोरवेल", 12, "सोयाबीन चक्र के बाद चना"),
        ("LND-04", "FARMER-04", "315/7", "KH-102", 2.5, 2.0, 1.5, 0.5, "Mustard", "कुआं", 8, "बटाईदार 50-50 अनुबंध")
    ]
    cursor.executemany("""
    INSERT INTO land_records (id, farmer_id, khasra, khata, total_land, cultivable_land, irrigated_land, rainfed_land, major_crop, irrigation_source, farming_experience, other_info)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, land_records)

    # 6. Unloading Bays
    bays = []
    for c_id in ["CTR-KRN", "CTR-KHN", "CTR-BHP", "CTR-KTA", "CTR-NZB", "CTR-PNP", "CTR-SNP", "CTR-RTK"]:
        for b_num in range(1, 5):
            bays.append((f"BAY-{c_id}-{b_num}", c_id, f"Bay #{b_num}", "AVAILABLE", None))
    cursor.executemany("INSERT INTO unloading_bays (id, center_id, bay_number, status, current_token) VALUES (?, ?, ?, ?, ?)", bays)

    # 7. Procurement Slots (Today + next 6 days)
    today = datetime.now().date()
    slots = []
    for day_offset in range(7):
        s_date = (today + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        for c in centers:
            cid = c[0]
            cap_half = c[6] // 2
            # Morning slot
            slots.append((f"SLT-{cid}-{s_date}-M", cid, s_date, "MORNING", cap_half, 12 if day_offset == 0 else 5, 0))
            # Afternoon slot
            slots.append((f"SLT-{cid}-{s_date}-A", cid, s_date, "AFTERNOON", cap_half, 8 if day_offset == 0 else 3, 0))
    cursor.executemany("INSERT INTO procurement_slots (id, center_id, slot_date, slot_window, capacity, booked_count, is_paused) VALUES (?, ?, ?, ?, ?, ?, ?)", slots)

    # 8. Seed Bookings representing Six-Stage Procurement
    today_str = today.strftime("%Y-%m-%d")
    
    # Booking 1: Stage 1 - BOOKED (Ram Kumar, today morning)
    b1_id = "BK-2026-9874"
    tok1 = "AB-2026-9874"
    cursor.execute("""
    INSERT INTO slot_bookings (
        id, booking_id, farmer_id, center_id, slot_id, crop_id, quantity_quintals,
        vehicle_type, slot_date, slot_window, token_number, qr_code, status, is_redirected
    ) VALUES (
        ?, ?, 'FARMER-01', 'CTR-KRN', 'SLT-CTR-KRN-""" + today_str + """-M', 'CRP-WHT', 45.0,
        'Tractor-Trolley', ?, 'MORNING', ?, 'APNIBAARI:""" + tok1 + """:FARMER-01:CTR-KRN:45.0', 'BOOKED', 0
    )
    """, (str(uuid.uuid4()), b1_id, today_str, tok1))

    # Booking 2: Stage 2 - YARD ARRIVED / GATE CHECK-IN (Gurpreet Singh at Khanna)
    b2_id = "BK-2026-9102"
    tok2 = "AB-2026-9102"
    b2_uuid = str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO slot_bookings (
        id, booking_id, farmer_id, center_id, slot_id, crop_id, quantity_quintals,
        vehicle_type, slot_date, slot_window, token_number, qr_code, status, is_redirected
    ) VALUES (
        ?, ?, 'FARMER-02', 'CTR-KHN', 'SLT-CTR-KHN-""" + today_str + """-M', 'CRP-WHT', 60.0,
        'Mini-Truck', ?, 'MORNING', ?, 'APNIBAARI:""" + tok2 + """:FARMER-02:CTR-KHN:60.0', 'ARRIVED', 0
    )
    """, (b2_uuid, b2_id, today_str, tok2))

    cursor.execute("""
    INSERT INTO gate_checkins (id, booking_id, token_number, center_id, farmer_lat, farmer_lon, distance_km, is_demo_override, checked_in_by)
    VALUES ('GC-01', ?, ?, 'CTR-KHN', 30.7070, 76.2205, 0.05, 0, 'USR-OFFICER-01')
    """, (b2_uuid, tok2))

    # Queue Entry for Booking 2
    cursor.execute("""
    INSERT INTO queue_entries (id, center_id, booking_id, token_number, queue_number, state)
    VALUES ('QE-01', 'CTR-KHN', ?, ?, 1, 'WAITING')
    """, (b2_uuid, tok2))

    # Booking 3: Stage 3 - GROSS WEIGHED (Suresh Verma at Bhopal)
    b3_id = "BK-2026-8840"
    tok3 = "AB-2026-8840"
    b3_uuid = str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO slot_bookings (
        id, booking_id, farmer_id, center_id, slot_id, crop_id, quantity_quintals,
        vehicle_type, slot_date, slot_window, token_number, qr_code, status, is_redirected
    ) VALUES (
        ?, ?, 'FARMER-03', 'CTR-BHP', 'SLT-CTR-BHP-""" + today_str + """-M', 'CRP-GRM', 35.0,
        'Tractor-Trolley', ?, 'MORNING', ?, 'APNIBAARI:""" + tok3 + """:FARMER-03:CTR-BHP:35.0', 'GROSS_WEIGHED', 0
    )
    """, (b3_uuid, b3_id, today_str, tok3))

    cursor.execute("""
    INSERT INTO weighments (id, booking_id, token_number, gross_weight_kg, weighbridge_no, weighed_by)
    VALUES ('WGH-01', ?, ?, 6850.0, 'WB-1', 'USR-OFFICER-02')
    """, (b3_uuid, tok3))

    # Booking 4: Stage 4 - QUALITY CHECKED (Farmer Ram Kumar earlier lot)
    b4_id = "BK-2026-8711"
    tok4 = "AB-2026-8711"
    b4_uuid = str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO slot_bookings (
        id, booking_id, farmer_id, center_id, slot_id, crop_id, quantity_quintals,
        vehicle_type, slot_date, slot_window, token_number, qr_code, status, is_redirected
    ) VALUES (
        ?, ?, 'FARMER-01', 'CTR-KRN', 'SLT-CTR-KRN-""" + today_str + """-M', 'CRP-WHT', 40.0,
        'Tractor-Trolley', ?, 'MORNING', ?, 'APNIBAARI:""" + tok4 + """:FARMER-01:CTR-KRN:40.0', 'QUALITY_CHECKED', 0
    )
    """, (b4_uuid, b4_id, today_str, tok4))

    cursor.execute("""
    INSERT INTO weighments (id, booking_id, token_number, gross_weight_kg, weighbridge_no, weighed_by)
    VALUES ('WGH-02', ?, ?, 7200.0, 'WB-2', 'USR-OFFICER-01')
    """, (b4_uuid, tok4))

    cursor.execute("""
    INSERT INTO quality_inspections (
        id, booking_id, token_number, moisture_pct, foreign_matter_pct, broken_grain_pct,
        grade, decision, deduction_pct, remarks, inspected_by, ai_confidence
    ) VALUES (
        'QI-01', ?, ?, 11.4, 0.4, 1.0, 'Grade A', 'ACCEPTED', 0.0, 'उत्कृष्ट दाना, मानक नमी 11.4%', 'USR-OFFICER-01', 0.96
    )
    """, (b4_uuid, tok4))

    # Booking 5: Stage 5 - UNLOADED (Grain Unloading at Bay)
    b5_id = "BK-2026-8520"
    tok5 = "AB-2026-8520"
    b5_uuid = str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO slot_bookings (
        id, booking_id, farmer_id, center_id, slot_id, crop_id, quantity_quintals,
        vehicle_type, slot_date, slot_window, token_number, qr_code, status, is_redirected
    ) VALUES (
        ?, ?, 'FARMER-02', 'CTR-KRN', 'SLT-CTR-KRN-""" + today_str + """-M', 'CRP-WHT', 50.0,
        'Tractor-Trolley', ?, 'MORNING', ?, 'APNIBAARI:""" + tok5 + """:FARMER-02:CTR-KRN:50.0', 'UNLOADED', 0
    )
    """, (b5_uuid, b5_id, today_str, tok5))

    cursor.execute("""
    INSERT INTO unloading_records (id, booking_id, token_number, bay_id, started_at, completed_at, recorded_by)
    VALUES ('UNL-01', ?, ?, 'BAY-CTR-KRN-1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'USR-OFFICER-01')
    """, (b5_uuid, tok5))

    # Booking 6: Stage 6 - COMPLETED + J-FORM + DBT PAYMENT (Ram Kumar previous harvest)
    b6_id = "BK-2026-8105"
    tok6 = "AB-2026-8105"
    b6_uuid = str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO slot_bookings (
        id, booking_id, farmer_id, center_id, slot_id, crop_id, quantity_quintals,
        vehicle_type, slot_date, slot_window, token_number, qr_code, status, is_redirected
    ) VALUES (
        ?, ?, 'FARMER-01', 'CTR-KRN', 'SLT-CTR-KRN-""" + today_str + """-M', 'CRP-WHT', 52.0,
        'Tractor-Trolley', ?, 'MORNING', ?, 'APNIBAARI:""" + tok6 + """:FARMER-01:CTR-KRN:52.0', 'COMPLETED', 0
    )
    """, (b6_uuid, b6_id, today_str, tok6))

    # Weighment for Stage 6: Gross 8,400 kg, Tare 3,200 kg -> Net 5,200 kg (52.0 Quintals)
    cursor.execute("""
    INSERT INTO weighments (
        id, booking_id, token_number, gross_weight_kg, tare_weight_kg, net_weight_kg, net_weight_quintals,
        weighbridge_no, weighed_by, tare_time, is_finalized
    ) VALUES (
        'WGH-03', ?, ?, 8400.0, 3200.0, 5200.0, 52.0, 'WB-1', 'USR-OFFICER-01', CURRENT_TIMESTAMP, 1
    )
    """, (b6_uuid, tok6))

    # Quality for Stage 6
    cursor.execute("""
    INSERT INTO quality_inspections (
        id, booking_id, token_number, moisture_pct, foreign_matter_pct, broken_grain_pct,
        grade, decision, deduction_pct, remarks, inspected_by, ai_confidence
    ) VALUES (
        'QI-02', ?, ?, 11.2, 0.3, 0.8, 'Grade A', 'ACCEPTED', 0.0, 'मानक अनुरूप - पूर्ण भुगतान स्वीकृत', 'USR-OFFICER-01', 0.98
    )
    """, (b6_uuid, tok6))

    # J-Form for Stage 6: 52 Quintals * 2275 = Rs 1,18,300
    j_form_id = "JF-2026-9921"
    cursor.execute("""
    INSERT INTO j_forms (
        id, j_form_number, booking_id, farmer_id, center_id, crop_name, net_weight_quintals,
        msp_rate, gross_amount, deduction_amount, payable_amount, generated_by
    ) VALUES (
        'JFM-01', ?, ?, 'FARMER-01', 'CTR-KRN', 'Wheat (गेहूं)', 52.0, 2275.0, 118300.0, 0.0, 118300.0, 'USR-OFFICER-01'
    )
    """, (j_form_id, b6_uuid))

    # Payment for Stage 6
    cursor.execute("""
    INSERT INTO payments (
        id, j_form_id, farmer_id, amount, bank_account_masked, ifsc, utr_number, status, initiated_at, settled_at
    ) VALUES (
        'PAY-01', 'JFM-01', 'FARMER-01', 118300.0, 'XXXXXX4820', 'SBIN0001234', 'UTR-SBI-20260906-88741', 'SUCCESS',
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    )
    """)

    # 9. Weather Records
    weather_data = [
        ("WTR-KRN", "CTR-KRN", today_str, 32.5, "Partly Cloudy", 15.0, "कृषि कार्य एवं उपार्जन सामान्य रूप से जारी रखा जा सकता है।"),
        ("WTR-KHN", "CTR-KHN", today_str, 31.0, "Sunny", 10.0, "मौसम अनुकूल है। उपार्जन सामान्य गति से चल रहा है।"),
        ("WTR-BHP", "CTR-BHP", today_str, 29.0, "Scattered Clouds", 25.0, "दोपहर बाद बादलों की संभावना। ढके हुए शेड की व्यवस्था है।"),
        ("WTR-KTA", "CTR-KTA", today_str, 34.0, "Clear Sky", 5.0, "तापमान सामान्य। मंडी संचालन निर्बाध।"),
        ("WTR-NZB", "CTR-NZB", today_str, 28.5, "Moderate Rain", 55.0, "सावधानी: 55% वर्षा की संभावना। शेड में उतराई प्राथमिकता दी जाए।")
    ]
    cursor.executemany("INSERT INTO weather_records (id, center_id, date, temperature, condition, rain_probability, advisory) VALUES (?, ?, ?, ?, ?, ?, ?)", weather_data)

    # 10. Notifications
    notifs = [
        ("NT-01", "USR-FARMER-01", "FARMER", "टोकन आरक्षित", "आपका टोकन AB-2026-9874 करनाल मंडी के लिए आरक्षित हो चुका है।", "SLOT"),
        ("NT-02", "USR-FARMER-01", "FARMER", "डीबीटी भुगतान सफल", "जे-फॉर्म JF-2026-9921 का भुगतान ₹1,18,300 आपके बैंक खाते में जमा हो गया है। UTR: UTR-SBI-20260906-88741", "PAYMENT"),
        ("NT-03", None, "OFFICER", "करनाल मंडी भार चेतावनी", "करनाल हब में वर्तमान क्षमता 88% पार कर चुकी है। स्मार्ट इंजन पानीपत हब में स्लॉट ट्रांसफर की सिफारिश करता है।", "CONGESTION"),
        ("NT-04", None, "OFFICER", "मौसम चेतावनी: निज़ामाबाद", "निज़ामाबाद हब में वर्षा की 55% संभावना दर्ज की गई है। खुले में रखे अनाज को शेड में पहुंचाएं।", "WEATHER")
    ]
    cursor.executemany("INSERT INTO notifications (id, user_id, role, title, message, category) VALUES (?, ?, ?, ?, ?, ?)", notifs)

    # 11. Support Tickets
    tickets = [
        ("TCK-01", "TCK-2026-0811", "राम कुमार", "9876543210", "ramkumar@example.com", "Slot Booking", "मुझे सुबह के बजाय दोपहर के स्लॉट में बदलना है।", "RESOLVED", "USR-OFFICER-01", "किसान को स्लॉट री-शेड्यूल करने में सहायता दी गई।"),
        ("TCK-02", "TCK-2026-0942", "महेश चंद", "9812345678", "mahesh@example.com", "Payment Status", "जे-फॉर्म की रसीद पोर्टल पर कब दिखाई देगी?", "OPEN", None, None)
    ]
    cursor.executemany("""
    INSERT INTO support_tickets (id, ticket_number, name, mobile, email, category, message, status, assigned_to, resolution_notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tickets)

    conn.commit()
    conn.close()
    print("Database seeded with realistic multi-center data.")

if __name__ == "__main__":
    seed()
