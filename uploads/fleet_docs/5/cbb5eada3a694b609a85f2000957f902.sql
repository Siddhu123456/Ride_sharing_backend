-- UUID generator for user_session.session_id
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ✅ Geo support
CREATE EXTENSION IF NOT EXISTS postgis;

-- ✅ For overlap exclusion constraint (already used)
CREATE EXTENSION IF NOT EXISTS btree_gist;


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
    'BIKE','AUTO','CAB','AC-CAB'
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
    'AADHAAR',
    'PAN',
    'GST_CERTIFICATE',
    'BUSINESS_REGISTRATION'
);

CREATE TYPE driver_document_type_enum AS ENUM (
    'DRIVING_LICENSE',
    'AADHAAR',
    'PAN'
);

CREATE TYPE vehicle_document_type_enum AS ENUM (
    'INSURANCE',
    'REGISTRATION'
);



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

    -- ✅ NEW: City Boundary Polygon
    boundary geometry(POLYGON, 4326),

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

    -- ✅ UPDATED to PostGIS polygon
    boundary geometry(POLYGON, 4326),

    created_by VARCHAR(20) NOT NULL DEFAULT 'admin',
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT,
    updated_on TIMESTAMPTZ,

    UNIQUE(city_id, name)
);


CREATE TABLE app_user (
    user_id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(15) UNIQUE,
    email VARCHAR(150) UNIQUE,
    country_code CHAR(2) NOT NULL REFERENCES country(country_code),

    -- Optional (can be null because GPS decides city)
    city_id BIGINT REFERENCES city(city_id),

    gender gender_enum,
    status account_status_enum NOT NULL DEFAULT 'ACTIVE',

    created_by BIGINT,
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT,
    updated_on TIMESTAMPTZ
);

CREATE TABLE user_auth (
    user_id BIGINT PRIMARY KEY REFERENCES app_user(user_id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
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


CREATE TABLE user_kyc (
    kyc_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,

    document_type VARCHAR(50) NOT NULL,
    document_number VARCHAR(100) NOT NULL,
    file_url TEXT,
    verification_status approval_status_enum NOT NULL DEFAULT 'PENDING',

    verified_by BIGINT REFERENCES app_user(user_id),
    verified_on TIMESTAMPTZ,

    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_on TIMESTAMPTZ
);


CREATE TABLE tenant_admin (
    tenant_admin_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    user_id BIGINT NOT NULL REFERENCES app_user(user_id),
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

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


CREATE TABLE fleet (
    fleet_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    owner_user_id BIGINT NOT NULL REFERENCES app_user(user_id),

    fleet_name VARCHAR(150) NOT NULL,
    status account_status_enum NOT NULL DEFAULT 'INACTIVE',
    approval_status approval_status_enum NOT NULL DEFAULT 'PENDING',

    verified_by BIGINT REFERENCES app_user(user_id),
    verified_on TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ,

    UNIQUE (tenant_id, fleet_name)
);


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

    CONSTRAINT uq_fleet_document_type_per_fleet UNIQUE (fleet_id, document_type)
);


CREATE TABLE driver_profile (
    driver_id BIGINT PRIMARY KEY REFERENCES app_user(user_id) ON DELETE CASCADE,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),

    driver_type driver_type_enum NOT NULL,
    approval_status approval_status_enum NOT NULL DEFAULT 'PENDING',
    rating NUMERIC(3,2) DEFAULT 5.00,

    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_on TIMESTAMPTZ
);


CREATE TABLE fleet_driver (
    id BIGSERIAL PRIMARY KEY,
    fleet_id BIGINT NOT NULL REFERENCES fleet(fleet_id) ON DELETE CASCADE,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,

    approval_status approval_status_enum NOT NULL DEFAULT 'PENDING',
    start_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    end_date TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
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
    verified_by BIGINT REFERENCES app_user(user_id),
    verified_on TIMESTAMPTZ,

    expiry_date DATE,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_driver_document UNIQUE (driver_id, document_type)
);


CREATE TABLE vehicle (
    vehicle_id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),
    fleet_id BIGINT REFERENCES fleet(fleet_id),

    category vehicle_category_enum NOT NULL,
    status vehicle_status_enum NOT NULL DEFAULT 'INACTIVE',
    approval_status approval_status_enum NOT NULL DEFAULT 'PENDING',

    registration_no VARCHAR(50) NOT NULL UNIQUE,
    make VARCHAR(50),
    model VARCHAR(50),
    year_of_manufacture INT,

    verified_by BIGINT REFERENCES app_user(user_id),
    verified_on TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES app_user(user_id),
    updated_on TIMESTAMPTZ
);


CREATE TABLE vehicle_document (
    document_id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT NOT NULL REFERENCES vehicle(vehicle_id) ON DELETE CASCADE,

    document_type vehicle_document_type_enum NOT NULL,
    file_url TEXT NOT NULL,
    verification_status approval_status_enum NOT NULL DEFAULT 'PENDING',

    verified_by BIGINT REFERENCES app_user(user_id),
    verified_on TIMESTAMPTZ,

    created_by BIGINT REFERENCES app_user(user_id),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_vehicle_doc UNIQUE (vehicle_id, document_type)
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

ALTER TABLE driver_vehicle_assignment
ADD CONSTRAINT no_overlap_vehicle_assignment
EXCLUDE USING gist (
    vehicle_id WITH =,
    tstzrange(start_time, COALESCE(end_time, 'infinity'::timestamptz)) WITH &&
);

CREATE TABLE driver_shift (
    shift_id BIGSERIAL PRIMARY KEY,
    driver_id BIGINT NOT NULL REFERENCES app_user(user_id),
    tenant_id BIGINT NOT NULL REFERENCES tenant(tenant_id),

    vehicle_id BIGINT REFERENCES vehicle(vehicle_id),

    status TEXT NOT NULL, -- ONLINE, OFFLINE, ON_TRIP
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expected_end_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,

    last_latitude DECIMAL(9,6),
    last_longitude DECIMAL(9,6)
);


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
    updated_on TIMESTAMPTZ
);


CREATE TABLE trip_fare_breakup (
  trip_id BIGINT PRIMARY KEY REFERENCES trip,
  base_fare NUMERIC,
  distance_fare NUMERIC,
  time_fare NUMERIC,
  surge_fare NUMERIC,
  discount NUMERIC,
  tax NUMERIC,
  total_fare NUMERIC,
  created_on TIMESTAMPTZ DEFAULT now()
);

/* =========================================================
   PAYMENTS & WALLETS
========================================================= */

CREATE TABLE wallet (
  wallet_id BIGSERIAL PRIMARY KEY,
  owner_type wallet_owner_enum,
  owner_user_id BIGINT REFERENCES app_user,
  balance NUMERIC DEFAULT 0
);

CREATE TABLE wallet_transaction (
  transaction_id BIGSERIAL PRIMARY KEY,
  wallet_id BIGINT REFERENCES wallet,
  amount NUMERIC,
  transaction_type wallet_txn_type_enum,
  created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE payment (
  payment_id BIGSERIAL PRIMARY KEY,
  trip_id BIGINT REFERENCES trip,
  amount NUMERIC,
  payment_mode payment_mode_enum,
  status payment_status_enum,
  created_on TIMESTAMPTZ DEFAULT now()
);


/* =========================================================
   RATINGS & FEEDBACK
========================================================= */

CREATE TABLE trip_rating (
  rating_id BIGSERIAL PRIMARY KEY,
  trip_id BIGINT REFERENCES trip,
  tenant_id BIGINT REFERENCES tenant,
  given_by_user_id BIGINT REFERENCES app_user,
  given_to_user_id BIGINT REFERENCES app_user,
  rating SMALLINT CHECK (rating BETWEEN 1 AND 5),
  feedback TEXT,
  created_on TIMESTAMPTZ DEFAULT now()
);




/* =========================================================
   SURGE PRICING
========================================================= */

CREATE TABLE surge_zone (
  surge_zone_id BIGSERIAL PRIMARY KEY,
  tenant_id BIGINT REFERENCES tenant,
  city_id BIGINT REFERENCES city,
  name TEXT,
  center_latitude DOUBLE PRECISION,
  center_longitude DOUBLE PRECISION,
  radius_km NUMERIC,
  is_active BOOLEAN DEFAULT TRUE,
  created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE surge_event (
  surge_event_id BIGSERIAL PRIMARY KEY,
  surge_zone_id BIGINT REFERENCES surge_zone,
  vehicle_type driver_type_enum,
  surge_multiplier NUMERIC,
  started_at TIMESTAMPTZ,
  ended_at TIMESTAMPTZ,
  trigger_reason TEXT,
  created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE trip_surge_applied (
  trip_id BIGINT PRIMARY KEY REFERENCES trip,
  surge_event_id BIGINT REFERENCES surge_event,
  surge_multiplier NUMERIC,
  applied_at TIMESTAMPTZ DEFAULT now()
);


/* =========================================================
   COUPONS & PROMOTIONS
========================================================= */

CREATE TABLE coupon (
  coupon_id BIGSERIAL PRIMARY KEY,
  tenant_id BIGINT REFERENCES tenant,
  code TEXT UNIQUE,
  discount_type TEXT CHECK (discount_type IN ('FLAT','PERCENT')),
  discount_value NUMERIC,
  max_discount NUMERIC,
  min_trip_amount NUMERIC,
  valid_from TIMESTAMPTZ,
  valid_to TIMESTAMPTZ,
  usage_limit INT,
  per_user_limit INT,
  is_active BOOLEAN DEFAULT TRUE,
  created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE coupon_redemption (
  redemption_id BIGSERIAL PRIMARY KEY,
  coupon_id BIGINT REFERENCES coupon,
  trip_id BIGINT REFERENCES trip,
  rider_id BIGINT REFERENCES rider_profile,
  discount_applied NUMERIC,
  redeemed_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE trip_discount (
  trip_id BIGINT PRIMARY KEY REFERENCES trip,
  coupon_id BIGINT REFERENCES coupon,
  discount_amount NUMERIC,
  applied_at TIMESTAMPTZ DEFAULT now()
);


/* =========================================================
   SUPPORT
========================================================= */

CREATE TABLE support_ticket (
  ticket_id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES app_user,
  trip_id BIGINT REFERENCES trip,
  status support_ticket_status_enum,
  created_on TIMESTAMPTZ DEFAULT now()
);

