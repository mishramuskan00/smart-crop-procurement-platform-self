import math
import uuid
import random
from datetime import datetime, timedelta
from database import get_db

# 1. Geo-fence Haversine Distance Calculation (in kilometers)
def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0 # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 3)

# 2. Dynamic Estimated Waiting Time (EWT) Calculation
def calculate_dynamic_ewt(center_id: str, vehicle_type: str = "Tractor-Trolley") -> dict:
    conn = get_db()
    cursor = conn.cursor()
    
    # Get active weighbridges and unloading bays
    cursor.execute("SELECT weighbridges, unloading_bays FROM centers WHERE id = ?", (center_id,))
    center_row = cursor.fetchone()
    weighbridges = center_row["weighbridges"] if center_row else 2
    unloading_bays = center_row["unloading_bays"] if center_row else 4
    
    # Count waiting queue entries
    cursor.execute("""
    SELECT COUNT(*) as waiting_count 
    FROM queue_entries 
    WHERE center_id = ? AND state = 'WAITING'
    """, (center_id,))
    queue_row = cursor.fetchone()
    waiting_count = queue_row["waiting_count"] if queue_row else 0
    
    # Baseline processing time in minutes
    baseline_vehicle_times = {
        "Tractor-Trolley": 18,
        "Mini-Truck": 25,
        "Multi-Axle": 40
    }
    base_time = baseline_vehicle_times.get(vehicle_type, 20)
    
    # Effective service parallel channels
    effective_channels = max(1, min(weighbridges, unloading_bays))
    
    # Weather multiplier
    cursor.execute("SELECT rain_probability FROM weather_records WHERE center_id = ?", (center_id,))
    w_row = cursor.fetchone()
    rain_prob = w_row["rain_probability"] if w_row else 10.0
    weather_multiplier = 1.3 if rain_prob > 40.0 else 1.0

    # Calculate minutes
    if waiting_count == 0:
        ewt_minutes = int(base_time * weather_multiplier)
    else:
        ewt_minutes = int(((waiting_count * base_time) / effective_channels) * weather_multiplier)
    
    # Congestion Level
    if ewt_minutes < 30:
        congestion_color = "green"
        congestion_label = "सामान्य (Normal)"
    elif ewt_minutes <= 60:
        congestion_color = "yellow"
        congestion_label = "मध्यम भार (Moderate Load)"
    else:
        congestion_color = "red"
        congestion_label = "अत्यधिक भीड़ (Overloaded)"

    conn.close()
    
    hours = ewt_minutes // 60
    mins = ewt_minutes % 60
    formatted_ewt = f"{hours}h {mins}m" if hours > 0 else f"{mins} min"
    
    return {
        "waiting_count": waiting_count,
        "ewt_minutes": ewt_minutes,
        "formatted_ewt": formatted_ewt,
        "congestion_color": congestion_color,
        "congestion_label": congestion_label,
        "rain_prob": rain_prob,
        "active_weighbridges": weighbridges,
        "active_bays": unloading_bays
    }

# 3. Concurrency-Safe Slot Booking & Quota Check
def book_procurement_slot(farmer_id: str, center_id: str, crop_id: str, quantity_quintals: float, vehicle_type: str, slot_date: str, slot_window: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN IMMEDIATE") # Lock for concurrency safety

        # 1. Check Farmer KYC approval
        cursor.execute("SELECT farmer_profiles.user_id, farmer_profiles.verification_status, farmer_profiles.farmer_id, farmer_profiles.full_name, users.mobile FROM farmer_profiles JOIN users ON farmer_profiles.user_id = users.id WHERE farmer_profiles.id = ?", (farmer_id,))
        farmer = cursor.fetchone()
        if not farmer or farmer["verification_status"] != "APPROVED":
            conn.rollback()
            conn.close()
            return {"success": False, "message": "किसान पंजीकरण अभी सत्यापित नहीं हुआ है। केवल स्वीकृत किसान ही स्लॉट आरक्षित कर सकते हैं।"}

        # 2. Check Land & Quota
        cursor.execute("SELECT cultivable_land FROM land_records WHERE farmer_id = ?", (farmer_id,))
        land = cursor.fetchone()
        cultivable_acres = (land["cultivable_land"] * 2.471) if land and land["cultivable_land"] else 2.5 # Ha to acres approx
        
        cursor.execute("SELECT max_quota_per_acre, name FROM crops WHERE id = ?", (crop_id,))
        crop = cursor.fetchone()
        max_allowed_quota = cultivable_acres * (crop["max_quota_per_acre"] if crop else 25.0)

        # Check total booked quantity for this season
        cursor.execute("""
        SELECT COALESCE(SUM(quantity_quintals), 0) as total_booked 
        FROM slot_bookings 
        WHERE farmer_id = ? AND crop_id = ? AND status != 'CANCELLED'
        """, (farmer_id, crop_id))
        already_booked = cursor.fetchone()["total_booked"]

        if (already_booked + quantity_quintals) > (max_allowed_quota + 5.0): # slight buffer
            conn.rollback()
            conn.close()
            return {
                "success": False, 
                "message": f"उपार्जन कोटा सीमा समाप्त। आपके सत्यापित रकबे के अनुसार अधिकतम अनुमेय मात्रा {round(max_allowed_quota, 1)} क्विंटल है (वर्तमान में आरक्षित: {round(already_booked, 1)} क्विंटल)।"
            }

        # 3. Check for Duplicate Booking on the same date
        cursor.execute("""
        SELECT id FROM slot_bookings 
        WHERE farmer_id = ? AND slot_date = ? AND status NOT IN ('CANCELLED', 'COMPLETED')
        """, (farmer_id, slot_date))
        if cursor.fetchone():
            conn.rollback()
            conn.close()
            return {"success": False, "message": "इस तिथि के लिए आपका एक स्लॉट पहले से सक्रिय है।"}

        # 4. Check Center Slot Capacity
        db_slot_window = "AFTERNOON" if any(x in str(slot_window).upper() for x in ["13", "14", "15", "16", "17", "18", "PM", "AFTERNOON"]) else "MORNING"
        cursor.execute("""
        SELECT id, capacity, booked_count, is_paused 
        FROM procurement_slots 
        WHERE center_id = ? AND slot_date = ? AND slot_window = ?
        """, (center_id, slot_date, db_slot_window))
        slot = cursor.fetchone()

        if not slot:
            # Create slot on the fly if within allowed dates
            slot_uuid = str(uuid.uuid4())
            cursor.execute("SELECT daily_capacity FROM centers WHERE id = ?", (center_id,))
            c_cap = cursor.fetchone()["daily_capacity"] // 2
            cursor.execute("""
            INSERT INTO procurement_slots (id, center_id, slot_date, slot_window, capacity, booked_count, is_paused)
            VALUES (?, ?, ?, ?, ?, 0, 0)
            """, (slot_uuid, center_id, slot_date, db_slot_window, c_cap))
            slot_id = slot_uuid
            slot_capacity = c_cap
            booked_count = 0
        else:
            if slot["is_paused"]:
                conn.rollback()
                conn.close()
                return {"success": False, "message": "प्रतिकूल मौसम या तकनीकी कारणों से यह स्लॉट अस्थायी रूप से रोक दिया गया है।"}
            if slot["booked_count"] >= slot["capacity"]:
                conn.rollback()
                conn.close()
                return {"success": False, "message": "चयनित स्लॉट की क्षमता पूर्ण हो चुकी है। कृपया दूसरा समय या नजदीकी केंद्र चुनें।"}
            slot_id = slot["id"]
            slot_capacity = slot["capacity"]
            booked_count = slot["booked_count"]

        # 5. Reserve Slot
        cursor.execute("UPDATE procurement_slots SET booked_count = booked_count + 1 WHERE id = ?", (slot_id,))

        # 6. Generate Unique Token
        cursor.execute("SELECT district FROM centers WHERE id = ?", (center_id,))
        dist_code = cursor.fetchone()["district"][:3].upper()
        token_num = f"{dist_code}-2026-{random.randint(1000, 9999)}"
        booking_id = f"BK-2026-{random.randint(1000, 9999)}"
        booking_uuid = str(uuid.uuid4())

        qr_payload = f"APNIBAARI:{token_num}:{farmer['farmer_id']}:{center_id}:{quantity_quintals}:{slot_date}:{slot_window}"

        # Normalize vehicle type
        v_str = str(vehicle_type).upper().replace("-", "_").replace(" ", "_")
        if "TRUCK" in v_str or "MINI" in v_str:
            norm_vehicle = "Mini-Truck"
        elif "AXLE" in v_str or "MULTI" in v_str or "HEAVY" in v_str:
            norm_vehicle = "Multi-Axle"
        else:
            norm_vehicle = "Tractor-Trolley"

        cursor.execute("""
        INSERT INTO slot_bookings (
            id, booking_id, farmer_id, center_id, slot_id, crop_id, quantity_quintals,
            vehicle_type, slot_date, slot_window, token_number, qr_code, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'BOOKED')
        """, (
            booking_uuid, booking_id, farmer_id, center_id, slot_id, crop_id,
            quantity_quintals, norm_vehicle, slot_date, db_slot_window, token_num, qr_payload
        ))

        # Record Status Audit
        cursor.execute("""
        INSERT INTO token_status_history (id, booking_id, token_number, to_status, remarks)
        VALUES (?, ?, ?, 'BOOKED', 'स्लॉट सफलतापूर्वक आरक्षित')
        """, (str(uuid.uuid4()), booking_uuid, token_num))

        # Create Notification
        cursor.execute("""
        INSERT INTO notifications (id, user_id, role, title, message, category)
        VALUES (?, ?, 'FARMER', 'स्लॉट आरक्षण सफल', ?, 'SLOT')
        """, (
            str(uuid.uuid4()), farmer["user_id"] if "user_id" in farmer.keys() else None,
            f"टोकन {token_num} जारी हुआ। तिथि: {slot_date} ({slot_window})"
        ))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "booking_id": booking_id,
            "token_number": token_num,
            "qr_code": qr_payload,
            "slot_date": slot_date,
            "slot_window": slot_window,
            "quantity_quintals": quantity_quintals,
            "message": "आपकी बारी (स्लॉट) सफलतापूर्वक आरक्षित हो गई है!"
        }
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "message": f"बुकिंग त्रुटि: {str(e)}"}

# 4. Smart Slot Recommendation Engine
def get_smart_slot_recommendation(farmer_id: str, preferred_center_id: str, crop_id: str, quantity: float, vehicle_type: str = "Tractor-Trolley") -> dict:
    conn = get_db()
    cursor = conn.cursor()
    
    # Check all centers
    cursor.execute("SELECT id, name, district, latitude, longitude, daily_capacity FROM centers WHERE is_active = 1")
    centers = cursor.fetchall()
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    recommendations = []
    
    for c in centers:
        cid = c["id"]
        ewt_info = calculate_dynamic_ewt(cid, vehicle_type)
        
        # Check slot availability
        cursor.execute("""
        SELECT slot_window, capacity, booked_count 
        FROM procurement_slots 
        WHERE center_id = ? AND slot_date = ? AND is_paused = 0
        """, (cid, today_str))
        slots = cursor.fetchall()
        
        available_today = sum([max(0, s["capacity"] - s["booked_count"]) for s in slots]) if slots else c["daily_capacity"] // 2
        
        # Weather check
        cursor.execute("SELECT rain_probability, condition FROM weather_records WHERE center_id = ?", (cid,))
        w = cursor.fetchone()
        rain = w["rain_probability"] if w else 10.0
        
        # Scoring: lower EWT, lower rain, higher availability = better score
        score = 100 - (ewt_info["ewt_minutes"] * 0.5) - (rain * 0.4) + (available_today * 0.2)
        if cid == preferred_center_id:
            score += 15 # Preferred center boost

        reason_parts = []
        if ewt_info["ewt_minutes"] < 30:
            reason_parts.append("कम प्रतीक्षा समय (त्वरित सेवा)")
        if rain < 20:
            reason_parts.append("अनुकूल साफ मौसम")
        if available_today > 30:
            reason_parts.append("पर्याप्त स्लॉट उपलब्ध")

        recommendations.append({
            "center_id": cid,
            "center_name": c["name"],
            "district": c["district"],
            "date": today_str if available_today > 5 else tomorrow_str,
            "recommended_window": "MORNING" if available_today > 15 else "AFTERNOON",
            "ewt": ewt_info["formatted_ewt"],
            "congestion": ewt_info["congestion_label"],
            "congestion_color": ewt_info["congestion_color"],
            "available_slots": available_today,
            "rain_prob": rain,
            "score": score,
            "reason": " • ".join(reason_parts) if reason_parts else "संतुलित क्षमता एवं सुरक्षित उपार्जन"
        })

    conn.close()
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    return {
        "best_recommendation": recommendations[0] if recommendations else None,
        "all_recommendations": recommendations[:3]
    }

# 5. Officer Concurrency-Safe Next Farmer Calling
def call_next_farmer(center_id: str, officer_id: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        
        # Find next waiting farmer in queue
        cursor.execute("""
        SELECT q.id, q.booking_id, q.token_number, q.queue_number, b.vehicle_type, f.full_name, c.name as crop_name
        FROM queue_entries q
        JOIN slot_bookings b ON q.booking_id = b.id
        JOIN farmer_profiles f ON b.farmer_id = f.id
        JOIN crops c ON b.crop_id = c.id
        WHERE q.center_id = ? AND q.state = 'WAITING'
        ORDER BY q.queue_number ASC
        LIMIT 1
        """, (center_id,))
        
        entry = cursor.fetchone()
        if not entry:
            conn.rollback()
            conn.close()
            return {"success": False, "message": "कतार में कोई प्रतीक्षा रत किसान नहीं है।"}
            
        entry_id = entry["id"]
        token_number = entry["token_number"]
        booking_id = entry["booking_id"]
        
        # Mark as CALLED
        cursor.execute("""
        UPDATE queue_entries 
        SET state = 'CALLED', called_by = ?, called_at = CURRENT_TIMESTAMP 
        WHERE id = ?
        """, (officer_id, entry_id))
        
        # Update token history
        cursor.execute("""
        INSERT INTO token_status_history (id, booking_id, token_number, to_status, remarks)
        VALUES (?, ?, ?, 'CALLED', 'अधिकारी द्वारा तौल / परीक्षण हेतु बुलाया गया')
        """, (str(uuid.uuid4()), booking_id, token_number))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "token_number": token_number,
            "queue_number": entry["queue_number"],
            "farmer_name": entry["full_name"],
            "crop_name": entry["crop_name"],
            "vehicle_type": entry["vehicle_type"],
            "message": f"टोकन {token_number} ({entry['full_name']}) को सेवा हेतु बुलाया गया।"
        }
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "message": f"कतार त्रुटि: {str(e)}"}

# 6. Electronic Weighbridge Recording (Gross / Tare / Net)
def record_weighment(booking_id: str, gross_weight_kg: float, tare_weight_kg: float, weighbridge_no: str, weighed_by: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        
        if gross_weight_kg <= 0:
            conn.rollback()
            conn.close()
            return {"success": False, "message": "सकल तौल (Gross Weight) शून्य से अधिक होना अनिवार्य है।"}
            
        if tare_weight_kg > 0 and tare_weight_kg >= gross_weight_kg:
            conn.rollback()
            conn.close()
            return {"success": False, "message": "खाली वाहन का तौल (Tare Weight) सकल तौल से कम होना चाहिए।"}

        cursor.execute("SELECT token_number, status, crop_id, farmer_id, center_id FROM slot_bookings WHERE id = ?", (booking_id,))
        booking = cursor.fetchone()
        if not booking:
            conn.rollback()
            conn.close()
            return {"success": False, "message": "बुकिंग रिकॉर्ड नहीं मिला।"}

        token_number = booking["token_number"]
        net_kg = max(0.0, gross_weight_kg - tare_weight_kg)
        net_quintals = round(net_kg / 100.0, 2)
        is_finalized = 1 if tare_weight_kg > 0 else 0

        # Upsert weighment
        cursor.execute("SELECT id FROM weighments WHERE booking_id = ?", (booking_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
            UPDATE weighments 
            SET gross_weight_kg = ?, tare_weight_kg = ?, net_weight_kg = ?, net_weight_quintals = ?,
                weighbridge_no = ?, weighed_by = ?, tare_time = CURRENT_TIMESTAMP, is_finalized = ?
            WHERE booking_id = ?
            """, (gross_weight_kg, tare_weight_kg, net_kg, net_quintals, weighbridge_no, weighed_by, is_finalized, booking_id))
        else:
            cursor.execute("""
            INSERT INTO weighments (
                id, booking_id, token_number, gross_weight_kg, tare_weight_kg, net_weight_kg,
                net_weight_quintals, weighbridge_no, weighed_by, is_finalized
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), booking_id, token_number, gross_weight_kg, tare_weight_kg, net_kg, net_quintals, weighbridge_no, weighed_by, is_finalized))

        # Update booking status
        new_status = "COMPLETED" if is_finalized else "GROSS_WEIGHED"
        cursor.execute("UPDATE slot_bookings SET status = ? WHERE id = ?", (new_status, booking_id))

        cursor.execute("""
        INSERT INTO token_status_history (id, booking_id, token_number, to_status, remarks)
        VALUES (?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), booking_id, token_number, new_status, f"तौल दर्ज: सकल {gross_weight_kg} kg, खाली {tare_weight_kg} kg, शुद्ध {net_quintals} क्विंटल"))

        # If finalized, generate J-Form and initiate Payment automatically!
        j_form_data = None
        if is_finalized:
            cursor.execute("SELECT msp_rate, name FROM crops WHERE id = ?", (booking["crop_id"],))
            crop = cursor.fetchone()
            msp = crop["msp_rate"]
            
            # Check for any quality deduction
            cursor.execute("SELECT deduction_pct FROM quality_inspections WHERE booking_id = ?", (booking_id,))
            q_row = cursor.fetchone()
            deduction_pct = q_row["deduction_pct"] if q_row else 0.0

            gross_amount = round(net_quintals * msp, 2)
            deduction_amount = round((gross_amount * deduction_pct) / 100.0, 2)
            payable_amount = round(gross_amount - deduction_amount, 2)
            
            j_form_num = f"JF-2026-{random.randint(10000, 99999)}"
            j_form_uuid = str(uuid.uuid4())

            cursor.execute("""
            INSERT INTO j_forms (
                id, j_form_number, booking_id, farmer_id, center_id, crop_name,
                net_weight_quintals, msp_rate, gross_amount, deduction_amount, payable_amount, generated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (j_form_uuid, j_form_num, booking_id, booking["farmer_id"], booking["center_id"], crop["name"], net_quintals, msp, gross_amount, deduction_amount, payable_amount, weighed_by))

            # Initiate Payment
            cursor.execute("SELECT bank_account, ifsc_code FROM farmer_profiles WHERE id = ?", (booking["farmer_id"],))
            bank = cursor.fetchone()
            utr_simulated = f"UTR-SBI-20260906-{random.randint(10000, 99999)}"

            cursor.execute("""
            INSERT INTO payments (
                id, j_form_id, farmer_id, amount, bank_account_masked, ifsc, utr_number, status, initiated_at, settled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'SUCCESS', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (str(uuid.uuid4()), j_form_uuid, booking["farmer_id"], payable_amount, bank["bank_account"] if bank else "XXXXXX0000", bank["ifsc_code"] if bank else "SBIN0001000", utr_simulated))

            # Complete queue entry
            cursor.execute("UPDATE queue_entries SET state = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE booking_id = ?", (booking_id,))

            j_form_data = {
                "j_form_number": j_form_num,
                "net_quintals": net_quintals,
                "msp_rate": msp,
                "payable_amount": payable_amount,
                "utr_number": utr_simulated
            }

        conn.commit()
        conn.close()

        return {
            "success": True,
            "net_weight_kg": net_kg,
            "net_weight_quintals": net_quintals,
            "is_finalized": bool(is_finalized),
            "j_form": j_form_data,
            "message": "तौल विवरण सफलतापूर्वक दर्ज किया गया।" + (" जे-फॉर्म एवं डीबीटी भुगतान प्रक्रिया पूरी हुई।" if is_finalized else "")
        }
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "message": f"तौल दर्ज करने में त्रुटि: {str(e)}"}

# 7. AI Grain Quality Inspection Provider (Demo + Spec-Ready)
def inspect_grain_quality(booking_id: str, moisture_pct: float, foreign_matter_pct: float, broken_grain_pct: float, remarks: str, inspected_by: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        
        cursor.execute("SELECT token_number, crop_id FROM slot_bookings WHERE id = ?", (booking_id,))
        b = cursor.fetchone()
        if not b:
            conn.rollback()
            conn.close()
            return {"success": False, "message": "बुकिंग नहीं मिली।"}

        cursor.execute("SELECT max_moisture FROM crops WHERE id = ?", (b["crop_id"],))
        crop = cursor.fetchone()
        max_moisture = crop["max_moisture"] if crop else 12.0

        # Quality rule evaluation
        deduction_pct = 0.0
        if moisture_pct > (max_moisture + 2.0):
            decision = "REJECTED"
            grade = "Sub-Standard (अमान्य)"
            remarks = f"नमी {moisture_pct}% अनुमेय सीमा {max_moisture}% से अत्यधिक है।"
        elif moisture_pct > max_moisture:
            decision = "ACCEPTED_WITH_DEDUCTION"
            deduction_pct = round((moisture_pct - max_moisture) * 1.0, 2)
            grade = "Grade B"
            remarks = f"मानक नमी {max_moisture}% से अधिक होने के कारण {deduction_pct}% कटौती लागू।"
        else:
            decision = "ACCEPTED"
            grade = "Grade A (FAQ Grade)"
            deduction_pct = 0.0
            if not remarks:
                remarks = "गुणवत्ता मानक के अनुरूप - एफएक्यू ग्रेड स्वीकृत।"

        qi_id = str(uuid.uuid4())
        cursor.execute("""
        INSERT OR REPLACE INTO quality_inspections (
            id, booking_id, token_number, moisture_pct, foreign_matter_pct, broken_grain_pct,
            grade, decision, deduction_pct, remarks, inspected_by, ai_confidence, ai_provider
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.96, 'ApniBaari-DemoAI-v1')
        """, (qi_id, booking_id, b["token_number"], moisture_pct, foreign_matter_pct, broken_grain_pct, grade, decision, deduction_pct, remarks, inspected_by))

        cursor.execute("UPDATE slot_bookings SET status = 'QUALITY_CHECKED' WHERE id = ?", (booking_id,))

        cursor.execute("""
        INSERT INTO token_status_history (id, booking_id, token_number, to_status, remarks)
        VALUES (?, ?, ?, 'QUALITY_CHECKED', ?)
        """, (str(uuid.uuid4()), booking_id, b["token_number"], f"गुणवत्ता जांच: {decision} ({grade}), नमी: {moisture_pct}%"))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "decision": decision,
            "grade": grade,
            "deduction_pct": deduction_pct,
            "moisture_pct": moisture_pct,
            "remarks": remarks,
            "ai_confidence": 96.4,
            "message": f"गुणवत्ता विश्लेषण पूर्ण: {grade} ({decision})"
        }
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "message": f"गुणवत्ता विश्लेषण त्रुटि: {str(e)}"}

# 8. Unloading Bay Operations
def assign_unloading_bay(booking_id: str, center_id: str, recorded_by: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        
        cursor.execute("SELECT id, bay_number FROM unloading_bays WHERE center_id = ? AND status = 'AVAILABLE' LIMIT 1", (center_id,))
        bay = cursor.fetchone()
        if not bay:
            conn.rollback()
            conn.close()
            return {"success": False, "message": "वर्तमान में कोई उतराई शेड (Unloading Bay) खाली नहीं है। कृपया थोड़ी देर प्रतीक्षा करें।"}

        bay_id = bay["id"]
        cursor.execute("SELECT token_number FROM slot_bookings WHERE id = ?", (booking_id,))
        token = cursor.fetchone()["token_number"]

        cursor.execute("UPDATE unloading_bays SET status = 'OCCUPIED', current_token = ? WHERE id = ?", (token, bay_id))
        cursor.execute("""
        INSERT INTO unloading_records (id, booking_id, token_number, bay_id, started_at, recorded_by)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (str(uuid.uuid4()), booking_id, token, bay_id, recorded_by))

        cursor.execute("UPDATE slot_bookings SET status = 'UNLOADED' WHERE id = ?", (booking_id,))

        cursor.execute("""
        INSERT INTO token_status_history (id, booking_id, token_number, to_status, remarks)
        VALUES (?, ?, ?, 'UNLOADED', ?)
        """, (str(uuid.uuid4()), booking_id, token, f"शेड {bay['bay_number']} में अनाज उतराई प्रारंभ"))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "bay_number": bay["bay_number"],
            "message": f"वाहन को {bay['bay_number']} में उतराई हेतु आवंटित किया गया।"
        }
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "message": f"शेड आवंटन त्रुटि: {str(e)}"}

# 9. Smart Decision Engine: Congestion Redirection
def apply_slot_redirection(source_center_id: str, target_center_id: str, slots_count: int, slot_date: str, applied_by: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        
        # Select upcoming booked slots from source center on date
        cursor.execute("""
        SELECT id, farmer_id, token_number 
        FROM slot_bookings 
        WHERE center_id = ? AND slot_date = ? AND status = 'BOOKED' 
        LIMIT ?
        """, (source_center_id, slot_date, slots_count))
        bookings_to_shift = cursor.fetchall()
        
        if not bookings_to_shift:
            conn.rollback()
            conn.close()
            return {"success": False, "message": "स्थानांतरित करने के लिए कोई आगामी आरक्षित स्लॉट नहीं मिला।"}

        actual_shifted = len(bookings_to_shift)
        
        cursor.execute("SELECT name FROM centers WHERE id = ?", (source_center_id,))
        source_name = cursor.fetchone()["name"]
        cursor.execute("SELECT name FROM centers WHERE id = ?", (target_center_id,))
        target_name = cursor.fetchone()["name"]

        for b in bookings_to_shift:
            b_id = b["id"]
            cursor.execute("""
            UPDATE slot_bookings 
            SET center_id = ?, is_redirected = 1, original_center_id = ? 
            WHERE id = ?
            """, (target_center_id, source_center_id, b_id))

            cursor.execute("""
            INSERT INTO token_status_history (id, booking_id, token_number, to_status, remarks)
            VALUES (?, ?, ?, 'REDIRECTED', ?)
            """, (str(uuid.uuid4()), b_id, b["token_number"], f"भीड़ प्रबंधन: स्लॉट {source_name} से {target_name} स्थानांतरित किया गया।"))

            cursor.execute("""
            INSERT INTO notifications (id, user_id, role, title, message, category)
            VALUES (?, ?, 'FARMER', 'स्लॉट केंद्र पुनर्निर्देशन', ?, 'REDIRECT')
            """, (
                str(uuid.uuid4()), None,
                f"आपका टोकन {b['token_number']} भीड़भाड़ से बचाव हेतु {target_name} स्थानांतरित किया गया है।"
            ))

        # Log redirection record
        cursor.execute("""
        INSERT INTO slot_redirections (id, source_center_id, target_center_id, slot_date, shifted_slots_count, reason, applied_by)
        VALUES (?, ?, ?, ?, ?, 'भीड़ प्रबंधन एवं तीव्र उपार्जन', ?)
        """, (str(uuid.uuid4()), source_center_id, target_center_id, slot_date, actual_shifted, applied_by))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "shifted_count": actual_shifted,
            "source_name": source_name,
            "target_name": target_name,
            "message": f"सफलतापूर्वक {actual_shifted} स्लॉट {source_name} से {target_name} स्थानांतरित किए गए। किसानों को सूचना भेज दी गई है।"
        }
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "message": f"रीडायरेक्शन त्रुटि: {str(e)}"}
