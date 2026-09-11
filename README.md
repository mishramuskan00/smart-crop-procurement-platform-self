# 🌾 Apni Baari (अपनी बारी)
हर किसान की बारी, सही समय की जानकारी

### Digital Procurement Scheduling & Queue Management Platform for Farmers

> From waiting for your turn → to knowing your turn.

Apni Baari is a digital platform designed to make agricultural procurement more organized, transparent, and convenient for farmers.

The platform aims to help farmers register, book procurement slots, receive digital tokens, track their queue, and know their procurement status without unnecessary waiting or repeated visits to procurement centers.

---

## 📌 Problem Statement

Farmers often face difficulties during crop procurement, including:

- Long queues at procurement centers
- Uncertainty about when their turn will come
- Overcrowding at procurement centers
- Multiple unnecessary visits
- Lack of real-time procurement status
- Difficulty accessing digital services
- Limited transparency in the procurement process

These problems can result in wasted time, transportation costs, overcrowding, and frustration for farmers.

---

## 💡 Our Solution

Apni Baari proposes a centralized digital system connecting:

**Farmers → Procurement Centers → Government Officials**

The system is designed to provide farmers with a clear procurement journey:

**Register → Book Slot → Get Token → Track Queue → Reach Center → Procurement → Payment Tracking**

---

## 🚜 Key Features

### 👨‍🌾 Farmer Portal

- Farmer registration
- Farmer login using OTP
- Farmer profile
- Crop and cultivation details
- Procurement slot booking
- Digital token / e-token
- QR-based token verification
- Live queue status
- Estimated waiting time
- Procurement status tracking
- Notifications and updates

### 📅 Slot Booking

Farmers can select an available procurement center and preferred time slot.

The objective is to distribute farmers across available slots and reduce unnecessary crowding.

### 🎟️ Digital Token

After booking a slot, the farmer can receive a digital token containing relevant booking information.

The token can later be used for verification at the procurement center.

### 📊 Queue Management

Farmers can view:

- Current queue position
- Token status
- Estimated waiting time
- Procurement center status
- Booking progress

This allows farmers to know when their turn is approaching instead of waiting blindly at the center.

### 🏛️ Government Dashboard

Government officials can monitor procurement activities through a dedicated dashboard.

Planned monitoring includes:

- Procurement centers
- Available slots
- Farmer bookings
- Queue status
- Center workload
- Procurement progress
- Notifications
- Reports and analytics

### 💬 WhatsApp Slot Booking

A planned feature of Apni Baari is a WhatsApp-based slot booking system.

Farmers who may find a web application difficult to use can interact with the system through WhatsApp.

The planned workflow includes:

**WhatsApp → OTP Authentication → Slot Selection → Booking Confirmation → Digital Token**

This feature is intended to make the platform more accessible to farmers who primarily use mobile messaging services.

---

## 🔄 How Apni Baari Works

```text
Farmer
   ↓
Registration / Login
   ↓
Select Procurement Center
   ↓
Check Available Slots
   ↓
Book Slot
   ↓
Receive Digital Token
   ↓
Track Queue / Waiting Time
   ↓
Reach Procurement Center
   ↓
Token / QR Verification
   ↓
Crop Procurement
   ↓
Procurement Status
   ↓
Payment / DBT Tracking
```

---

## 🏗️ Proposed System Architecture

```text
                  APNI BAARI
                      │
          ┌───────────┴───────────┐
          │                       │
      Farmer Portal        Government Portal
          │                       │
          └───────────┬───────────┘
                      │
                Backend API
                      │
                  Database
                      │
          ┌───────────┼───────────┐
          │           │           │
       Booking      Queue     Notifications
          │           │           │
          └───────────┼───────────┘
                      │
              Procurement Centers
```

---

## 🛠️ Technology Stack

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- FastAPI (planned/in development)

### Database
- Relational database (planned)

### Authentication
- OTP-based authentication (planned)

### Integrations
- WhatsApp-based interaction (planned)
- QR verification
- Notification services
- Government system integrations (future scope)

---

## 📂 Project Structure

```text
smart-crop-procurement-platform-self/
│
└── Dashboard/
    │
    ├── farmer-login.html
    ├── registration.html
    ├── dashboard.html
    │
    ├── gov-dashboard.html
    ├── gov-analytics.html
    ├── gov-live-centers.html
    ├── gov-notifications.html
    ├── gov-procurement.html
    ├── gov-queue-management.html
    ├── gov-reports.html
    ├── gov-settings.html
    ├── gov-slot-management.html
    │
    ├── admin-dashboard.html
    ├── admin-login.html
    ├── admin-audit.html
    ├── admin-approvals.html
    ├── admin-masters.html
    ├── admin-officers.html
    │
    ├── css/
    │   ├── style.css
    │   └── gov-style.css
    │
    ├── js/
    │   ├── script.js
    │   ├── gov-script.js
    │   └── api-client.js
    │
    └── backend/
        ├── main.py
        ├── database.py
        ├── services.py
        ├── seed.py
        └── test_e2e.py
```

---

## 🚧 Current Status

**Current stage: Prototype / Active Development**

The current version primarily focuses on the frontend interface, user flows, dashboards, and overall system design.

Backend integration, database connectivity, real OTP authentication, WhatsApp integration, and real-time procurement data are part of the ongoing development roadmap.

The project is not yet production-ready.

---

## 🗺️ Roadmap

### Phase 1 — Prototype
- [x] Farmer portal UI
- [x] Registration interface
- [x] Farmer dashboard
- [x] Government dashboard interface
- [x] Admin interface
- [x] Procurement workflow design

### Phase 2 — Backend
- [ ] Backend API
- [ ] Database integration
- [ ] User authentication
- [ ] OTP verification
- [ ] Slot management
- [ ] Booking APIs
- [ ] Queue management

### Phase 3 — Smart Features
- [ ] Real-time queue updates
- [ ] QR-based verification
- [ ] WhatsApp bot
- [ ] Automated notifications
- [ ] Payment / DBT tracking
- [ ] Analytics

### Phase 4 — Advanced Development
- [ ] AI-based queue prediction
- [ ] Regional language support
- [ ] Voice-based assistance
- [ ] Location-based services
- [ ] Mobile application
- [ ] Cloud deployment
- [ ] Integration with relevant government systems

---

## 🎯 Objectives

Apni Baari aims to:

- Reduce unnecessary waiting at procurement centers
- Reduce overcrowding
- Improve procurement scheduling
- Provide transparency to farmers
- Digitize the farmer procurement journey
- Improve monitoring for government officials
- Make digital procurement services more accessible

---

## 🌱 Expected Impact

If implemented at scale, the system could help create a more organized procurement process where farmers have better visibility into:

**Where to go → When to go → What is their turn → What is happening with their procurement**

The broader goal is to reduce uncertainty and make the procurement experience more predictable and transparent.

---

## 🔮 Future Vision

Apni Baari is not intended to remain only a prototype.

The long-term vision is to develop it into a scalable digital procurement platform that can combine:

- Scheduling
- Queue management
- Digital verification
- Real-time monitoring
- Farmer notifications
- AI-assisted predictions
- Regional language accessibility
- Government integrations

The goal is to build technology around the actual needs of farmers, rather than simply digitizing an existing process.

---

## 👩‍💻 Developer

**Muskan Mishra**  
B.Tech — Computer Science & Engineering (AI)

This project is being developed as an independent continuation of the Apni Baari concept.

---

## 📄 License

This project is currently intended for educational, research, and development purposes.

---

## 🌾 Apni Baari

> A farmer should not have to spend an entire day waiting to find out when their turn will come.

**Apni Baari — From waiting for your turn → to knowing your turn.**
