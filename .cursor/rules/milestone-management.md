# Milestone Management Rules

## Milestone Completion Process

**⚠️ MANDATORY: A milestone is NOT complete until ALL items below are checked off**

Use `make milestone-checklist` to see the full checklist. ALWAYS create a TodoWrite list with these exact items when working on milestones.

## Technical Implementation Requirements

### Code Quality Gate

- [ ] All technical requirements implemented and functional
- [ ] All acceptance criteria from milestone spec met
- [ ] Code quality checks pass: `make lint` (ruff, black, eslint)
- [ ] Type checking passes: `make typecheck` (mypy strict mode)
- [ ] All tests pass: `make test` (backend pytest, frontend vitest)
- [ ] Security requirements validated (if applicable)

### Implementation Verification Commands

```bash
# Verify all quality gates pass
make lint && make typecheck && make test

# Verify environment consistency
conda run -n ymb-py311 python --version
make check-deps

# Verify security requirements (if applicable)
conda run -n ymb-py311 pytest tests/test_*security*.py -v
```

## Documentation Updates (MANDATORY)

### MVP Implementation Plan Updates

**File: `MVP_imp_plan.md`**

1. **Add ✅ checkmark to milestone title**

   ```markdown
   ### Milestone 1.X – Description ✅
   ```

2. **Add "Status: **COMPLETED**" to milestone description**

   ```markdown
   - Status: **COMPLETED**
   ```

3. **Add reference to detailed spec file**
   ```markdown
   Note: Detailed spec can be found in [M1.X_spec.md](M1.X_spec.md).
   ```

### CLAUDE.md Updates

**File: `CLAUDE.md`**

- Update "Current Status" section to reflect latest completion
- Update milestone progress information
- Reference new capabilities and next steps

### Milestone Checklist Updates

**File: `MVP_imp_plan.md` (bottom section)**

- Update milestone checklist from `[ ]` to `[x]`
- Ensure checklist reflects actual completion status

## Commit and Push Requirements

### Comprehensive Commit Message

```bash
# Example comprehensive commit message
git commit -m "feat: complete milestone 1.X - [description]

- Implement [technical requirement 1]
- Add [technical requirement 2]
- Include comprehensive security controls
- Add full test suite with [X]% coverage
- Update documentation and milestone tracking

Closes #[issue-number]"
```

### Verification Steps

```bash
# 1. Push changes to GitHub
git push origin branch-name

# 2. Verify all changes are reflected in remote repository
git log --oneline -n 5

# 3. Check GitHub Actions CI passes
# (View in GitHub web interface)
```

## Process Validation

### TodoWrite Item Completion

- [ ] All TodoWrite items marked as completed
- [ ] Documentation accurately reflects milestone completion
- [ ] Ready for next milestone or PR creation

### Personal Workflow Rule

**NEVER mark milestone TodoWrite items as "completed" without first completing ALL documentation updates above.**

## Example Milestone Format

### Completed Milestone Documentation

```markdown
### Milestone 1.4 – RSS Source Seeding and Single-Feed Ingestion ✅

- Goal: Complete RSS ingestion pipeline with security architecture
- Status: **COMPLETED**
  Note: Detailed spec can be found in [M1.4_spec.md](M1.4_spec.md).
- Implementation:
  - Feed client with SSRF protection
  - XSS sanitization with bleach
  - Content mapper with validation
  - CLI tools for ingestion
  - Comprehensive security test suite
```

## Milestone Workflow Patterns

### Starting a New Milestone

1. **Read the milestone specification** (e.g., `M1.X_spec.md`)
2. **Create TodoWrite list** with all technical requirements
3. **Set up development environment** if needed
4. **Begin implementation** following security-first approach

### During Implementation

1. **Regular commits** with descriptive messages
2. **Run quality checks** frequently: `make lint && make typecheck && make test`
3. **Update TodoWrite progress** as tasks are completed
4. **Document any blockers or deviations** from the spec

### Milestone Completion

1. **Complete ALL technical requirements**
2. **Pass ALL quality gates**
3. **Update ALL documentation** (MVP plan, CLAUDE.md, checklist)
4. **Create comprehensive commit** with full description
5. **Push and verify** all changes are reflected

## Quality Assurance

### Pre-Completion Checklist

Before marking any milestone as complete, verify:

- All acceptance criteria met
- Security requirements implemented and tested
- Documentation is accurate and up-to-date
- Code quality gates pass
- Tests provide adequate coverage
- No regressions introduced

### Post-Completion Verification

After marking milestone complete:

- Verify GitHub reflects all changes
- Check that CI passes
- Confirm next milestone is ready to begin
- Update project status communications

## Integration with Project Workflow

### Milestone Dependencies

- Each milestone builds on previous completed milestones
- Ensure dependencies are met before beginning
- Document any changes to dependency assumptions

### Security Integration

- All milestones must implement security controls
- Security testing required for all milestones
- Security review before marking complete

### Documentation Consistency

- Keep all documentation sources aligned
- Update project status in multiple locations
- Maintain accurate progress tracking
