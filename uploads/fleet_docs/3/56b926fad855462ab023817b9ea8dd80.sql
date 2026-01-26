--------------------------------------------------
-- LOOKUP TABLES (Must come first)
--------------------------------------------------

CREATE TABLE lu_tenant_role (
    role_code TEXT PRIMARY KEY
);

INSERT INTO lu_tenant_role VALUES
('RIDER'),('DRIVER'),('FLEET_OWNER'),('DISPATCHER'),
('TENANT_ADMIN'),('PLATFORM_ADMIN'),('SUPPORT_AGENT');

CREATE TABLE lu_gender (
    gender_code TEXT PRIMARY KEY
);

INSERT INTO lu_gender VALUES
('MALE'),('FEMALE'),('OTHER'),('PREFER_NOT_TO_SAY');

CREATE TABLE lu_approval_status (
    status_code TEXT PRIMARY KEY
);

INSERT INTO lu_approval_status VALUES
('PENDING'),('APPROVED'),('REJECTED');

CREATE TABLE lu_account_status (
    status_code TEXT PRIMARY KEY
);

INSERT INTO lu_account_status VALUES
('ACTIVE'),('INACTIVE'),('SUSPENDED'),('CLOSED');

CREATE TABLE lu_driver_type (
    type_code TEXT PRIMARY KEY
);

INSERT INTO lu_driver_type VALUES
('INDEPENDENT'),('FLEET');

CREATE TABLE lu_vehicle_category (
    category_code TEXT PRIMARY KEY
);

INSERT INTO lu_vehicle_category VALUES
('BIKE'),('AUTO'),('SEDAN'),('SUV'),('LUXURY');

CREATE TABLE lu_vehicle_status (
    status_code TEXT PRIMARY KEY
);

INSERT INTO lu_vehicle_status VALUES
('ACTIVE'),('INACTIVE'),('BLOCKED');

CREATE TABLE lu_trip_status (
    status_code TEXT PRIMARY KEY
);

INSERT INTO lu_trip_status VALUES
('REQUESTED'),('ASSIGNED'),('PICKED_UP'),('COMPLETED'),('CANCELLED');

CREATE TABLE lu_payment_status (
    status_code TEXT PRIMARY KEY
);

INSERT INTO lu_payment_status VALUES
('PENDING'),('SUCCESS'),('FAILED'),('REFUNDED');

CREATE TABLE lu_support_ticket_status (
    status_code TEXT PRIMARY KEY
);

INSERT INTO lu_support_ticket_status VALUES
('OPEN'),('IN_PROGRESS'),('RESOLVED'),('CLOSED');

CREATE TABLE lu_settlement_status (
    status_code TEXT PRIMARY KEY
);

INSERT INTO lu_settlement_status VALUES
('PENDING'),('COMPLETED'),('FAILED');

CREATE TABLE lu_coupon_type (
    type_code TEXT PRIMARY KEY
);

INSERT INTO lu_coupon_type VALUES
('FLAT'),('PERCENTAGE');

--------------------------------------------------
-- CORE MASTER TABLES
--------------------------------------------------

CREATE TABLE tenant (
    tenant_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    default_currency CHAR(3) NOT NULL,
    default_timezone VARCHAR(50) NOT NULL,
    status TEXT NOT NULL REFERENCES lu_account_status(status_code),

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

    created_by BIGINT,
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

    created_by BIGINT,
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
    boundary TEXT,

    created_by BIGINT,
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT,
    updated_on TIMESTAMPTZ,

    UNIQUE(city_id, name)
);

--------------------------------------------------
-- USERS & IDENTITY
--------------------------------------------------

CREATE TABLE app_user (
    user_id BIGSERIAL PRIMARY KEY,

    full_name VARCHAR(150) NOT NULL,

    phone VARCHAR(15) UNIQUE,
    email VARCHAR(150) UNIQUE,

    country_code CHAR(2) NOT NULL REFERENCES country(country_code),
    city_id BIGINT REFERENCES city(city_id),

    gender TEXT REFERENCES lu_gender(gender_code),
    role TEXT NOT NULL REFERENCES lu_tenant_role(role_code),
    status TEXT NOT NULL REFERENCES lu_account_status(status_code),

    created_by BIGINT,
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT,
    updated_on TIMESTAMPTZ
);

CREATE TABLE user_session (
    session_id UUID PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,

    login_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    logout_at TIMESTAMPTZ,
    ip_address INET,
    user_agent TEXT,

    created_by BIGINT,
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT,
    updated_on TIMESTAMPTZ
);

CREATE TABLE user_kyc (
    kyc_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,

    document_type VARCHAR(50) NOT NULL,
    document_number VARCHAR(100) NOT NULL,
    verification_status TEXT NOT NULL REFERENCES lu_approval_status(status_code),

    verified_by BIGINT,
    verified_on TIMESTAMPTZ,

    created_by BIGINT,
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT,
    updated_on TIMESTAMPTZ
);


CREATE TABLE user_auth (
    user_id BIGINT PRIMARY KEY
        REFERENCES app_user(user_id)
        ON DELETE CASCADE,

    password_hash TEXT NOT NULL,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    last_password_change TIMESTAMPTZ,

    created_by BIGINT,
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT,
    updated_on TIMESTAMPTZ
);

------------------PART2-----------------------
--------------------------------------------------
-- TENANT MAPPINGS
--------------------------------------------------

CREATE TABLE tenant_admin (
    tenant_admin_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    user_id BIGINT NOT NULL REFERENCES app_user(user_id),
    is_primary BOOLEAN DEFAULT FALSE,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ,

    UNIQUE (tenant_id, user_id)
);

CREATE TABLE tenant_country (
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    country_code CHAR(2) NOT NULL REFERENCES country(country_code),

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ,

    PRIMARY KEY (tenant_id, country_code)
);

CREATE TABLE tenant_city (
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    city_id BIGINT NOT NULL REFERENCES city(city_id),

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ,

    PRIMARY KEY (tenant_id, city_id)
);

CREATE TABLE tenant_tax_rule (
    tax_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    country_code CHAR(2) NOT NULL REFERENCES country(country_code),

    tax_type VARCHAR(50),
    rate NUMERIC(5,2) NOT NULL,
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);

--------------------------------------------------
-- DRIVER & FLEET MANAGEMENT
--------------------------------------------------

CREATE TABLE driver_profile (
    driver_id BIGINT PRIMARY KEY REFERENCES app_user(user_id) ON DELETE CASCADE,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),

    driver_type TEXT NOT NULL REFERENCES lu_driver_type(type_code),
    approval_status TEXT NOT NULL REFERENCES lu_approval_status(status_code),
    rating NUMERIC(3,2) DEFAULT 5.00,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE fleet (
    fleet_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    owner_user_id BIGINT NOT NULL REFERENCES app_user(user_id),

    fleet_name VARCHAR(150) NOT NULL,
    status TEXT NOT NULL REFERENCES lu_account_status(status_code),
    approval_status TEXT NOT NULL REFERENCES lu_approval_status(status_code),

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ,

    UNIQUE (tenant_id, fleet_name)
);

CREATE TABLE fleet_driver (
    id BIGSERIAL PRIMARY KEY,
    fleet_id BIGINT NOT NULL REFERENCES fleet(fleet_id) ON DELETE CASCADE,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,

    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ,

    UNIQUE (fleet_id, driver_id, start_date)
);

--------------------------------------------------
-- VEHICLES
--------------------------------------------------

CREATE TABLE vehicle (
    vehicle_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    fleet_id BIGINT NOT NULL REFERENCES fleet(fleet_id),

    category TEXT NOT NULL REFERENCES lu_vehicle_category(category_code),
    status TEXT NOT NULL REFERENCES lu_vehicle_status(status_code),
    registration_no VARCHAR(50) NOT NULL UNIQUE,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE vehicle_document (
    document_id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT NOT NULL REFERENCES vehicle(vehicle_id) ON DELETE CASCADE,

    document_type VARCHAR(50) NOT NULL,
    file_url TEXT NOT NULL,
    verification_status TEXT NOT NULL REFERENCES lu_approval_status(status_code),

    verified_by BIGINT REFERENCES app_user(user_id),
    verified_on TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE driver_vehicle_assignment (
    assignment_id BIGSERIAL PRIMARY KEY,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id),
    vehicle_id BIGINT NOT NULL REFERENCES vehicle(vehicle_id),

    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ,

    UNIQUE (driver_id, vehicle_id, start_time)
);

--------------------------------------------------
-- DRIVER OPERATIONS
--------------------------------------------------

CREATE TABLE driver_shift (
    shift_id BIGSERIAL PRIMARY KEY,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),

    status TEXT NOT NULL,

    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,

    last_latitude DECIMAL(9,6),
    last_longitude DECIMAL(9,6),

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE driver_location (
    driver_id BIGINT PRIMARY KEY REFERENCES app_user(user_id) ON DELETE CASCADE,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    last_updated TIMESTAMPTZ NOT NULL
);

CREATE TABLE driver_location_history (
    id BIGSERIAL PRIMARY KEY,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL
);
----------------PART3--------------------
--------------------------------------------------
-- PRICING & SURGING
--------------------------------------------------

CREATE TABLE fare_config (
    fare_id BIGSERIAL PRIMARY KEY,

    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    city_id BIGINT NOT NULL REFERENCES city(city_id),
    vehicle_category TEXT NOT NULL REFERENCES lu_vehicle_category(category_code),

    base_fare NUMERIC(10,2) NOT NULL,
    per_km NUMERIC(10,2) NOT NULL,
    per_minute NUMERIC(10,2) NOT NULL,
    minimum_fare NUMERIC(10,2) NOT NULL,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ,

    UNIQUE (tenant_id, city_id, vehicle_category)
);

CREATE TABLE pricing_time_rule (
    rule_id BIGSERIAL PRIMARY KEY,

    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    city_id BIGINT NOT NULL REFERENCES city(city_id),

    rule_type VARCHAR(50) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    multiplier NUMERIC(5,2) NOT NULL,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE surge_zone (
    surge_zone_id BIGSERIAL PRIMARY KEY,
    zone_id BIGINT NOT NULL REFERENCES zone(zone_id),

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE surge_event (
    surge_id BIGSERIAL PRIMARY KEY,

    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    surge_zone_id BIGINT NOT NULL REFERENCES surge_zone(surge_zone_id),

    multiplier NUMERIC(5,2) NOT NULL,
    demand_index INT,
    supply_index INT,

    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

--------------------------------------------------
-- TRIPS & DISPATCH
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

    status TEXT NOT NULL REFERENCES lu_trip_status(status_code),

    requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    assigned_at TIMESTAMPTZ,
    picked_up_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,

    fare_amount NUMERIC(10,2),
    driver_earning NUMERIC(10,2),
    platform_fee NUMERIC(10,2),

    payment_status TEXT REFERENCES lu_payment_status(status_code),

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE dispatch_attempt (
    attempt_id BIGSERIAL PRIMARY KEY,

    trip_id BIGINT NOT NULL REFERENCES trip(trip_id) ON DELETE CASCADE,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id),

    sent_at TIMESTAMPTZ NOT NULL,
    responded_at TIMESTAMPTZ,
    response TEXT,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE trip_route_point (
    id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id) ON DELETE CASCADE,

    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE dispatcher_assignment (
    assignment_id BIGSERIAL PRIMARY KEY,

    dispatcher_id BIGINT NOT NULL REFERENCES app_user(user_id),
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    city_id BIGINT REFERENCES city(city_id),
    zone_id BIGINT REFERENCES zone(zone_id),

    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ,

    UNIQUE (dispatcher_id, tenant_id, start_time)
);

CREATE TABLE trip_cancellation (
    cancel_id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id) ON DELETE CASCADE,
    cancelled_by BIGINT NOT NULL REFERENCES app_user(user_id),
    reason TEXT,
    cancelled_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE trip_otp (
    otp_id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id) ON DELETE CASCADE,

    otp_code VARCHAR(10) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT FALSE,

    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE trip_fare_breakdown (
    id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id),

    base_fare NUMERIC(10,2),
    distance_fare NUMERIC(10,2),
    time_fare NUMERIC(10,2),
    surge_amount NUMERIC(10,2),
    night_charge NUMERIC(10,2),
    tax_amount NUMERIC(10,2),
    discount_amount NUMERIC(10,2),

    final_fare NUMERIC(10,2) NOT NULL,

    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);

--------------------------------------------------
-- PAYMENTS & WALLETS
--------------------------------------------------

CREATE TABLE payment (
    payment_id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id),

    amount NUMERIC(10,2) NOT NULL,
    currency CHAR(3) NOT NULL,
    payment_mode TEXT NOT NULL,
    status TEXT NOT NULL REFERENCES lu_payment_status(status_code),

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE driver_wallet (
    driver_id BIGINT PRIMARY KEY REFERENCES app_user(user_id),
    balance NUMERIC(12,2) NOT NULL DEFAULT 0,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE platform_wallet (
    id SMALLINT PRIMARY KEY DEFAULT 1,
    balance NUMERIC(14,2) NOT NULL DEFAULT 0,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE tenant_wallet (
    tenant_id BIGINT PRIMARY KEY REFERENCES tenant(tenant_id),
    balance NUMERIC(12,2) NOT NULL DEFAULT 0,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE tenant_settlement (
    settlement_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),

    amount NUMERIC(12,2) NOT NULL,
    status TEXT NOT NULL REFERENCES lu_settlement_status(status_code),

    requested_at TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE refund (
    refund_id BIGSERIAL PRIMARY KEY,
    payment_id BIGINT NOT NULL REFERENCES payment(payment_id),

    amount NUMERIC(10,2) NOT NULL,
    reason TEXT,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);

--------------------------------------------------
-- LEDGERS
--------------------------------------------------

CREATE TABLE platform_ledger (
    entry_id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT REFERENCES trip(trip_id),

    amount NUMERIC(12,2) NOT NULL,
    entry_type TEXT NOT NULL,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tenant_ledger (
    entry_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    trip_id BIGINT REFERENCES trip(trip_id),

    amount NUMERIC(12,2) NOT NULL,
    entry_type TEXT NOT NULL,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE fleet_ledger (
    entry_id BIGSERIAL PRIMARY KEY,
    fleet_id BIGINT NOT NULL REFERENCES fleet(fleet_id),
    trip_id BIGINT REFERENCES trip(trip_id),

    amount NUMERIC(12,2) NOT NULL,
    entry_type TEXT NOT NULL,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);
-----------------PART 4-----------------------
--------------------------------------------------
-- SAFETY & SUPPORT
--------------------------------------------------

CREATE TABLE sos_event (
    sos_id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id),
    triggered_by BIGINT NOT NULL REFERENCES app_user(user_id),

    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),

    triggered_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE support_ticket (
    ticket_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(user_id),
    trip_id BIGINT REFERENCES trip(trip_id),
    sos_id BIGINT REFERENCES sos_event(sos_id),

    issue_type VARCHAR(100),
    severity VARCHAR(20),
    status TEXT NOT NULL REFERENCES lu_support_ticket_status(status_code),

    assigned_to BIGINT REFERENCES app_user(user_id),
    assigned_at TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE support_ticket_conversation (
    message_id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES support_ticket(ticket_id),
    sender_id BIGINT NOT NULL REFERENCES app_user(user_id),

    message_text TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE support_ticket_assignment_history (
    history_id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES support_ticket(ticket_id),
    assigned_to BIGINT REFERENCES app_user(user_id),

    assigned_at TIMESTAMPTZ NOT NULL,
    unassigned_at TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE lost_item_report (
    report_id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id),
    user_id BIGINT NOT NULL REFERENCES app_user(user_id),

    description TEXT NOT NULL,
    status VARCHAR(50),

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

--------------------------------------------------
-- RATINGS
--------------------------------------------------

CREATE TABLE trip_rating (
    rating_id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trip(trip_id),

    rater_id BIGINT NOT NULL REFERENCES app_user(user_id),
    ratee_id BIGINT NOT NULL REFERENCES app_user(user_id),

    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,

    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE driver_rating_summary (
    driver_id BIGINT PRIMARY KEY REFERENCES app_user(user_id),
    avg_rating NUMERIC(3,2),
    total_ratings INT,
    updated_on TIMESTAMPTZ
);

CREATE TABLE rider_rating_summary (
    rider_id BIGINT PRIMARY KEY REFERENCES app_user(user_id),
    avg_rating NUMERIC(3,2),
    total_ratings INT,
    updated_on TIMESTAMPTZ
);

CREATE TABLE tenant_rating_summary (
    tenant_id BIGINT PRIMARY KEY REFERENCES tenant(tenant_id),
    avg_rating NUMERIC(3,2),
    total_ratings INT,
    updated_on TIMESTAMPTZ
);

--------------------------------------------------
-- COUPONS & PROMOTIONS
--------------------------------------------------

CREATE TABLE coupon (
    coupon_id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    coupon_type TEXT NOT NULL REFERENCES lu_coupon_type(type_code),

    value NUMERIC(10,2) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,

    max_uses INT,
    per_user_limit INT,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE coupon_tenant (
    coupon_id BIGINT REFERENCES coupon(coupon_id),
    tenant_id BIGINT REFERENCES tenant(tenant_id),

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (coupon_id, tenant_id)
);

CREATE TABLE coupon_redemption (
    redemption_id BIGSERIAL PRIMARY KEY,
    coupon_id BIGINT NOT NULL REFERENCES coupon(coupon_id),
    user_id BIGINT NOT NULL REFERENCES app_user(user_id),
    trip_id BIGINT REFERENCES trip(trip_id),

    redeemed_at TIMESTAMPTZ NOT NULL,
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (coupon_id, user_id, trip_id)
);

--------------------------------------------------
-- DRIVER INCENTIVES & REWARDS
--------------------------------------------------

CREATE TABLE driver_incentive_scheme (
    scheme_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),

    name VARCHAR(150) NOT NULL,
    description TEXT,

    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,

    criteria JSONB NOT NULL,
    reward_amount NUMERIC(10,2) NOT NULL,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);

CREATE TABLE driver_incentive_progress (
    id BIGSERIAL PRIMARY KEY,
    scheme_id BIGINT NOT NULL REFERENCES driver_incentive_scheme(scheme_id),
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id),

    progress_value INT NOT NULL DEFAULT 0,
    achieved BOOLEAN NOT NULL DEFAULT FALSE,

    updated_on TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (scheme_id, driver_id)
);

CREATE TABLE driver_incentive_reward (
    reward_id BIGSERIAL PRIMARY KEY,
    scheme_id BIGINT NOT NULL REFERENCES driver_incentive_scheme(scheme_id),
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id),

    amount NUMERIC(10,2) NOT NULL,
    paid BOOLEAN NOT NULL DEFAULT FALSE,

    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);

select * from lu_gender;



INSERT INTO country (
  country_code, name, phone_code, default_timezone, default_currency
) VALUES
('IN', 'India', '+91', 'Asia/Kolkata', 'INR');

INSERT INTO city (
  country_code, name, timezone, currency
) VALUES
('IN', 'Hyderabad', 'Asia/Kolkata', 'INR');

INSERT INTO tenant (
  name, default_currency, default_timezone, status
) VALUES
('RideSharing India', 'INR', 'Asia/Kolkata', 'ACTIVE');
INSERT INTO app_user
(full_name, email, role, status, country_code)
VALUES
('Platform Admin', 'admin@test.com', 'PLATFORM_ADMIN', 'ACTIVE', 'IN');


INSERT INTO user_auth (user_id, password_hash, is_locked, last_password_change)
VALUES (1, '$2b$12$pMo4NrEO1paQPuf9sDvibegdkBP7S3kDANNbUI.iQmUB5u0Lz5KDe', FALSE, now());

select * from app_user;
select * from user_auth;
UPDATE user_auth
SET password_hash = '$2b$12$2WjEUXGBdxqS0kpMfYWQ0.Opw8ljITCy02SYj62lu7bK9uoTPzM2G',
    is_locked = FALSE,
    last_password_change = now()
WHERE user_id = 1;

select * from user_session;

INSERT INTO app_user
(full_name, email, role, status, country_code)
VALUES
('Tenant_Admin', 'tenantadmin@test.com', 'TENANT_ADMIN', 'ACTIVE', 'IN');

INSERT INTO user_auth (user_id, password_hash, is_locked, last_password_change)
VALUES (2, '$2b$12$J7D/.VEGWDDTzX8gUnm6y.YknAhT6M5k.AOr50/fLJrf82Hpehb3a', FALSE, now());


select * from user_auth;

select * from lu_tenant_role;

INSERT INTO app_user
(full_name, email, role, status, country_code)
VALUES
('Driver2', 'driver2@test.com', 'DRIVER', 'ACTIVE', 'IN');

select * from driver_profile;
INSERT INTO user_auth (user_id, password_hash, is_locked, last_password_change)
VALUES (4, '$2b$12$cRJoCUxObd.45k3aVZh.z.BFANmgKAvtpIGsHo6JzSRBr5VIvEn5a', FALSE, now());

select * from tenant_admin;

select * from user_session;

select * from tenant;


Insert into tenant_admin(tenant_admin_id,tenant_id,user_id,is_primary) values(1,1,2,TRUE)

