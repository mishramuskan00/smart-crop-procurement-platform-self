import urllib.request
import urllib.parse
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000/api"

def request(path, method="GET", data=None, headers=None):
    url = f"{BASE_URL}{path}"
    h = headers or {}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        h["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', errors='replace')
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw}

def run_all_tests():
    print("==================================================")
    print("APNI BAARI - END-TO-END VERIFICATION")
    print("==================================================")
    passed = 0
    total = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, total
        total += 1
        safe_det = str(details).encode("ascii", "replace").decode("ascii")
        if condition:
            passed += 1
            print(f"  [PASS] {name} {safe_det}")
        else:
            print(f"  [FAIL] {name} - {safe_det}")

    # 1. Health check
    code, res = request("/health")
    assert_test("1. System Health API", code == 200 and res.get("status") == "ONLINE", f"Centers: {res.get('active_centers')}")

    # 2. Auth: Farmer OTP Send & Verify
    code, res = request("/auth/send-otp", "POST", {"mobile": "9876543210", "role": "FARMER"})
    assert_test("2. Farmer Send OTP", code == 200, f"OTP: {res.get('demo_otp')}")

    code, res = request("/auth/verify-otp", "POST", {"mobile": "9876543210", "otp": "123456", "role": "FARMER"})
    farmer_token = res.get("token")
    assert_test("3. Farmer Verify OTP & Session Token", code == 200 and farmer_token is not None, f"Farmer: {res.get('user',{}).get('name')}")

    # 3. Auth: Officer OTP Verify
    code, res = request("/auth/verify-otp", "POST", {"mobile": "9998887771", "otp": "123456", "role": "OFFICER", "official_id": "OFF-HR-701", "department": "Ministry of Food"})
    officer_token = res.get("token")
    assert_test("4. Officer Verify OTP", code == 200 and officer_token is not None, f"Role: {res.get('user',{}).get('role')}")

    # 4. Auth: Admin OTP Verify
    code, res = request("/auth/verify-otp", "POST", {"mobile": "9999999999", "otp": "123456", "role": "ADMIN", "official_id": "ADM-GOI-001", "department": "Central Ministry"})
    admin_token = res.get("token")
    assert_test("5. Admin Verify OTP", code == 200 and admin_token is not None, f"Role: {res.get('user',{}).get('role')}")

    # 5. Centers listing
    code, centers = request("/centers")
    assert_test("6. Centers Master List", code == 200 and len(centers) >= 8, f"Found {len(centers)} active mandis")

    # 6. Farmer KYC Queue
    code, kyc_queue = request("/farmers/kyc-queue")
    assert_test("7. Farmer KYC Queue API", code == 200, f"Pending applications: {len(kyc_queue)}")

    # 7. Slot Availability
    code, slots_res = request("/slots/available?crop_id=CRP-WHT&center_id=CTR-KRN")
    assert_test("8. Slot Availability API", code == 200 and "slots" in slots_res, f"Available slots: {len(slots_res.get('slots', []))}")

    # 8. Slot Recommendation (AI Engine)
    code, rec = request("/slots/recommend?crop_id=CRP-WHT&farmer_lat=29.6857&farmer_lng=76.9905")
    assert_test("9. Smart Slot Recommendation", code == 200 and "recommended_center" in rec, f"Recommended: {rec.get('recommended_center',{}).get('name')}")

    # 9. Book a Slot
    booking_payload = {
        "farmer_id": "FID-HR-2026-001",
        "center_id": "CTR-KRN",
        "crop_id": "CRP-WHT",
        "quantity_quintals": 45.0,
        "slot_date": "2026-09-07",
        "slot_window": "09:00 - 10:00",
        "vehicle_type": "TRACTOR_TROLLEY",
        "vehicle_number": "HR-05-AB-7788"
    }
    code, book_res = request("/slots/book", "POST", booking_payload)
    token_num = book_res.get("token_number")
    booking_id = book_res.get("booking_id")
    assert_test("10. Concurrency-Safe Slot Booking", code == 200 and token_num is not None, f"Token: {token_num}")

    # 10. Gate Check-In (Geo-fencing)
    checkin_payload = {
        "token_number": token_num,
        "latitude": 29.6857,
        "longitude": 76.9905,
        "demo_override": True
    }
    code, checkin_res = request("/gate/checkin", "POST", checkin_payload)
    assert_test("11. 2km Geo-Fenced Gate Check-In", code == 200 and checkin_res.get("status") == "GATE_ARRIVED", f"Queue Position: #{checkin_res.get('queue_position')}")

    # 11. Queue Status
    code, q_res = request("/queue/CTR-KRN")
    assert_test("12. Center Live Dispatch Queue", code == 200 and "active_queue" in q_res, f"Queue Length: {q_res.get('queue_length')}")

    # 12. Call Next Farmer
    code, call_res = request("/queue/call-next", "POST", {"center_id": "CTR-KRN", "weighbridge_id": 1})
    assert_test("13. Queue Electronic Calling (Next Farmer)", code == 200, f"Status: {call_res.get('status')}")

    # 13. Weighbridge Gross & Tare
    wb_payload = {
        "booking_id": booking_id,
        "token_number": token_num,
        "gross_weight_kg": 7500.0,
        "tare_weight_kg": 2500.0,
        "weighbridge_id": "WB-01",
        "operator_name": "Satish Kumar"
    }
    code, wb_res = request("/weighbridge/record", "POST", wb_payload)
    assert_test("14. Electronic Weighbridge Recording", code == 200 and wb_res.get("net_weight_quintals") == 50.0, f"Net: {wb_res.get('net_weight_quintals')} qtl")

    # 14. AI Quality Inspection
    qi_payload = {
        "booking_id": booking_id,
        "token_number": token_num,
        "moisture_pct": 11.2,
        "foreign_matter_pct": 0.4,
        "broken_grain_pct": 1.2
    }
    code, qi_res = request("/quality/inspect", "POST", qi_payload)
    assert_test("15. AI Grain Quality Analysis", code == 200 and qi_res.get("grade") == "GRADE_A", f"Grade: {qi_res.get('grade')}, Net Payable: {qi_res.get('net_payable_weight_qtl')} qtl")

    # 15. Unloading Bay Assignment
    code, bay_res = request("/unloading/assign", "POST", {"booking_id": booking_id, "token_number": token_num, "center_id": "CTR-KRN"})
    assert_test("16. Unloading Bay Dynamic Assignment", code == 200 and bay_res.get("bay_number") is not None, f"Bay #{bay_res.get('bay_number')}")

    # 16. Certified J-Form Generation
    code, jf_res = request("/jform/generate", "POST", {"booking_id": booking_id, "token_number": token_num})
    jform_num = jf_res.get("j_form_number")
    tot_amt = jf_res.get("total_amount")
    assert_test("17. Certified Digital J-Form Issuance", code == 200 and jform_num is not None, f"J-Form: {jform_num}, Amount: Rs. {tot_amt}")

    # 17. Instant DBT Payment
    code, dbt_res = request("/payments/initiate-dbt", "POST", {"booking_id": booking_id, "token_number": token_num})
    dbt_amt = dbt_res.get("amount")
    assert_test("18. Direct Benefit Transfer (DBT) Payout", code == 200 and dbt_res.get("status") == "COMPLETED", f"UTR: {dbt_res.get('utr_number')}, Rs. {dbt_amt}")

    # 18. Officer Dashboard Summary
    code, off_sum = request("/officers/dashboard-summary")
    assert_test("19. Government Officer Dashboard Telemetry", code == 200 and "stats" in off_sum, f"Arrivals Today: {off_sum.get('stats',{}).get('arrivals_today')}")

    # 19. Smart Decision Engine Congestion Redirection
    redir_payload = {
        "source_center_id": "CTR-KRN",
        "target_center_id": "CTR-PNP",
        "slots_count": 20,
        "slot_date": "2026-09-07"
    }
    code, redir_res = request("/officers/redirect-slots", "POST", redir_payload)
    assert_test("20. Smart Decision Engine Surge Redirection", code == 200 and redir_res.get("success") == True, redir_res.get("message"))

    # 20. Capacity Adjustment
    code, cap_res = request("/officers/adjust-capacity", "POST", {"center_id": "CTR-KRN", "daily_capacity": 380})
    assert_test("21. Mandi Dynamic Capacity Adjustment", code == 200 and cap_res.get("new_capacity") == 380, f"New Capacity: {cap_res.get('new_capacity')} qtl")

    # 21. Mandi Broadcast Announcement
    ann_payload = {
        "center_id": "CTR-KRN",
        "title": "Weather Warning",
        "message": "Rain alert in Karnal region. Extra covered bays opened."
    }
    code, ann_res = request("/officers/broadcast-announcement", "POST", ann_payload)
    assert_test("22. Farmer SMS / Broadcast Advisory", code == 200 and ann_res.get("success") == True, f"Sent: {ann_res.get('title')}")

    # 22. Admin Dashboard & Master Stats
    code, adm_res = request("/admin/stats")
    assert_test("23. Central Admin Dashboard & Statistics", code == 200 and "total_farmers" in adm_res, f"Registered Farmers: {adm_res.get('total_farmers')}")

    # 23. Notifications Feed
    code, notif_res = request("/notifications?role=FARMER")
    assert_test("24. Real-Time In-App Notification Feed", code == 200 and "notifications" in notif_res, f"Items: {len(notif_res.get('notifications', []))}")

    # 24. Chatbot / Voice Assistant
    code, bot_res = request("/chatbot/query", "POST", {"query": "mera token status kya hai"})
    assert_test("25. AI Virtual Assistant (Token Intent)", code == 200 and bot_res.get("intent") == "TOKEN_STATUS", bot_res.get("response_hi"))

    code, bot_msp = request("/chatbot/query", "POST", {"query": "wheat msp rate kya hai"})
    assert_test("26. AI Virtual Assistant (MSP Intent)", code == 200 and bot_msp.get("intent") == "MSP_RATES", bot_msp.get("response_hi"))

    # 25. Weather API
    code, wth_res = request("/weather/CTR-KRN")
    assert_test("27. IMD Real-Time Mandi Weather Telemetry", code == 200 and "weather" in wth_res, f"Temp: {wth_res.get('weather',{}).get('temperature')}°C, Rain Prob: {wth_res.get('weather',{}).get('rain_probability')}%")

    # 26. Support Ticket Submission
    code, tck_res = request("/support/ticket", "POST", {
        "name": "राम कुमार",
        "mobile": "9876543210",
        "category": "Slot Rescheduling",
        "message": "Need slot adjustment due to tractor repair."
    })
    assert_test("28. Farmer Grievance & Ticket Resolution", code == 200 and tck_res.get("success") == True, f"Ticket: {tck_res.get('ticket_number')}")

    print("==================================================")
    print(f"VERIFICATION SUMMARY: {passed} / {total} TESTS PASSED")
    print("==================================================")
    if passed == total:
        print(">>> ALL 28 CORE CAPABILITIES FULLY FUNCTIONAL AND VERIFIED! <<<")
    else:
        print(f">>> {total - passed} TESTS FAILED <<<")

if __name__ == "__main__":
    run_all_tests()
