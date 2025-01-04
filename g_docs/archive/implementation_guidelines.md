# Implementation Guidelines for New Functionality

## 1. Analysis Phase (MANDATORY)
1. First examine the existing codebase:
   - Use `list_dir` to understand project structure
   - Use `grep_search` to find related existing code
   - Use `codebase_search` for semantic understanding
   - Read key files completely before making changes

2. Document findings:
   - Existing models and their relationships
   - Naming conventions in use
   - Design patterns being followed
   - Similar functionality that exists

## 2. Planning Phase (MANDATORY)
1. Create a clear plan:
   - List all files that need to be modified
   - List new files that need to be created
   - Identify potential impacts on existing code
   - Document dependencies and relationships

2. Validate approach:
   - Ensure new code follows existing patterns
   - Verify naming matches conventions
   - Check for duplicate functionality
   - Consider test impact

## 3. Implementation Rules
1. NO rewriting existing code unless explicitly requested
2. NO renaming existing models/classes/functions
3. NO changing existing patterns or conventions
4. NO modifying working tests without clear justification

## 4. Implementation Order
1. Start with minimal changes to existing files
2. Add new models that extend existing ones
3. Create new repositories following existing patterns
4. Add new routes building on existing structure
5. Create new tests matching existing style

## 5. Validation Steps
1. Run existing tests before any changes
2. Make changes incrementally
3. Run tests after each significant change
4. Document any test failures and their cause
5. Never proceed with broken tests

## 6. Code Review Checklist
1. Have I duplicated existing functionality?
2. Am I following established patterns?
3. Do my changes break existing tests?
4. Have I maintained naming consistency?
5. Are my changes minimal and necessary?

## 7. When in Doubt
1. Stop and ask for clarification
2. Review existing code again
3. Document concerns and alternatives
4. Wait for explicit approval before proceeding

## 8. Red Flags to Watch For
1. Finding yourself renaming existing models
2. Creating parallel functionality
3. Modifying multiple existing files
4. Breaking existing tests
5. Changing established patterns

## Example of Bad Practice
```
Problem: Asked to implement cost routes
Bad Approach:
- Jumped straight into implementation
- Created duplicate functionality
- Renamed existing models without justification
- Modified working code unnecessarily
- Created conflicts with existing tests

Correct Approach:
1. First examine existing codebase
2. Document current structure and patterns
3. Plan additions that build on existing code
4. Implement only what's needed
5. Maintain compatibility with existing code
```

## Using These Guidelines
1. Treat this as a mandatory checklist
2. Complete each phase before moving to the next
3. Document decisions and findings
4. When in doubt, refer back to these guidelines
5. Learn from mistakes and update guidelines as needed 