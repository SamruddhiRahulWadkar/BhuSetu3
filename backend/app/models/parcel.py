import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class ParcelRecord(Base):
    __tablename__ = "parcels"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ulpin = Column(String(14), unique=True, index=True, nullable=True)  # 14-digit Unique Land Parcel Identification Number
    survey_no = Column(String(50), nullable=False, index=True)
    khasra_no = Column(String(50), nullable=True, index=True)
    khata_no = Column(String(50), nullable=True, index=True)
    sub_division = Column(String(50), nullable=True)

    village = Column(String(100), nullable=False, index=True)
    tehsil = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)

    recorded_area = Column(Float, nullable=True)
    recorded_area_unit = Column(String(50), nullable=True)
    area_sqm = Column(Float, nullable=True)
    area_hectares = Column(Float, nullable=True)

    land_class = Column(String(100), default="agricultural")
    tenure_type = Column(String(100), default="freehold")  # freehold, tribal_restricted, govt_grant, inam

    # PostGIS-compatible GeoJSON geometry & centroid
    geometry_geojson = Column(Text, nullable=True)
    centroid_lat = Column(Float, nullable=True)
    centroid_lng = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner_shares = relationship("OwnerShare", back_populates="parcel", cascade="all, delete-orphan")
    mutation_events = relationship("MutationEvent", back_populates="parcel", cascade="all, delete-orphan")


class OwnerShare(Base):
    __tablename__ = "owner_shares"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parcel_id = Column(String(36), ForeignKey("parcels.id", ondelete="SET NULL"), nullable=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    owner_name = Column(String(255), nullable=False)
    owner_name_latin = Column(String(255), nullable=True)
    father_or_husband_name = Column(String(255), nullable=True)
    
    share_fraction = Column(Float, default=1.0)  # e.g. 0.5 for 1/2
    share_raw = Column(String(50), default="1/1")  # raw text extracted

    is_minor = Column(Boolean, default=False)
    guardian_name = Column(String(255), nullable=True)
    court_order_ref = Column(String(255), nullable=True)

    is_deceased = Column(Boolean, default=False)
    date_of_death = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    parcel = relationship("ParcelRecord", back_populates="owner_shares")
    document = relationship("Document", back_populates="owner_shares")


class MutationEvent(Base):
    __tablename__ = "mutation_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parcel_id = Column(String(36), ForeignKey("parcels.id", ondelete="SET NULL"), nullable=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    mutation_no = Column(String(50), nullable=False, index=True)
    mutation_date = Column(String(50), nullable=True)
    registration_date = Column(String(50), nullable=True)
    mutation_type = Column(String(50), default="sale")  # sale, inheritance, partition, gift, mortgage

    from_party = Column(String(255), nullable=True)
    to_party = Column(String(255), nullable=True)
    transferred_area = Column(Float, nullable=True)
    transferred_area_unit = Column(String(50), nullable=True)
    transferred_area_sqm = Column(Float, nullable=True)

    order_ref = Column(String(255), nullable=True)
    status = Column(String(50), default="certified")  # entered, verified, certified, disputed

    created_at = Column(DateTime, default=datetime.utcnow)

    parcel = relationship("ParcelRecord", back_populates="mutation_events")
    document = relationship("Document", back_populates="mutation_events")
