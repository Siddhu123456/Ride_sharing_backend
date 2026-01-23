--------------------------------------------------
-- 1. ENUM DEFINITIONS
--------------------------------------------------

CREATE TYPE tenant_role_enum AS ENUM (
    'RIDER','DRIVER','FLEET_OWNER','DISPATCHER',
    'TENANT_ADMIN','PLATFORM_ADMIN','SUPPORT_AGENT'
);

CREATE TYPE gender_enum AS ENUM (
    'MALE','FEMALE','OTHER','PREFER_NOT_TO_SAY'
);

CREATE TYPE approval_status_enum AS ENUM (
    'PENDING','APPROVED','REJECTED'
);

CREATE TYPE account_status_enum AS ENUM (
    'ACTIVE','INACTIVE','SUSPENDED','CLOSED'
);

CREATE TYPE driver_type_enum AS ENUM (
    'BIKE','AUTO','CAB'
);

CREATE TYPE vehicle_category_enum AS ENUM (
    'BIKE','AUTO','CAB','AC-CA'
);

CREATE TYPE vehicle_status_enum AS ENUM (
    'ACTIVE','INACTIVE','BLOCKED'
);

CREATE TYPE trip_status_enum AS ENUM (
    'REQUESTED','ASSIGNED','PICKED_UP','COMPLETED','CANCELLED'
);

CREATE TYPE payment_status_enum AS ENUM (
    'PENDING','SUCCESS','FAILED','REFUNDED'
);

CREATE TYPE support_ticket_status_enum AS ENUM (
    'OPEN','IN_PROGRESS','RESOLVED','CLOSED'
);

CREATE TYPE settlement_status_enum AS ENUM (
    'PENDING','COMPLETED','FAILED'
);

CREATE TYPE coupon_type_enum AS ENUM (
    'FLAT','PERCENTAGE'
);

CREATE TYPE fleet_document_type_enum AS ENUM (
    -- Owner / Business Identity
    'AADHAAR',
    'PAN',
    'GST_CERTIFICATE',
    'BUSINESS_REGISTRATION'     -- MSME / Shop Act / Trade License / Company Reg
);

CREATE TYPE driver_document_type_enum AS ENUM (
    'DRIVING_LICENSE',
    'AADHAAR',
    'PAN'
);


--------------------------------------------------
-- 2. CORE MASTER TABLES
--------------------------------------------------

CREATE TABLE tenant (
    tenant_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    default_currency CHAR(3) NOT NULL,
    default_timezone VARCHAR(50) NOT NULL,
    status account_status_enum NOT NULL DEFAULT 'ACTIVE',

    created_by BIGINT,
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT,
    updated_on TIMESTAMPTZ
);

CREATE TABLE country (
    country_code CHAR(2) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone_code VARCHAR(5) NOT NULL,
    default_timezone VARCHAR(50) NOT NULL,
    default_currency CHAR(3) NOT NULL,

    created_by VARCHAR(20) NOT NULL DEFAULT 'admin',
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT,
    updated_on TIMESTAMPTZ
);

CREATE TABLE city (
    city_id BIGSERIAL PRIMARY KEY,
    country_code CHAR(2) NOT NULL REFERENCES country(country_code),
    name VARCHAR(120) NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    currency CHAR(3) NOT NULL,

    created_by VARCHAR(20) NOT NULL DEFAULT 'admin',
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT,
    updated_on TIMESTAMPTZ,

    UNIQUE(country_code, name)
);

CREATE TABLE zone (
    zone_id BIGSERIAL PRIMARY KEY,
    city_id BIGINT NOT NULL REFERENCES city(city_id),
    name VARCHAR(120) NOT NULL,

    center_lat DECIMAL(9,6),
    center_lng DECIMAL(9,6),
    boundary TEXT, -- GeoJSON or WKT

    created_by VARCHAR(20) NOT NULL DEFAULT 'admin',
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT,
    updated_on TIMESTAMPTZ,

    UNIQUE(city_id, name)
);

--------------------------------------------------
-- 3. USERS & IDENTITY
--------------------------------------------------

CREATE TABLE app_user (
    user_id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(15) UNIQUE,
    email VARCHAR(150) UNIQUE,
    country_code CHAR(2) NOT NULL REFERENCES country(country_code),
    city_id BIGINT REFERENCES city(city_id),
    gender gender_enum,
    status account_status_enum NOT NULL DEFAULT 'ACTIVE',

    created_by BIGINT,
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT,
    updated_on TIMESTAMPTZ
);

CREATE TABLE user_roles (
  user_role_id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES app_user(user_id),
  user_role tenant_role_enum NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  assigned_on TIMESTAMPTZ DEFAULT now(),

  UNIQUE(user_id, user_role)
);

CREATE TABLE user_session (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
    active_role tenant_role_enum NOT NULL,
    logged_in_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    logged_out_at TIMESTAMPTZ,

    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Personal KYC for RIDER, DRIVER, or FLEET_OWNER
CREATE TABLE user_kyc (
    kyc_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,

    document_type VARCHAR(50) NOT NULL, -- e.g., PASSPORT, NATIONAL_ID
    document_number VARCHAR(100) NOT NULL,
    file_url TEXT,
    verification_status approval_status_enum NOT NULL DEFAULT 'PENDING',

    verified_by BIGINT REFERENCES app_user(user_id), -- Tenant Admin
    verified_on TIMESTAMPTZ,

    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_on TIMESTAMPTZ
);

CREATE TABLE user_auth (
    user_id BIGINT PRIMARY KEY REFERENCES app_user(user_id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    updated_on TIMESTAMPTZ
);

--------------------------------------------------
-- 4. TENANT CONFIGURATION
--------------------------------------------------

CREATE TABLE tenant_admin (
    tenant_admin_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    user_id BIGINT NOT NULL REFERENCES app_user(user_id),
    is_primary BOOLEAN DEFAULT FALSE,
	is_active BOOLEAN NOT NULL DEFAULT true;

    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, user_id)
);



CREATE TABLE tenant_city (
    tenant_city_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    city_id BIGINT NOT NULL REFERENCES city(city_id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    launched_on DATE,
    CONSTRAINT uq_tenant_city UNIQUE (tenant_id, city_id)
);

CREATE TABLE tenant_tax_rule (
    tax_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    country_code CHAR(2) NOT NULL REFERENCES country(country_code),
    tax_type VARCHAR(50),
    rate NUMERIC(5,2) NOT NULL,
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ
);

--------------------------------------------------
-- 5. FLEET & DRIVER MANAGEMENT
--------------------------------------------------

-- A user applies for a Fleet by creating this record
CREATE TABLE fleet (
    fleet_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    owner_user_id BIGINT NOT NULL REFERENCES app_user(user_id),

    fleet_name VARCHAR(150) NOT NULL,
    status account_status_enum NOT NULL DEFAULT 'INACTIVE',
    approval_status approval_status_enum NOT NULL DEFAULT 'PENDING',

    verified_by BIGINT REFERENCES app_user(user_id), -- Tenant Admin
    verified_on TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ,

    UNIQUE (tenant_id, fleet_name)
);

-- Business-specific documents for the Fleet (e.g., Company Registration)
CREATE TABLE fleet_document (
    document_id BIGSERIAL PRIMARY KEY,
    fleet_id BIGINT NOT NULL REFERENCES fleet(fleet_id) ON DELETE CASCADE,

    document_type fleet_document_type_enum NOT NULL,
    file_url TEXT NOT NULL,
    document_number VARCHAR(100),

    verification_status approval_status_enum NOT NULL DEFAULT 'PENDING',
    verified_by BIGINT REFERENCES app_user(user_id),
    verified_on TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- ✅ Only 1 document per type per fleet
    CONSTRAINT uq_fleet_document_type_per_fleet UNIQUE (fleet_id, document_type)
);

--

CREATE TABLE driver_profile (
    driver_id BIGINT PRIMARY KEY REFERENCES app_user(user_id) ON DELETE CASCADE,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),

    driver_type driver_type_enum NOT NULL,
    approval_status approval_status_enum NOT NULL DEFAULT 'PENDING',
    rating NUMERIC(3,2) DEFAULT 5.00,

    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_on TIMESTAMPTZ
);

-- Fleet Owner adds drivers here
CREATE TABLE fleet_driver (
    id BIGSERIAL PRIMARY KEY,
    fleet_id BIGINT NOT NULL REFERENCES fleet(fleet_id) ON DELETE CASCADE,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,

    approval_status approval_status_enum NOT NULL DEFAULT 'PENDING', -- Verified by Tenant Admin
    start_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    end_date TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id), -- The Fleet Owner
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (fleet_id, driver_id, start_date)
);

CREATE TABLE driver_document (
    document_id BIGSERIAL PRIMARY KEY,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,

    document_type driver_document_type_enum NOT NULL,
    file_url TEXT NOT NULL,
    document_number VARCHAR(100),

    verification_status approval_status_enum NOT NULL DEFAULT 'PENDING',
    verified_by BIGINT REFERENCES app_user(user_id), -- Tenant Admin
    verified_on TIMESTAMPTZ,

    expiry_date DATE, -- useful for DL

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_driver_document UNIQUE (driver_id, document_type)
);

--------------------------------------------------
-- 6. VEHICLES
--------------------------------------------------

CREATE TABLE vehicle (
    vehicle_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    fleet_id BIGINT REFERENCES fleet(fleet_id), -- Can be NULL for independent drivers

    category vehicle_category_enum NOT NULL,
    status vehicle_status_enum NOT NULL DEFAULT 'INACTIVE',
    approval_status approval_status_enum NOT NULL DEFAULT 'PENDING',
    
    registration_no VARCHAR(50) NOT NULL UNIQUE,
    make VARCHAR(50),
    model VARCHAR(50),
    year_of_manufacture INT,

    verified_by BIGINT REFERENCES app_user(user_id), -- Tenant Admin
    verified_on TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id), -- Fleet Owner or Independent Driver
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE vehicle_document (
    document_id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT NOT NULL REFERENCES vehicle(vehicle_id) ON DELETE CASCADE,

    document_type VARCHAR(50) NOT NULL, -- e.g., Insurance, Registration
    file_url TEXT NOT NULL,
    verification_status approval_status_enum NOT NULL DEFAULT 'PENDING',

    verified_by BIGINT REFERENCES app_user(user_id),
    verified_on TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE driver_vehicle_assignment (
    assignment_id BIGSERIAL PRIMARY KEY,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id),
    vehicle_id BIGINT NOT NULL REFERENCES vehicle(vehicle_id),

    start_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    end_time TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    UNIQUE (driver_id, vehicle_id, start_time)
);

CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE driver_vehicle_assignment
ADD CONSTRAINT no_overlap_vehicle_assignment
EXCLUDE USING gist (
    vehicle_id WITH =,
    tstzrange(start_time, COALESCE(end_time, 'infinity'::timestamptz)) WITH &&
);


--------------------------------------------------
-- 7. OPERATIONS & PRICING
--------------------------------------------------

CREATE TABLE driver_shift (
    shift_id BIGSERIAL PRIMARY KEY,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id),
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    status TEXT NOT NULL, -- ONLINE, OFFLINE, ON_TRIP
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    last_latitude DECIMAL(9,6),
    last_longitude DECIMAL(9,6)
);

ALTER TABLE driver_shift
ADD COLUMN vehicle_id BIGINT REFERENCES vehicle(vehicle_id);

ALTER TABLE driver_shift
ADD COLUMN expected_end_at TIMESTAMPTZ;



CREATE TABLE driver_location (
    driver_id BIGINT PRIMARY KEY REFERENCES app_user(user_id),
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    last_updated TIMESTAMPTZ NOT NULL
);

CREATE TABLE driver_location_history (
    id BIGSERIAL PRIMARY KEY,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id),
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE fare_config (
    fare_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    city_id BIGINT NOT NULL REFERENCES city(city_id),
    vehicle_category vehicle_category_enum NOT NULL,
    base_fare NUMERIC(10,2) NOT NULL,
    per_km NUMERIC(10,2) NOT NULL,
    per_minute NUMERIC(10,2) NOT NULL,
    minimum_fare NUMERIC(10,2) NOT NULL,
    UNIQUE (tenant_id, city_id, vehicle_category)
);

CREATE TABLE pricing_time_rule (
    rule_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    city_id BIGINT NOT NULL REFERENCES city(city_id),
    rule_type VARCHAR(50),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    multiplier NUMERIC(5,2) NOT NULL DEFAULT 1.00
);

CREATE TABLE surge_zone (
    surge_zone_id BIGSERIAL PRIMARY KEY,
    zone_id BIGINT NOT NULL REFERENCES zone(zone_id),
    created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE surge_event (
    surge_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    surge_zone_id BIGINT NOT NULL REFERENCES surge_zone(surge_zone_id),
    multiplier NUMERIC(5,2) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ
);

--------------------------------------------------
-- 8. TRIPS & DISPATCH
--------------------------------------------------
CREATE TABLE trip (
    trip_id BIGSERIAL PRIMARY KEY,

    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    rider_id BIGINT NOT NULL REFERENCES app_user(user_id),
    driver_id BIGINT REFERENCES app_user(user_id),
    vehicle_id BIGINT REFERENCES vehicle(vehicle_id),

    city_id BIGINT NOT NULL REFERENCES city(city_id),
    zone_id BIGINT REFERENCES zone(zone_id),

    pickup_lat DECIMAL(9,6) NOT NULL,
    pickup_lng DECIMAL(9,6) NOT NULL,
    drop_lat DECIMAL(9,6),
    drop_lng DECIMAL(9,6),

    vehicle_category vehicle_category_enum NOT NULL DEFAULT 'BIKE',

    status trip_status_enum NOT NULL DEFAULT 'REQUESTED',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    assigned_at TIMESTAMPTZ,
    picked_up_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,

    fare_amount NUMERIC(10,2),
    driver_earning NUMERIC(10,2),
    platform_fee NUMERIC(10,2),
    payment_status payment_status_enum DEFAULT 'PENDING',

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE dispatch_attempt (
    attempt_id BIGSERIAL PRIMARY KEY,

    trip_id BIGINT NOT NULL REFERENCES trip(trip_id) ON DELETE CASCADE,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id),

    sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    responded_at TIMESTAMPTZ,
    response TEXT, -- ACCEPTED, REJECTED, TIMEOUT

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ,

    CONSTRAINT uq_dispatch_attempt_trip_driver UNIQUE (trip_id, driver_id)
);




CREATE TABLE trip_otp (
    otp_id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id) ON DELETE CASCADE,
    otp_code VARCHAR(10) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE trip_fare_breakdown (
    id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id),
    base_fare NUMERIC(10,2),
    distance_fare NUMERIC(10,2),
    time_fare NUMERIC(10,2),
    surge_amount NUMERIC(10,2),
    tax_amount NUMERIC(10,2),
    discount_amount NUMERIC(10,2),
    final_fare NUMERIC(10,2) NOT NULL
);

--------------------------------------------------
-- 9. WALLETS & LEDGERS
--------------------------------------------------

CREATE TABLE platform_wallet (
    id SMALLINT PRIMARY KEY DEFAULT 1,
    balance NUMERIC(14,2) NOT NULL DEFAULT 0
);

CREATE TABLE tenant_wallet (
    tenant_id BIGINT PRIMARY KEY REFERENCES tenant(tenant_id),
    balance NUMERIC(12,2) NOT NULL DEFAULT 0
);

CREATE TABLE driver_wallet (
    driver_id BIGINT PRIMARY KEY REFERENCES app_user(user_id),
    balance NUMERIC(12,2) NOT NULL DEFAULT 0
);

CREATE TABLE payment (
    payment_id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id),
    amount NUMERIC(10,2) NOT NULL,
    currency CHAR(3) NOT NULL,
    payment_mode TEXT,
    status payment_status_enum NOT NULL
);

CREATE TABLE platform_ledger (
    entry_id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT REFERENCES trip(trip_id),
    amount NUMERIC(12,2) NOT NULL,
    entry_type TEXT NOT NULL, -- CREDIT, DEBIT
    created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE tenant_ledger (
    entry_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    trip_id BIGINT REFERENCES trip(trip_id),
    amount NUMERIC(12,2) NOT NULL,
    entry_type TEXT NOT NULL,
    created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE fleet_ledger (
    entry_id BIGSERIAL PRIMARY KEY,
    fleet_id BIGINT NOT NULL REFERENCES fleet(fleet_id),
    trip_id BIGINT REFERENCES trip(trip_id),
    amount NUMERIC(12,2) NOT NULL,
    entry_type TEXT NOT NULL,
    created_on TIMESTAMPTZ DEFAULT now()
);

--------------------------------------------------
-- 10. SAFETY, SUPPORT & RATINGS
--------------------------------------------------

CREATE TABLE sos_event (
    sos_id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id),
    triggered_by BIGINT NOT NULL REFERENCES app_user(user_id),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE support_ticket (
    ticket_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(user_id),
    trip_id BIGINT REFERENCES trip(trip_id),
    status support_ticket_status_enum NOT NULL DEFAULT 'OPEN',
    assigned_to BIGINT REFERENCES app_user(user_id), -- Support Agent
    created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE trip_rating (
    rating_id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id),
    rater_id BIGINT NOT NULL REFERENCES app_user(user_id),
    ratee_id BIGINT NOT NULL REFERENCES app_user(user_id),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_on TIMESTAMPTZ DEFAULT now()
);

--------------------------------------------------
-- 11. COUPONS & INCENTIVES
--------------------------------------------------

CREATE TABLE coupon (
    coupon_id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    coupon_type coupon_type_enum NOT NULL,
    value NUMERIC(10,2) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    max_uses INT,
    per_user_limit INT DEFAULT 1
);

CREATE TABLE coupon_tenant (
    coupon_id BIGINT REFERENCES coupon(coupon_id),
    tenant_id BIGINT REFERENCES tenant(tenant_id),
    PRIMARY KEY (coupon_id, tenant_id)
);

CREATE TABLE driver_incentive_scheme (
    scheme_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    name VARCHAR(150) NOT NULL,
    criteria JSONB NOT NULL, -- e.g., {"trips_required": 50}
    reward_amount NUMERIC(10,2) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL
);

CREATE TABLE driver_incentive_reward (
    reward_id BIGSERIAL PRIMARY KEY,
    scheme_id BIGINT NOT NULL REFERENCES driver_incentive_scheme(scheme_id),
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id),
    amount NUMERIC(10,2) NOT NULL,
    paid BOOLEAN DEFAULT FALSE,
    created_on TIMESTAMPTZ DEFAULT now()
);
