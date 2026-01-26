/* =========================================================
   ENUM DEFINITIONS
========================================================= */

CREATE TYPE gender_enum AS ENUM ('MALE','FEMALE','OTHER');
CREATE TYPE account_status_enum AS ENUM ('ACTIVE','INACTIVE','SUSPENDED');
CREATE TYPE approval_status_enum AS ENUM ('PENDING','APPROVED','REJECTED');
CREATE TYPE driver_type_enum AS ENUM ('BIKE','AUTO','CAR');
CREATE TYPE vehicle_status_enum AS ENUM ('PENDING','ACTIVE','SUSPENDED','REJECTED');
CREATE TYPE trip_status_enum AS ENUM ('REQUESTED','ASSIGNED','ONGOING','COMPLETED','CANCELLED');
CREATE TYPE payment_status_enum AS ENUM ('PENDING','SUCCESS','FAILED','REFUNDED');
CREATE TYPE payment_mode_enum AS ENUM ('ONLINE','OFFLINE');
CREATE TYPE support_ticket_status_enum AS ENUM ('OPEN','IN_PROGRESS','RESOLVED','CLOSED');
CREATE TYPE document_type_enum AS ENUM ('AADHAR','PAN','DRIVING_LICENSE','RC','INSURANCE','PERMIT');
CREATE TYPE document_status_enum AS ENUM ('UPLOADED','VERIFIED','REJECTED');
CREATE TYPE user_role_enum AS ENUM ('RIDER','DRIVER','FLEET_OWNER','TENANT_ADMIN');
CREATE TYPE wallet_owner_enum AS ENUM ('DRIVER','FLEET_OWNER');
CREATE TYPE wallet_txn_type_enum AS ENUM ('CREDIT','DEBIT');
CREATE TYPE invite_status_enum AS ENUM ('SENT','ACCEPTED','EXPIRED');


CREATE TYPE driver_availability_enum AS ENUM ('ONLINE','OFFLINE','BUSY');
CREATE TYPE trip_cancelled_by_enum AS ENUM ('RIDER','DRIVER','SYSTEM');




/* =========================================================
   USERS, AUTH & SESSION
========================================================= */

CREATE TABLE app_user (
  user_id BIGSERIAL PRIMARY KEY,
  full_name TEXT NOT NULL,
  gender gender_enum,
  phone TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE,
  status account_status_enum DEFAULT 'ACTIVE',
  created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE user_auth (
  user_id BIGINT PRIMARY KEY REFERENCES app_user,
  password_hash TEXT NOT NULL,
  is_locked BOOLEAN DEFAULT FALSE
);

CREATE TABLE user_roles (
  user_role_id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES app_user(user_id),

  role user_role_enum NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  assigned_on TIMESTAMPTZ DEFAULT now(),

  UNIQUE(user_id, role)
);

CREATE TABLE user_session (
  session_id UUID PRIMARY KEY,
  user_id BIGINT REFERENCES app_user,
  active_role user_role_enum,
  logged_in_at TIMESTAMPTZ DEFAULT now(),
  logged_out_at TIMESTAMPTZ
);


/* =========================================================
   TENANT & REGION
========================================================= */

CREATE TABLE tenant (
  tenant_id BIGSERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  default_currency CHAR(3) NOT NULL,
  default_timezone TEXT NOT NULL,
  status account_status_enum DEFAULT 'ACTIVE',
  created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE country (
  country_code CHAR(2) PRIMARY KEY,
  name TEXT NOT NULL,
  timezone TEXT NOT NULL,
  currency CHAR(3) NOT NULL
);

CREATE TABLE tenant_country (
  tenant_country_id BIGSERIAL PRIMARY KEY,
  tenant_id BIGINT REFERENCES tenant,
  country_code CHAR(2) REFERENCES country,
  is_active BOOLEAN DEFAULT TRUE,
  launched_on DATE,
  created_on TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, country_code)
);

CREATE TABLE city (
  city_id BIGSERIAL PRIMARY KEY,
  country_code CHAR(2) REFERENCES country,
  name TEXT NOT NULL,
  timezone TEXT NOT NULL,
  currency CHAR(3) NOT NULL,
  UNIQUE (country_code, name)
);

CREATE TABLE tenant_city (
  tenant_city_id BIGSERIAL PRIMARY KEY,
  tenant_id BIGINT REFERENCES tenant,
  city_id BIGINT REFERENCES city,
  is_active BOOLEAN DEFAULT TRUE,
  launched_on DATE,
  created_on TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, city_id)
);

CREATE TABLE tenant_admin (
  tenant_admin_id BIGSERIAL PRIMARY KEY,
  tenant_id BIGINT REFERENCES tenant,
  user_id BIGINT REFERENCES app_user,
  is_primary BOOLEAN DEFAULT FALSE,
  status account_status_enum DEFAULT 'ACTIVE',
  created_on TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, user_id)
);


/* =========================================================
   USER PROFILES
========================================================= */

CREATE TABLE rider_profile (
  rider_id BIGINT PRIMARY KEY REFERENCES app_user,
  created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE fleet_owner_profile (
  owner_id BIGINT PRIMARY KEY REFERENCES app_user,
  tenant_id BIGINT REFERENCES tenant,
  created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE driver_profile (
  driver_id BIGINT PRIMARY KEY REFERENCES app_user,
  tenant_id BIGINT REFERENCES tenant,
  driver_type driver_type_enum,
  approval_status approval_status_enum DEFAULT 'PENDING',
  availability driver_availability_enum DEFAULT 'OFFLINE',
  last_online_at TIMESTAMPTZ,
  rating NUMERIC DEFAULT 5,
  created_on TIMESTAMPTZ DEFAULT now()
);


/* =========================================================
   KYC & DOCUMENTS
========================================================= */

CREATE TABLE user_kyc (
  kyc_id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES app_user,
  kyc_role user_role_enum,
  status approval_status_enum,
  verified_at TIMESTAMPTZ,
  created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE driver_document (
  driver_document_id BIGSERIAL PRIMARY KEY,
  driver_id BIGINT REFERENCES driver_profile,
  document_type document_type_enum,
  file_url TEXT NOT NULL,
  status document_status_enum,
  expiry_date DATE,
  verified_at TIMESTAMPTZ,
  created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE vehicle_document (
  vehicle_document_id BIGSERIAL PRIMARY KEY,
  vehicle_type driver_type_enum,
  vehicle_id BIGINT,
  document_type document_type_enum,
  file_url TEXT NOT NULL,
  status document_status_enum DEFAULT 'UPLOADED',
  expiry_date DATE,
  verified_at TIMESTAMPTZ,
  created_on TIMESTAMPTZ DEFAULT now()
);



CREATE TABLE fleet_owner_document (
  document_id BIGSERIAL PRIMARY KEY,
  owner_id BIGINT REFERENCES fleet_owner_profile,
  document_type document_type_enum,
  file_url TEXT NOT NULL,
  status document_status_enum,
  verified_at TIMESTAMP,
  created_on TIMESTAMP DEFAULT now()
);

/* =========================================================
   VEHICLES
========================================================= */

CREATE TABLE bike (
  bike_id BIGSERIAL PRIMARY KEY,
  tenant_id BIGINT REFERENCES tenant,
  driver_id BIGINT UNIQUE REFERENCES driver_profile,
  registration_no TEXT UNIQUE NOT NULL,
  status vehicle_status_enum DEFAULT 'PENDING',
  created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE auto (
  auto_id BIGSERIAL PRIMARY KEY,
  tenant_id BIGINT REFERENCES tenant,
  driver_id BIGINT UNIQUE REFERENCES driver_profile,
  registration_no TEXT UNIQUE NOT NULL,
  status vehicle_status_enum DEFAULT 'PENDING',
  created_on TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE car (
  car_id BIGSERIAL PRIMARY KEY,
  tenant_id BIGINT REFERENCES tenant,
  owner_id BIGINT REFERENCES fleet_owner_profile,
  registration_no TEXT UNIQUE NOT NULL,
  status vehicle_status_enum DEFAULT 'PENDING',
  created_on TIMESTAMPTZ DEFAULT now()
);


/* =========================================================
   CAR DRIVER ASSIGNMENT (SHIFTS)
========================================================= */

CREATE TABLE car_driver_assignment (
  assignment_id BIGSERIAL PRIMARY KEY,
  car_id BIGINT REFERENCES car,
  driver_id BIGINT REFERENCES driver_profile,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ,
  created_on TIMESTAMPTZ DEFAULT now()
);


/* =========================================================
   DRIVER LOCATION
========================================================= */

CREATE TABLE driver_live_location (
  driver_id BIGINT PRIMARY KEY REFERENCES driver_profile,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  recorded_at TIMESTAMPTZ DEFAULT now()
);


/* =========================================================
   PRICING
========================================================= */

CREATE TABLE pricing_time_window (
  time_window_id BIGSERIAL PRIMARY KEY,
  name TEXT,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL
);

CREATE TABLE tenant_vehicle_pricing (
  pricing_id BIGSERIAL PRIMARY KEY,
  tenant_id BIGINT REFERENCES tenant,
  city_id BIGINT REFERENCES city,
  vehicle_type driver_type_enum,
  time_window_id BIGINT REFERENCES pricing_time_window,
  base_fare NUMERIC,
  per_km_charge NUMERIC,
  minimum_fare NUMERIC,
  commission_percentage NUMERIC,
  created_on TIMESTAMPTZ DEFAULT now()
);


/* =========================================================
   TRIPS
========================================================= */

CREATE TABLE trip (
  trip_id BIGSERIAL PRIMARY KEY,
  tenant_id BIGINT REFERENCES tenant,
  city_id BIGINT REFERENCES city,
  rider_id BIGINT REFERENCES rider_profile,
  driver_id BIGINT REFERENCES driver_profile,
  vehicle_type driver_type_enum,
  pickup_latitude DOUBLE PRECISION,
  pickup_longitude DOUBLE PRECISION,
  drop_latitude DOUBLE PRECISION,
  drop_longitude DOUBLE PRECISION,
  distance_km NUMERIC,
  fare_amount NUMERIC,
  status trip_status_enum,
  requested_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);





/* =========================================================
   DISPATCH & MATCHING TELEMETRY
========================================================= */

CREATE TABLE trip_dispatch_attempt (
  attempt_id BIGSERIAL PRIMARY KEY,
  trip_id BIGINT REFERENCES trip,
  tenant_id BIGINT REFERENCES tenant,
  attempt_number INT,
  started_at TIMESTAMPTZ DEFAULT now(),
  ended_at TIMESTAMPTZ,
  search_radius_km NUMERIC,
  candidate_driver_count INT,
  result TEXT
);

CREATE TABLE trip_driver_candidate (
  candidate_id BIGSERIAL PRIMARY KEY,
  attempt_id BIGINT REFERENCES trip_dispatch_attempt,
  driver_id BIGINT REFERENCES driver_profile,
  distance_km NUMERIC,
  eta_seconds INT,
  eligibility_status TEXT,
  evaluated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE trip_driver_offer (
  offer_id BIGSERIAL PRIMARY KEY,
  attempt_id BIGINT REFERENCES trip_dispatch_attempt,
  driver_id BIGINT REFERENCES driver_profile,
  offered_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ,
  response TEXT,
  responded_at TIMESTAMPTZ
);

CREATE TABLE trip_cancellation (
  trip_id BIGINT PRIMARY KEY REFERENCES trip,
  cancelled_by trip_cancelled_by_enum,
  reason TEXT,
  cancelled_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE trip_audit_log (
  audit_id BIGSERIAL PRIMARY KEY,
  trip_id BIGINT REFERENCES trip,
  old_status trip_status_enum,
  new_status trip_status_enum,
  changed_by_user_id BIGINT REFERENCES app_user,
  changed_at TIMESTAMPTZ DEFAULT now()
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
