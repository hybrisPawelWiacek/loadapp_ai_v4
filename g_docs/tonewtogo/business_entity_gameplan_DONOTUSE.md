# Business Entity Support Implementation Gameplan
Version: 1.0
Last Updated: January 2025

This document outlines the implementation plan for enhancing Business Entity support in LoadApp.AI, focusing on data model improvements, API endpoints, and integration with existing services.

## Implementation Plan

### 1. Domain Layer Updates

#### 1.1 Enhance BusinessEntity Domain Model
File: `backend/domain/entities/business.py`
```python
class BusinessEntity(BaseModel):
    id: UUID
    name: str
    address: str
    contact_info: Dict[str, str]
    business_type: str
    certifications: List[str]
    operating_countries: List[str]
    cost_overheads: Dict[str, Decimal]
    default_cost_settings: Optional[Dict[str, Any]]
    is_active: bool = True
```

#### 1.2 Business Entity Validation Rules
- Minimum Requirements:
  * At least one certification
  * At least one operating country
  * Valid business types: "carrier", "shipper", "logistics_provider"
  * Contact info must include "email"
  * All cost overhead values must be positive decimals

### 2. Infrastructure Layer Updates

#### 2.1 Update Business Entity Model
File: `backend/infrastructure/models/business_models.py`
```python
class BusinessEntityModel(Base):
    __tablename__ = "business_entities"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    contact_info = Column(JSON, nullable=False)
    business_type = Column(String(50), nullable=False)
    certifications = Column(JSON, nullable=False)
    operating_countries = Column(JSON, nullable=False)
    cost_overheads = Column(JSON, nullable=False)
    default_cost_settings = Column(JSON)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### 2.2 Database Migration
File: `migrations/versions/XXXXXX_enhance_business_entities.py`
- Add new columns with appropriate data types
- Create indexes for frequently queried fields
- Set default values for new columns
- Ensure SQLite compatibility

### 3. API Layer Updates

#### 3.1 Business Entity Routes
File: `backend/api/routes/business_routes.py`

New Endpoints:
1. Create Business Entity
   ```
   POST /api/business-entity
   - Request: Business entity details
   - Response: Created business entity
   ```

2. Get Business Entity
   ```
   GET /api/business-entity/{id}
   - Response: Business entity details
   ```

3. List Business Entities
   ```
   GET /api/business-entity
   - Query Parameters: 
     * page (default: 1)
     * size (default: 10)
     * is_active (optional)
     * business_type (optional)
   - Response: Paginated list of business entities
   ```

4. Update Business Entity
   ```
   PUT /api/business-entity/{id}
   - Request: Updated business entity details
   - Response: Updated business entity
   ```

5. Delete Business Entity
   ```
   DELETE /api/business-entity/{id}
   - Response: 204 No Content
   ```

6. Update Default Cost Settings
   ```
   PATCH /api/business-entity/{id}/cost-settings
   - Request: Default cost settings
   - Response: Updated business entity
   ```

### 4. Service Layer Updates

#### 4.1 Enhanced Business Service
File: `backend/domain/services/business_service.py`

```python
class BusinessService:
    def create_business_entity(self, data: Dict) -> BusinessEntity:
        """Create new business entity with validation."""
        
    def update_business_entity(self, id: UUID, data: Dict) -> BusinessEntity:
        """Update existing business entity."""
        
    def get_business_entity(self, id: UUID) -> Optional[BusinessEntity]:
        """Retrieve business entity by ID."""
        
    def list_business_entities(self, filters: Dict) -> List[BusinessEntity]:
        """List business entities with filtering."""
        
    def deactivate_business_entity(self, id: UUID) -> None:
        """Soft delete business entity."""
        
    def update_default_cost_settings(self, id: UUID, settings: Dict) -> BusinessEntity:
        """Update default cost settings for business entity."""
        
    def validate_business_entity(self, entity: BusinessEntity) -> bool:
        """Validate business entity data."""
```

### 5. Testing Plan

#### 5.1 Unit Tests
File: `tests/backend/domain/entities/test_business.py`

Test Cases:
- Business entity validation rules
- Default cost settings validation
- Business type validation
- Contact info validation
- Cost overheads validation

#### 5.2 Repository Tests
File: `tests/backend/infrastructure/repositories/test_business_repository.py`

Test Cases:
- CRUD operations
- JSON field serialization/deserialization
- Soft delete functionality
- Default cost settings updates
- Query filters

#### 5.3 API Tests
File: `tests/backend/api/routes/test_business_routes.py`

Test Cases:
- All API endpoints
- Validation error responses
- Business logic enforcement
- Edge cases and error handling

### 6. Integration Points

#### 6.1 Cost Service Integration
- Use business entity's default cost settings when creating new cost settings
- Validate rates against business entity's certifications
- Apply business-specific cost overheads

#### 6.2 Transport Service Integration
- Validate transport types against business entity's certifications
- Check operating countries against route countries
- Apply business-specific transport rules

#### 6.3 Offer Service Integration
- Include business entity details in offer generation
- Use business-specific margins if defined
- Apply business-specific pricing rules

### 7. Migration Strategy

#### 7.1 Database Migration Steps
1. Create new columns with nullable constraints
2. Add data migration script for existing records
3. Add required constraints after data migration
4. Create necessary indexes

#### 7.2 Code Deployment Steps
1. Deploy database changes
2. Deploy code changes with backward compatibility
3. Run data migration scripts
4. Enable new features
5. Monitor for any issues

### 8. Documentation Updates

#### 8.1 API Documentation
- Document new endpoints with request/response examples
- Document validation rules
- Add error response examples
- Update OpenAPI/Swagger specifications

#### 8.2 System Architecture
- Update architecture diagrams
- Document new relationships
- Add migration notes
- Update deployment guide

## Implementation Notes

### Validation Rules
1. Business Entity:
   - Name: 3-100 characters
   - Address: Required, max 255 characters
   - Contact Info: Must include email
   - Business Type: Must be one of allowed values
   - Certifications: At least one required
   - Operating Countries: At least one required
   - Cost Overheads: All values must be positive

### SQLite Compatibility
1. JSON Fields:
   - Use TEXT columns with JSON validation
   - Implement proper serialization/deserialization
   - Handle JSON parsing errors gracefully

2. DateTime Fields:
   - Store in UTC
   - Use TEXT type for SQLite
   - Ensure proper timezone handling

### Error Handling
1. API Responses:
   - 400: Invalid input data
   - 404: Entity not found
   - 409: Conflict (e.g., duplicate name)
   - 500: Internal server error

2. Validation Errors:
   - Clear error messages
   - Field-level validation details
   - Business rule violation explanations

## Progress Tracking

- [ ] Domain Layer Updates
  - [ ] Enhanced BusinessEntity model
  - [ ] Validation rules implementation

- [ ] Infrastructure Layer Updates
  - [ ] Updated database model
  - [ ] Migration script
  - [ ] Repository implementation

- [ ] API Layer Updates
  - [ ] New endpoints implementation
  - [ ] Request/response validation
  - [ ] Error handling

- [ ] Service Layer Updates
  - [ ] Enhanced business service
  - [ ] Integration with other services

- [ ] Testing
  - [ ] Unit tests
  - [ ] Repository tests
  - [ ] API tests
  - [ ] Integration tests

- [ ] Documentation
  - [ ] API documentation
  - [ ] Architecture updates
  - [ ] Migration guide

## Implementation Timeline

1. Week 1:
   - Domain and infrastructure layer updates
   - Basic CRUD operations

2. Week 2:
   - API endpoints implementation
   - Service layer enhancements

3. Week 3:
   - Testing implementation
   - Documentation updates

4. Week 4:
   - Integration testing
   - Bug fixes and refinements
   - Final documentation updates

## Conclusion

This implementation plan provides a structured approach to enhancing Business Entity support in LoadApp.AI. The plan ensures backward compatibility while adding new features and maintaining data integrity. Regular testing and documentation updates will help maintain code quality and system reliability. 