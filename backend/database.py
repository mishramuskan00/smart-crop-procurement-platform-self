import sqlite3
import os
import logging

DB_PATH = os.path.join(os.path.dirname(__file__), "apnibaari.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        mobile TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('FARMER', 'OFFICER', 'ADMIN')),
        department TEXT,
        official_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. OTP Sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otp_sessions (
        id TEXT PRIMARY KEY,
        mobile TEXT NOT NULL,
        otp TEXT NOT NULL,
        role TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        verified INTEGER DEFAULT 0,
        attempts INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. User Sessions / Tokens
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 4. Centers / Mandis
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS centers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        district TEXT NOT NULL,
        state TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        daily_capacity INT DEFAULT 300,
        weighbridges INT DEFAULT 2,
        unloading_bays INT DEFAULT 4,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Crops & Seasons & MSP
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS seasons (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        year INT NOT NULL,
        is_active INTEGER DEFAULT 1
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crops (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        hindi_name TEXT NOT NULL,
        season_id TEXT NOT NULL,
        msp_rate REAL NOT NULL,
        max_moisture REAL DEFAULT 12.0,
        max_quota_per_acre REAL DEFAULT 25.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (season_id) REFERENCES seasons(id)
    );
    """)

    # 6. Farmer Profiles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS farmer_profiles (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        farmer_id TEXT UNIQUE,
        application_id TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        guardian_name TEXT,
        dob TEXT,
        gender TEXT,
        category TEXT,
        identity_type TEXT,
        identity_number TEXT,
        address TEXT,
        state TEXT NOT NULL,
        district TEXT NOT NULL,
        tehsil TEXT,
        village TEXT,
        cultivation_type TEXT NOT NULL CHECK(cultivation_type IN ('owner', 'tenant', 'sharecropper', 'joint')),
        bank_account TEXT,
        ifsc_code TEXT,
        verification_status TEXT DEFAULT 'PENDING' CHECK(verification_status IN ('PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'RESUBMISSION_REQUIRED')),
        verification_remarks TEXT,
        verified_by TEXT,
        verified_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    # 7. Land Records
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS land_records (
        id TEXT PRIMARY KEY,
        farmer_id TEXT NOT NULL,
        khasra TEXT,
        khata TEXT,
        total_land REAL DEFAULT 0,
        cultivable_land REAL DEFAULT 0,
        irrigated_land REAL DEFAULT 0,
        rainfed_land REAL DEFAULT 0,
        major_crop TEXT,
        irrigation_source TEXT,
        farming_experience INT DEFAULT 0,
        other_info TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmer_profiles(id) ON DELETE CASCADE
    );
    """)

    # 8. Farmer Documents
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS farmer_documents (
        id TEXT PRIMARY KEY,
        farmer_id TEXT NOT NULL,
        doc_type TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INT DEFAULT 0,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmer_profiles(id) ON DELETE CASCADE
    );
    """)

    # 9. Procurement Slots
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS procurement_slots (
        id TEXT PRIMARY KEY,
        center_id TEXT NOT NULL,
        slot_date TEXT NOT NULL,
        slot_window TEXT NOT NULL CHECK(slot_window IN ('MORNING', 'AFTERNOON')),
        capacity INT NOT NULL,
        booked_count INT DEFAULT 0,
        is_paused INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(center_id, slot_date, slot_window),
        FOREIGN KEY (center_id) REFERENCES centers(id)
    );
    """)

    # 10. Slot Bookings & Tokens
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS slot_bookings (
        id TEXT PRIMARY KEY,
        booking_id TEXT UNIQUE NOT NULL,
        farmer_id TEXT NOT NULL,
        center_id TEXT NOT NULL,
        slot_id TEXT NOT NULL,
        crop_id TEXT NOT NULL,
        quantity_quintals REAL NOT NULL,
        vehicle_type TEXT NOT NULL CHECK(vehicle_type IN ('Tractor-Trolley', 'Mini-Truck', 'Multi-Axle')),
        slot_date TEXT NOT NULL,
        slot_window TEXT NOT NULL,
        token_number TEXT UNIQUE NOT NULL,
        qr_code TEXT NOT NULL,
        status TEXT DEFAULT 'BOOKED' CHECK(status IN (
            'BOOKED',
            'ARRIVED',
            'GATE_ARRIVED',
            'CALLED',
            'GROSS_WEIGHED',
            'QUALITY_CHECKED',
            'UNLOADED',
            'COMPLETED',
            'CANCELLED',
            'REDIRECTED'
        )),
        is_redirected INTEGER DEFAULT 0,
        original_center_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmer_profiles(id),
        FOREIGN KEY (center_id) REFERENCES centers(id),
        FOREIGN KEY (slot_id) REFERENCES procurement_slots(id),
        FOREIGN KEY (crop_id) REFERENCES crops(id)
    );
    """)

    # 11. Token Status History (Audit & Timeline)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS token_status_history (
        id TEXT PRIMARY KEY,
        booking_id TEXT NOT NULL,
        token_number TEXT NOT NULL,
        from_status TEXT,
        to_status TEXT NOT NULL,
        changed_by TEXT,
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (booking_id) REFERENCES slot_bookings(id)
    );
    """)

    # 12. Gate Check-ins & Geo-fencing
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gate_checkins (
        id TEXT PRIMARY KEY,
        booking_id TEXT NOT NULL,
        token_number TEXT NOT NULL,
        center_id TEXT NOT NULL,
        farmer_lat REAL,
        farmer_lon REAL,
        distance_km REAL,
        is_demo_override INTEGER DEFAULT 0,
        checked_in_by TEXT,
        checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (booking_id) REFERENCES slot_bookings(id),
        FOREIGN KEY (center_id) REFERENCES centers(id)
    );
    """)

    # 13. Queue Entries (for live queuing & "NEXT FARMER")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS queue_entries (
        id TEXT PRIMARY KEY,
        center_id TEXT NOT NULL,
        booking_id TEXT NOT NULL,
        token_number TEXT NOT NULL,
        queue_number INT NOT NULL,
        state TEXT DEFAULT 'WAITING' CHECK(state IN ('WAITING', 'CALLED', 'PROCESSING', 'COMPLETED', 'SKIPPED')),
        called_by TEXT,
        called_at TIMESTAMP,
        completed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (center_id) REFERENCES centers(id),
        FOREIGN KEY (booking_id) REFERENCES slot_bookings(id)
    );
    """)

    # 14. Weighment Records
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weighments (
        id TEXT PRIMARY KEY,
        booking_id TEXT UNIQUE NOT NULL,
        token_number TEXT NOT NULL,
        gross_weight_kg REAL NOT NULL,
        tare_weight_kg REAL DEFAULT 0,
        net_weight_kg REAL DEFAULT 0,
        net_weight_quintals REAL DEFAULT 0,
        weighbridge_no TEXT DEFAULT 'WB-1',
        weighed_by TEXT,
        gross_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tare_time TIMESTAMP,
        is_finalized INTEGER DEFAULT 0,
        FOREIGN KEY (booking_id) REFERENCES slot_bookings(id)
    );
    """)

    # 15. Quality Inspections
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quality_inspections (
        id TEXT PRIMARY KEY,
        booking_id TEXT UNIQUE NOT NULL,
        token_number TEXT NOT NULL,
        moisture_pct REAL NOT NULL,
        foreign_matter_pct REAL DEFAULT 0,
        broken_grain_pct REAL DEFAULT 0,
        damaged_grain_pct REAL DEFAULT 0,
        grade TEXT DEFAULT 'Grade A',
        decision TEXT NOT NULL CHECK(decision IN ('ACCEPTED', 'ACCEPTED_WITH_DEDUCTION', 'REJECTED', 'REINSPECTION_REQUESTED')),
        deduction_pct REAL DEFAULT 0,
        remarks TEXT,
        inspected_by TEXT,
        ai_confidence REAL DEFAULT 0.95,
        ai_provider TEXT DEFAULT 'ApniBaari-DemoAI-v1',
        image_path TEXT,
        inspected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (booking_id) REFERENCES slot_bookings(id)
    );
    """)

    # 16. Unloading Bays & Records
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unloading_bays (
        id TEXT PRIMARY KEY,
        center_id TEXT NOT NULL,
        bay_number TEXT NOT NULL,
        status TEXT DEFAULT 'AVAILABLE' CHECK(status IN ('AVAILABLE', 'OCCUPIED', 'MAINTENANCE')),
        current_token TEXT,
        FOREIGN KEY (center_id) REFERENCES centers(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unloading_records (
        id TEXT PRIMARY KEY,
        booking_id TEXT NOT NULL,
        token_number TEXT NOT NULL,
        bay_id TEXT NOT NULL,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        recorded_by TEXT,
        FOREIGN KEY (booking_id) REFERENCES slot_bookings(id),
        FOREIGN KEY (bay_id) REFERENCES unloading_bays(id)
    );
    """)

    # 17. J-Forms (Official MSP Procurement Invoices)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS j_forms (
        id TEXT PRIMARY KEY,
        j_form_number TEXT UNIQUE NOT NULL,
        booking_id TEXT UNIQUE NOT NULL,
        farmer_id TEXT NOT NULL,
        center_id TEXT NOT NULL,
        crop_name TEXT NOT NULL,
        net_weight_quintals REAL NOT NULL,
        msp_rate REAL NOT NULL,
        gross_amount REAL NOT NULL,
        deduction_amount REAL DEFAULT 0,
        payable_amount REAL NOT NULL,
        generated_by TEXT,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (booking_id) REFERENCES slot_bookings(id),
        FOREIGN KEY (farmer_id) REFERENCES farmer_profiles(id),
        FOREIGN KEY (center_id) REFERENCES centers(id)
    );
    """)

    # 18. DBT Payments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id TEXT PRIMARY KEY,
        j_form_id TEXT UNIQUE NOT NULL,
        farmer_id TEXT NOT NULL,
        amount REAL NOT NULL,
        bank_account_masked TEXT,
        ifsc TEXT,
        utr_number TEXT UNIQUE,
        status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'INITIATED', 'PROCESSING', 'SUCCESS', 'FAILED', 'COMPLETED')),
        failure_reason TEXT,
        initiated_at TIMESTAMP,
        settled_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (j_form_id) REFERENCES j_forms(id),
        FOREIGN KEY (farmer_id) REFERENCES farmer_profiles(id)
    );
    """)

    # 19. Slot Redirections & Smart Decision Engine actions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS slot_redirections (
        id TEXT PRIMARY KEY,
        source_center_id TEXT NOT NULL,
        target_center_id TEXT NOT NULL,
        slot_date TEXT NOT NULL,
        shifted_slots_count INT NOT NULL,
        reason TEXT,
        applied_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_center_id) REFERENCES centers(id),
        FOREIGN KEY (target_center_id) REFERENCES centers(id)
    );
    """)

    # 20. Notifications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        role TEXT,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        category TEXT DEFAULT 'SYSTEM',
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 21. Grievance / Support Tickets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS support_tickets (
        id TEXT PRIMARY KEY,
        ticket_number TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        mobile TEXT NOT NULL,
        email TEXT,
        category TEXT DEFAULT 'General Support',
        message TEXT NOT NULL,
        status TEXT DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')),
        assigned_to TEXT,
        resolution_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 22. Weather Records
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather_records (
        id TEXT PRIMARY KEY,
        center_id TEXT NOT NULL,
        date TEXT NOT NULL,
        temperature REAL,
        condition TEXT,
        rain_probability REAL,
        advisory TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (center_id) REFERENCES centers(id)
    );
    """)

    # 23. Audit Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        role TEXT,
        action TEXT NOT NULL,
        entity TEXT NOT NULL,
        entity_id TEXT,
        details TEXT,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print("Database tables initialized successfully.")

if __name__ == "__main__":
    init_db()
