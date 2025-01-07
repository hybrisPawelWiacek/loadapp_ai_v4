"""Tests for business service."""
import pytest
from uuid import uuid4
from decimal import Decimal
from unittest.mock import Mock

from backend.domain.entities.business import BusinessEntity
from backend.domain.services.business_service import BusinessService


@pytest.fixture
def mock_business_repo():
    """Create mock business repository."""
    return Mock()


@pytest.fixture
def business_service(mock_business_repo):
    """Create business service with mock repository."""
    return BusinessService(mock_business_repo)


@pytest.fixture
def sample_business():
    """Create sample business entity."""
    return BusinessEntity(
        id=uuid4(),
        name="Test Transport Company",
        address="123 Test Street",
        contact_info={"email": "test@example.com"},
        business_type="carrier",
        certifications=["ISO9001"],
        operating_countries=["DE", "PL"],
        cost_overheads={"admin": Decimal("100.00")}
    )


def test_list_active_businesses(business_service, mock_business_repo, sample_business):
    """Test listing active business entities."""
    # Arrange
    mock_business_repo.find_active.return_value = [sample_business]
    
    # Act
    result = business_service.list_active_businesses()
    
    # Assert
    assert len(result) == 1
    assert result[0].id == sample_business.id
    mock_business_repo.find_active.assert_called_once()


def test_validate_certifications_success(business_service, mock_business_repo, sample_business):
    """Test successful certification validation."""
    # Arrange
    mock_business_repo.find_by_id.return_value = sample_business
    
    # Act
    result = business_service.validate_certifications("general", sample_business.id)
    
    # Assert
    assert result is True
    mock_business_repo.find_by_id.assert_called_once_with(sample_business.id)


def test_validate_certifications_business_not_found(business_service, mock_business_repo):
    """Test certification validation with non-existent business."""
    # Arrange
    mock_business_repo.find_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(ValueError, match="Business entity not found"):
        business_service.validate_certifications("general", uuid4())


def test_update_business_overheads_success(business_service, mock_business_repo, sample_business):
    """Test successful update of business overhead costs."""
    # Arrange
    mock_business_repo.find_by_id.return_value = sample_business
    mock_business_repo.save.return_value = sample_business
    
    new_overheads = {
        "administration": Decimal("150.00"),
        "insurance": Decimal("250.00"),
        "facilities": Decimal("200.00"),
        "other": Decimal("50.00")
    }
    
    # Act
    result = business_service.update_business_overheads(sample_business.id, new_overheads)
    
    # Assert
    assert result is not None
    assert result.cost_overheads == new_overheads
    mock_business_repo.find_by_id.assert_called_once_with(sample_business.id)
    mock_business_repo.save.assert_called_once()


def test_update_business_overheads_not_found(business_service, mock_business_repo):
    """Test updating overheads for non-existent business."""
    # Arrange
    mock_business_repo.find_by_id.return_value = None
    
    # Act
    result = business_service.update_business_overheads(
        uuid4(),
        {"admin": Decimal("100.00")}
    )
    
    # Assert
    assert result is None
    mock_business_repo.save.assert_not_called()


def test_update_business_overheads_negative_values(business_service, mock_business_repo, sample_business):
    """Test updating business overheads with negative values."""
    # Arrange
    mock_business_repo.find_by_id.return_value = sample_business
    
    negative_overheads = {
        "administration": Decimal("-150.00"),
        "insurance": Decimal("250.00")
    }
    
    # Act & Assert
    with pytest.raises(ValueError, match="Overhead costs cannot be negative"):
        business_service.update_business_overheads(sample_business.id, negative_overheads)
    
    mock_business_repo.save.assert_not_called() 