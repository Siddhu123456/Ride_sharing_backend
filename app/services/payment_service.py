from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.trip import Trip
from app.models.vehicle import Vehicle
from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.models.fare_config import FareConfig
from app.schemas.enums import WalletOwnerEnum, WalletTxnDirectionEnum, WalletTxnReasonEnum

def get_or_create_wallet(db, owner_type, owner_id):
    wallet = db.query(Wallet).filter_by(
        owner_type=owner_type,
        owner_id=owner_id
    ).first()

    if not wallet:
        wallet = Wallet(
            owner_type=owner_type,
            owner_id=owner_id,
            balance=Decimal("0.00")
        )
        db.add(wallet)
        db.flush()

    return wallet


def create_payment_for_trip(db: Session, trip: Trip):

    #get fleet from the vehicle
    vehicle = db.query(Vehicle).filter(
        Vehicle.vehicle_id == trip.vehicle_id
    ).first()

    if not vehicle or not vehicle.fleet_id:
        raise ValueError("Fleet not found for trip vehicle")

    fleet_id = vehicle.fleet_id

    #get platform commission % from fare config
    fare_config = db.query(FareConfig).filter(
        FareConfig.city_id == trip.city_id,
        FareConfig.vehicle_category == trip.vehicle_category,
        FareConfig.is_active.is_(True)
    ).first()

    if not fare_config:
        raise ValueError("Fare config not found")

    commission_pct = Decimal(fare_config.platform_commission_percent)
    total_fare = Decimal(trip.fare_amount)

    platform_fee = (total_fare * commission_pct) / Decimal(100)
    fleet_earning = total_fare - platform_fee

    # Store snapshot of fees on trip
    trip.platform_fee = platform_fee
    trip.fleet_owner_earning = fleet_earning

    # Get or create wallets
    tenant_wallet = get_or_create_wallet(
        db, WalletOwnerEnum.TENANT, trip.tenant_id
    )

    fleet_wallet = get_or_create_wallet(
        db, WalletOwnerEnum.FLEET_OWNER, fleet_id
    )

    # Credit wallets
    tenant_wallet.balance += platform_fee
    fleet_wallet.balance += fleet_earning

    # Ledger entries
    db.add_all([
        # Tenant commission (credit)
        WalletTransaction(
            wallet_id=tenant_wallet.wallet_id,
            trip_id=trip.trip_id,
            amount=platform_fee,
            direction=WalletTxnDirectionEnum.CREDIT,
            reason=WalletTxnReasonEnum.COMMISSION_LOCKED
        ),

        # Fleet earning (credit)
        WalletTransaction(
            wallet_id=fleet_wallet.wallet_id,
            trip_id=trip.trip_id,
            amount=fleet_earning,
            direction=WalletTxnDirectionEnum.CREDIT,
            reason=WalletTxnReasonEnum.TRIP_EARNING
        )
    ])


    vehicle = db.query(Vehicle).filter(
        Vehicle.vehicle_id == trip.vehicle_id
    ).first()

    if not vehicle or not vehicle.fleet_id:
        raise ValueError("Fleet not found for trip vehicle")

    fleet_id = vehicle.fleet_id
    
    # Get commission %
    fare_config = db.query(FareConfig).filter(
        FareConfig.city_id == trip.city_id,
        FareConfig.vehicle_category == trip.vehicle_category,
        FareConfig.is_active.is_(True)
    ).first()

    commission_pct = fare_config.platform_commission_percent
    total_fare = Decimal(trip.fare_amount)

    platform_fee = (total_fare * commission_pct) / Decimal(100)
    fleet_owner_earning = total_fare - platform_fee

    # Store snapshot on trip
    trip.platform_fee = platform_fee
    trip.fleet_owner_earning = fleet_owner_earning

    # Get / create wallets
    tenant_wallet = get_or_create_wallet(
        db, WalletOwnerEnum.TENANT, trip.tenant_id
    )

    fleet_wallet = get_or_create_wallet(
        db, WalletOwnerEnum.FLEET_OWNER, fleet_id
    )

    # Credit wallets
    tenant_wallet.balance += platform_fee
    fleet_wallet.balance += fleet_owner_earning

    #  Ledger entries
    db.add_all([
        WalletTransaction(
            wallet_id=tenant_wallet.wallet_id,
            trip_id=trip.trip_id,
            amount=platform_fee,
            transaction_type=WalletTxnTypeEnum.PLATFORM_COMMISSION
        ),
        WalletTransaction(
            wallet_id=fleet_wallet.wallet_id,
            trip_id=trip.trip_id,
            amount=fleet_owner_earning,
            transaction_type=WalletTxnTypeEnum.TRIP_EARNING
        )
    ])



