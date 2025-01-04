# Combined Rules & Guidelines

This document merges the essential contents of both ".cursorrules" and "g_docs/implementation_guidelines.md" into a single, comprehensive set of rules for this project. It is organized from the most general guidance to the most specific project instructions.

above is to be removed...
---

## 1. Introduction

These rules and guidelines have been compiled to ensure consistent, high-quality contributions to the LoadApp.AI project while adhering to Clean Architecture principles, domain-driven design, and best practices in testing and version control. Please review and follow these instructions carefully before making any changes or adding new functionality.

---

## 2. Environment & Dependencies

1. Always use a Python virtual environment (venv).  
   - Example:  
     - Create: python3.12 -m venv venv  
     - Activate: source venv/bin/activate  
     - Upgrade pip: pip install --upgrade pip  

2. Maintain an updated requirements.txt with explicit package versions.  
   - Pin exact versions (e.g., pydantic==2.5.2) to ensure consistent builds.

3. Use .env files for environment variables.  
   - Keep secrets out of version control.

4. Keep .gitignore updated to exclude environment files, secrets, etc.

5. Python Version Compatibility:  
   - Use Python 3.12 for best compatibility.  
   - Avoid Python 3.13 (many packages still lack support).

6. Package Version Control & Troubleshooting:  
   - Document version constraints in requirements.txt.  
   - Test upgrades in isolation; watch for conflicts.  
   - For installation issues, consider system dependencies (rust, C-extensions, etc.).

---

## 3. Version Control & Commits

1. After each successful feature development (confirmed by review or passing tests), remind the team (or yourself) to create a git commit.

2. Create atomic commits for each completed/approved feature.

3. Use conventional commit messages:
   - feat: new features  
   - fix: bug fixes  
   - docs: documentation changes  
   - refactor: code restructuring  
   - Include relevant ticket/issue numbers in commit messages.

4. Provide a short summary of significant changes in the commit message.

5. For pushing changes to the remote repository:  
   - Remote URL: https://github.com/hybrisPawelWiacek/loadapp_ai_v4  
   - Main branch: main  
   - After committing: git push origin main  
   - For new features: create branches from main (e.g., feature/my_new_feature)

---

## 4. Architectural Philosophy & Clean Architecture Principles

1. Prefer simplicity over complexity.  
2. Avoid premature optimization.  
3. Follow YAGNI (You Aren't Gonna Need It) principle.  
4. Maintain:
   - Clean architecture principles  
   - Domain-driven design practices  
   - Clear separation of concerns  
   - Proper error handling  
   - Essential documentation  

5. Keep domain logic in the backend/domain/ directory.  
   - Use dataclasses for domain entities.  
   - Keep services focused and stateless.

6. Infrastructure goes in backend/infrastructure/.  
   - Handle DB, external services, adapters, etc.

7. Use dependency injection patterns where practical.  
   - Document public interfaces and domain logic.  
   - Isolate external service configurations.

---

## 5. Code Style & Documentation

1. Use Python type hints consistently.

2. Follow Google-style docstrings.

3. Group imports (standard library, third-party, local) in logical order.

4. Use TODO markers for future extension points or technical debt.

5. Write meaningful commit messages that reflect the changes made (including any relevant ticket numbers).

---

## 6. Code Safety & Change Management

1. Never modify approved code without explicit permission.

2. Request approval before modifying code outside the immediate scope of the current task.

3. When suggesting changes to existing code:
   - Explain why the change is needed.
   - Show which files would be affected.
   - Wait for explicit approval before proceeding.

4. Focus changes only on files directly related to the current task.

5. Flag any potential impacts on existing functionality.

---

## 7. Testing Discipline

1. Run a full test suite after each implementation using:  
   - pytest [test_file] -v  
   - Avoid python -m pytest or other variations.

2. When tests fail:
   - Analyze the cause.  
   - Present two options with pros/cons:  
     1) Update tests to match new requirements.  
     2) Modify the code to make tests pass.  
   - Wait for explicit approval on how to proceed.

3. Document any test modifications with a rationale.

4. Ensure test coverage for new functionality. Keep coverage above 60%.

5. Maintain the integrity of existing tests; do not modify them unnecessarily.

---

## 8. Database Design & SQLAlchemy Model Guidelines

1. Always confirm SQLite compatibility before implementing models.  
   - Use Column(String(36)) for UUID.  
   - Use Column(DateTime(timezone=True)) for datetimes (store in UTC).  
   - Use INTEGER for booleans (0 or 1).

2. Keep model names in PascalCase and column names in snake_case.

3. Avoid reserved names:  
   - metadata, query, session

4. Suffix infrastructure model classes with "Model" (e.g., BusinessModel).

5. Always define __tablename__ = 'some_table' in models.

6. Document data type conversions in model docstrings.  
   - For instance, converting Python UUID objects into strings before storing.

---

## 9. Port Usage & Service Configuration

1. Never use port 5000 for backend services (it conflicts with Apple AirTunes).  
   - Use port 5001 for the backend (Flask default is overridden).  
   - Use port 8501 for the Streamlit frontend.

2. Always log port configuration on startup to avoid conflicts.

---

## 9. Development Workflow

1. Start with a minimal viable solution.

2. Create implementation artifacts for major tasks:  
   - Gameplan document:
     - Step-by-step approach
     - Key technical decisions & trade-offs
     - Integration points and dependencies
     - Potential risks and mitigations
     - Core functionality components
     - Required tests & validations
     - Documentation updates
     - Integration verification steps

3. Track progress against the gameplan.

4. Reference the gameplan during implementation.

5. Suggest iterative improvements.

6. Comment on potential optimizations.

7. Reference relevant documentation.

8. Highlight technical risks.

---

## 10. Implementation Guidelines

### Phase 1: Analysis
1. Examine the existing codebase:
   - Use directory listings to understand the project structure.
   - Use grep or code search tools to locate similar or related code.
   - Read key source files thoroughly before beginning any modifications.

2. Document findings:
   - Existing models and data relationships.
   - Naming conventions and patterns in use.
   - Similar or overlapping functionality.

### Phase 2: Planning
1. Create a clear plan:
   - List all files to be modified or added.
   - Identify potential impacts on existing code.
   - Document dependencies and relationships.

2. Validate your approach:
   - Ensure new code follows existing patterns.
   - Verify naming conventions remain consistent.
   - Confirm no duplication of functionality.
   - Consider the impact on tests (new and existing).

### Phase 3: Implementation Rules
1. Do not rewrite existing code unless explicitly requested.
2. Do not rename existing models/classes/functions.
3. Avoid changing established patterns or conventions.
4. Limit your modifications to the minimal set needed.

### Phase 4: Implementation Order
1. Start with the smallest changes possible.
2. Add or extend new models that build on existing ones.
3. Create new repositories following the current structure and patterns.
4. Add or modify routes in a manner consistent with the existing API design.
5. Write new tests that match the style and structure of existing tests.

### Phase 5: Validation Steps
1. Run existing tests before making any changes (baseline).
2. Make changes incrementally and run tests again.
3. Document any test failures you encounter.
4. Never proceed with broken tests; fix them or get approval on how to handle them.

### Phase 6: Code Review Checklist
1. Check for duplication of existing functionality.
2. Confirm you're following established patterns and naming standards.
3. Ensure existing tests remain valid and pass.
4. Verify new changes are minimal and necessary.
5. Document or comment your reasoning when changes are non-trivial.

### When in Doubt
1. Pause and request clarification from the team or project owner.
2. Perform more thorough reviews of existing code.
3. Document concerns and potential alternatives.
4. Wait for explicit approval before making significant changes.

---

## 11. Common Mistakes & Prevention

• Always search the codebase for existing implementations before adding new ones.  
• Keep domain code in backend/domain/, API code in backend/api/, infrastructure code in backend/infrastructure/, and frontend code in frontend/.  
• Avoid rewriting or renaming known, tested modules without clear justification and approval.  
• Confirm database type compatibility (especially for SQLite) before storing data.  
• Maintain consistent naming across classes, files, variables, and routes.

---

## 12. Putting It All Together

1. Start with minimal, focused changes in each development cycle.
2. Write or update tests, run them frequently, and keep coverage in mind.
3. Use conventional commit messages and push to the correct remote branch or main branch when ready.
4. Document your approach in a gameplan when working on major features.
5. Follow simple, clean architecture patterns; do not over-engineer.

---

## 13. Final Note

By adhering to these combined guidelines—covering environment setup, code style, testing, database design, version control, and a thorough approach to design and implementation—we ensure the ongoing quality and maintainability of the LoadApp.AI platform. When in doubt, seek clarification before proceeding. 