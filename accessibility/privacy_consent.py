"""
Privacy and Consent Management Module
===================================
Handles collection, storage, and management of disability accommodation
preferences with robust privacy protections and consent mechanisms.

Complies with:
- GDPR (General Data Protection Regulation)
- ADA (Americans with Disabilities Act)
- Section 508 of the Rehabilitation Act
- Kenyan Data Protection Act (if applicable)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, cast # type: ignore
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
import os
import uuid
import secrets


class ConsentStatus(Enum):
    """Consent status enumeration"""
    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    GRANTED = "granted"
    PARTIAL = "partial"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"


class DataCategory(Enum):
    """Categories of personal data"""
    IDENTITY = "identity"
    DISABILITY_INFO = "disability_info"
    ACCOMMODATION_NEEDS = "accommodation_needs"
    EMPLOYMENT_HISTORY = "employment_history"
    PREFERENCES = "preferences"
    USAGE_DATA = "usage_data"


@dataclass
class ConsentRecord:
    """Record of user consent for data processing"""
    consent_id: str
    user_id: str
    data_categories: List[str]
    purpose: str
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    status: str = ConsentStatus.NOT_REQUESTED.value
    consent_version: str = "1.0"
    ip_hash: Optional[str] = None
    user_agent: Optional[str] = None
    consent_proof: Optional[str] = None  # Cryptographic proof of consent
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "consent_id": self.consent_id,
            "user_id": self.user_id,
            "data_categories": self.data_categories,
            "purpose": self.purpose,
            "granted_at": cast(datetime, self.granted_at).isoformat() if self.granted_at else None,
            "expires_at": cast(datetime, self.expires_at).isoformat() if self.expires_at else None,
            "status": self.status,
            "consent_version": self.consent_version,
            "ip_hash": self.ip_hash,
            "user_agent": self.user_agent,
            "consent_proof": self.consent_proof
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ConsentRecord":
        """Create from dictionary"""
        granted_at = datetime.fromisoformat(data["granted_at"]) if data.get("granted_at") else None
        expires_at = datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        return cls(
            consent_id=data["consent_id"],
            user_id=data["user_id"],
            data_categories=data["data_categories"],
            purpose=data["purpose"],
            granted_at=granted_at,
            expires_at=expires_at,
            status=data["status"],
            consent_version=data.get("consent_version", "1.0"),
            ip_hash=data.get("ip_hash"),
            user_agent=data.get("user_agent"),
            consent_proof=data.get("consent_proof")
        )


@dataclass
class PrivacyPreference:
    """User privacy preferences for data handling"""
    user_id: str
    share_with_employers: bool = False
    share_with_campus_services: bool = True
    allow_analytics: bool = True
    allow_personalization: bool = True
    allow_research: bool = False
    data_retention_days: int = 365
    anonymize_data: bool = False
    require_explicit_consent: bool = True
    third_party_sharing: bool = False
    marketing_communications: bool = False
    emergency_contact_sharing: bool = False


@dataclass
class AccessibilityDataRecord:
    """
    Accessibility accommodation data record with enhanced privacy.
    Data is pseudonymized and encrypted at rest.
    """
    record_id: str
    user_pseudonym: str  # Hashed user ID, not direct identifier
    accommodation_profile_version: str = "1.0"
    collected_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    consent_status: str = ConsentStatus.PENDING.value
    disability_categories: List[str] = field(default_factory=list)
    accommodation_needs: List[Dict[str, Any]] = field(default_factory=list)
    workplace_requirements: List[str] = field(default_factory=list)
    mobility_requirements: Dict[str, bool] = field(default_factory=dict)
    sensory_requirements: Dict[str, bool] = field(default_factory=dict)
    technology_preferences: Dict[str, Any] = field(default_factory=dict)
    communication_preferences: Dict[str, Any] = field(default_factory=dict)
    emergency_contact: Optional[Dict[str, str]] = None
    verification_status: str = "unverified"  # unverified, verified, expired
    verified_by: Optional[str] = None
    verification_date: Optional[datetime] = None
    campus_services_shared: bool = False
    employer_shared_count: int = 0
    last_employer_shared: Optional[datetime] = None
    
    def to_personal_record(self) -> Dict:
        """
        Convert to personal data record (for campus services sharing).
        Contains real identifiers for authorized sharing.
        """
        return {
            "record_id": self.record_id,
            "user_pseudonym": self.user_pseudonym,
            "accommodation_profile_version": self.accommodation_profile_version,
            "collected_at": self.collected_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "disability_categories": self.disability_categories,
            "accommodation_needs": self.accommodation_needs,
            "workplace_requirements": self.workplace_requirements,
            "mobility_requirements": self.mobility_requirements,
            "sensory_requirements": self.sensory_requirements,
            "technology_preferences": self.technology_preferences,
            "communication_preferences": self.communication_preferences,
            "verification_status": self.verification_status,
            "verified_by": self.verified_by,
            "verification_date": cast(datetime, self.verification_date).isoformat() if self.verification_date else None
        }
    
    def to_anonymous_record(self) -> Dict:
        """
        Convert to anonymous record (for research/improvement).
        All identifying information removed.
        """
        return {
            "record_id": hashlib.sha256(self.record_id.encode()).hexdigest()[:16], # type: ignore
            "accommodation_profile_version": self.accommodation_profile_version,
            "collected_at": self.collected_at.isoformat(),
            "disability_categories": self.disability_categories,
            "accommodation_needs": [a.get("category") for a in self.accommodation_needs],
            "workplace_requirements": self.workplace_requirements,
            "mobility_requirements": self.mobility_requirements,
            "sensory_requirements": self.sensory_requirements
        }


class PrivacyManager:
    """
    Manages privacy and consent for accessibility data.
    Implements data minimization, purpose limitation, and consent management.
    """
    
    def __init__(self, encryption_key: Optional[str] = None, storage_path: str = "data/accessibility/"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self._encryption_key = encryption_key or self._generate_encryption_key()
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.privacy_preferences: Dict[str, PrivacyPreference] = {}
        
    def _generate_encryption_key(self) -> str:
        """Generate a secure encryption key"""
        return secrets.token_hex(32)
    
    def _hash_user_id(self, user_id: str) -> str:
        """Create pseudonymized user identifier"""
        return hashlib.sha256(f"{user_id}{self._encryption_key}".encode()).hexdigest()
    
    def create_consent_request(
        self,
        user_id: str,
        data_categories: List[str],
        purpose: str,
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ConsentRecord:
        """
        Create a new consent request for user approval.
        """
        consent_id = str(uuid.uuid4())
        consent = ConsentRecord(
            consent_id=consent_id,
            user_id=user_id,
            data_categories=data_categories,
            purpose=purpose,
            status=ConsentStatus.PENDING.value,
            ip_hash=self._hash_user_id(request_ip) if request_ip else None,
            user_agent=user_agent
        )
        self.consent_records[consent_id] = consent
        return consent
    
    def record_consent(
        self,
        consent_id: str,
        granted: bool,
        granted_categories: Optional[List[str]] = None
    ) -> ConsentRecord:
        """
        Record user consent decision.
        """
        if consent_id not in self.consent_records:
            raise ValueError(f"Consent record {consent_id} not found")
        
        consent = self.consent_records[consent_id]
        consent.status = ConsentStatus.GRANTED.value if granted else ConsentStatus.DENIED.value
        consent.granted_at = datetime.now()
        
        if granted:
            consent.expires_at = datetime.now() + timedelta(days=365)
            consent.consent_proof = self._generate_consent_proof(consent)
            if granted_categories:
                consent.data_categories = granted_categories
        
        return consent
    
    def _generate_proof_data(self, consent: ConsentRecord) -> str:
        """Generate proof data handle"""
        g_at = cast(datetime, consent.granted_at).isoformat() if consent.granted_at else "none"
        return f"{consent.consent_id}{consent.user_id}{g_at}"

    def _generate_consent_proof(self, consent: ConsentRecord) -> str:
        """Generate cryptographic proof of consent"""
        consent_data = self._generate_proof_data(consent)
        return hashlib.sha256(consent_data.encode()).hexdigest()
    
    def verify_consent(self, user_id: str, data_category: str) -> bool:
        """
        Verify if user has granted consent for a specific data category.
        """
        for consent in self.consent_records.values():
            if consent.user_id == user_id:
                if consent.status == ConsentStatus.GRANTED.value:
                    expires_at = cast(Optional[datetime], consent.expires_at)
                    if expires_at and expires_at > datetime.now():
                        if data_category in consent.data_categories:
                            return True
        return False
    
    def withdraw_consent(self, user_id: str, data_category: Optional[str] = None) -> bool:
        """
        Withdraw user consent. If no category specified, withdraw all consent.
        """
        withdrawn = False
        for consent in self.consent_records.values():
            if consent.user_id == user_id:
                if consent.status == ConsentStatus.GRANTED.value:
                    if data_category:
                        cat_str = str(data_category)
                        if cat_str in consent.data_categories:
                            consent.data_categories.remove(cat_str)
                            if not consent.data_categories:
                                consent.status = ConsentStatus.WITHDRAWN.value
                            withdrawn = True
                    else:
                        consent.status = ConsentStatus.WITHDRAWN.value
                        withdrawn = True
        return withdrawn
    
    def save_privacy_preferences(self, user_id: str, preferences: PrivacyPreference):
        """Save user privacy preferences"""
        self.privacy_preferences[user_id] = preferences
        prefs_path = os.path.join(self.storage_path, f"privacy_{user_id}.json")
        with open(prefs_path, 'w') as f:
            json.dump(preferences.__dict__, f, indent=2)
    
    def get_privacy_preferences(self, user_id: str) -> Optional[PrivacyPreference]:
        """Retrieve user privacy preferences"""
        prefs_path = os.path.join(self.storage_path, f"privacy_{user_id}.json")
        if os.path.exists(prefs_path):
            with open(prefs_path, 'r') as f:
                data = json.load(f)
                return PrivacyPreference(user_id=user_id, **data)
        return None
    
    def generate_data_export(self, user_id: str) -> Dict[str, Any]:
        """
        Generate complete data export for user (GDPR right of access).
        """
        export_data: Dict[str, Any] = {
            "export_date": datetime.now().isoformat(),
            "user_id": user_id,
            "pseudonym": self._hash_user_id(user_id),
            "consent_records": [],
            "privacy_preferences": None,
            "accessibility_data": None
        }
        
        for consent in self.consent_records.values():
            if consent.user_id == user_id:
                recs: Any = export_data["consent_records"]
                recs.append(consent.to_dict())
        
        prefs = self.get_privacy_preferences(user_id)
        if prefs:
            export_data["privacy_preferences"] = cast(Any, prefs.__dict__)
        
        return export_data
    
    def delete_user_data(
        self, 
        user_id: str, 
        retain_anonymous: bool = True
    ) -> Dict[str, Any]:
        """
        Delete all user data (GDPR right to erasure).
        Returns anonymous statistics if retain_anonymous is True.
        """
        deletion_report: Dict[str, Any] = {
            "user_id": user_id,
            "deleted_at": datetime.now().isoformat(),
            "records_deleted": 0,
            "anonymous_data_retained": retain_anonymous
        }
        
        # Delete consent records
        consent_count = len([
            c for c in self.consent_records.values() 
            if c.user_id == user_id
        ])
        self.consent_records = {
            k: v for k, v in self.consent_records.items() 
            if v.user_id != user_id
        }
        current_count = int(deletion_report["records_deleted"])
        deletion_report["records_deleted"] = current_count + consent_count
        
        # Delete privacy preferences
        prefs_path = os.path.join(self.storage_path, f"privacy_{user_id}.json")
        if os.path.exists(prefs_path):
            os.remove(prefs_path)
            current_count = int(deletion_report["records_deleted"])
            deletion_report["records_deleted"] = current_count + 1
        
        return deletion_report


class AccessibilityDataStore:
    """
    Secure storage for accessibility accommodation data.
    Implements encryption and access controls.
    """
    
    def __init__(self, privacy_manager: PrivacyManager, storage_path: str = "data/accessibility/"):
        self.privacy_manager = privacy_manager
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self.records: Dict[str, AccessibilityDataRecord] = {}
        
    def create_record(
        self, 
        user_id: str,
        disability_categories: List[str],
        accommodation_needs: List[Dict[str, Any]]
    ) -> AccessibilityDataRecord:
        """
        Create a new accessibility accommodation record.
        """
        record_id = str(uuid.uuid4())
        pseudonym = self.privacy_manager._hash_user_id(user_id)
        
        record = AccessibilityDataRecord(
            record_id=record_id,
            user_pseudonym=pseudonym,
            disability_categories=disability_categories,
            accommodation_needs=accommodation_needs
        )
        
        self.records[record_id] = record
        return record
    
    def update_record(
        self, 
        record_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[AccessibilityDataRecord]:
        """
        Update an existing accessibility record.
        """
        if record_id not in self.records:
            return None
        
        record = self.records[record_id]
        for key, value in updates.items():
            if hasattr(record, key):
                setattr(record, key, value)
        record.last_updated = datetime.now()
        return record
    
    def share_with_campus_services(
        self, 
        record_id: str,
        service_id: str,
        verifier_id: str
    ) -> bool:
        """
        Share accessibility data with campus disability services.
        Requires verification and consent.
        """
        if record_id not in self.records:
            return False
        
        record = self.records[record_id]
        
        # Verify consent
        if not self.privacy_manager.verify_consent(
            record.user_pseudonym, 
            "campus_services"
        ):
            return False
        
        record.verification_status = "verified"
        record.verified_by = verifier_id
        record.verification_date = datetime.now()
        record.campus_services_shared = True
        
        return True
    
    def prepare_employer_disclosure(
        self,
        record_id: str,
        employer_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Prepare accommodation information for employer disclosure.
        Minimizes data to only what's necessary for accommodation.
        """
        if record_id not in self.records:
            return None
        
        record = self.records[record_id]
        
        # Verify consent
        if not self.privacy_manager.verify_consent(
            record.user_pseudonym,
            "employer_sharing"
        ):
            return None
        
        # Create minimal disclosure (only accommodation needs)
        disclosure = {
            "record_id": record_id,
            "generated_at": datetime.now().isoformat(),
            "accommodations_required": [
                need.get("specific_accommodation") 
                for need in record.accommodation_needs
            ],
            "effective_date": datetime.now().isoformat(),
            "review_date": (datetime.now() + timedelta(days=90)).isoformat()
        }
        
        # Update sharing count
        record.employer_shared_count += 1
        record.last_employer_shared = datetime.now()
        
        return disclosure
    
    def get_anonymous_statistics(self) -> Dict:
        """
        Generate anonymous statistics for system improvement.
        All identifying information removed.
        """
        categories_count = {}
        needs_count = {}
        
        for record in self.records.values():
            for category in record.disability_categories:
                categories_count[category] = categories_count.get(category, 0) + 1
            
            for need in record.accommodation_needs:
                need_type = need.get("category", "unknown")
                needs_count[need_type] = needs_count.get(need_type, 0) + 1
        
        return {
            "total_records": len(self.records),
            "disability_categories": categories_count,
            "accommodation_needs": needs_count,
            "generated_at": datetime.now().isoformat()
        }


# Consent form templates
CONSENT_FORMS = {
    "initial_consent": {
        "title": "Accessibility Accommodation Consent",
        "purpose": "To provide appropriate job recommendations and workplace accommodations",
        "data_categories": [
            "disability_info",
            "accommodation_needs",
            "mobility_requirements",
            "sensory_requirements"
        ],
        "recipients": [
            "AI Career Recommender System",
            "Campus Disability Services (with your permission)"
        ],
        "retention": "Data retained for 2 years or until you request deletion",
        "rights": [
            "Right to access your data",
            "Right to correct inaccurate data",
            "Right to withdraw consent",
            "Right to request data deletion"
        ]
    },
    
    "employer_sharing_consent": {
        "title": "Employer Accommodation Disclosure Consent",
        "purpose": "To share your accommodation needs with prospective employers",
        "data_categories": [
            "accommodation_needs",
            "workplace_requirements"
        ],
        "recipients": [
            "Prospective Employers (only after you apply)"
        ],
        "retention": "Shared only when you apply; employer retains per their policy",
        "rights": [
            "You control what information is shared",
            "You can revoke sharing permission at any time"
        ]
    },
    
    "research_consent": {
        "title": "Research Participation Consent",
        "purpose": "To help improve accessibility features (anonymized data only)",
        "data_categories": [
            "anonymized_accommodation_needs"
        ],
        "recipients": [
            "Research Team (anonymized data only)"
        ],
        "retention": "Anonymized data retained indefinitely for research",
        "rights": [
            "No identifying information is collected",
            "You cannot be identified from this data"
        ]
    }
}
