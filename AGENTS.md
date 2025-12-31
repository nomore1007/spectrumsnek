# AGENTS.md - Development Guidelines for AI Agents

This document provides essential information for AI coding agents working in this repository. It includes build/test/lint commands, code style guidelines, and development practices.

## Build, Lint, and Test Commands

### Primary Build Commands
```bash
# Setup environment, dependencies, and device permissions
./setup.sh

# Run the radio scanner (hardware mode)
./run_scanner.sh [options]

# Run interactive mode (keyboard controls)
./run_scanner.sh --interactive [options]

# Run demo mode (no hardware required)
./run_scanner.sh --demo [options]

# Check Python syntax
python -m py_compile radio_scanner.py interactive_scanner.py
```

### Testing Commands
```bash
# Run syntax check
python -m py_compile radio_scanner.py interactive_scanner.py

# Test full setup (hardware, drivers, permissions)
./test_setup.sh

# Test RTL-SDR connection (requires hardware)
./run_scanner.sh --freq 100 --mode spectrum --duration 1

# Test interactive mode (requires hardware, will timeout)
timeout 5 ./run_scanner.sh --interactive --freq 100
# Use Page Up/Down to select frequency digits, arrows to adjust

# Test web interface (requires hardware)
./run_scanner.sh --interactive --web --freq 100 &
# Then visit http://localhost:5000 in browser

# Test recording functionality
./run_scanner.sh --freq 95.5 --mode record --duration 5
```

### Linting and Code Quality
```bash
# Run Python syntax check
python -m py_compile radio_scanner.py

# Check code style (requires flake8)
flake8 radio_scanner.py

# Format code (requires black)
black radio_scanner.py

# Type checking (requires mypy)
mypy radio_scanner.py
```

### Development Workflow
```bash
# Install dependencies
pip install -r requirements.txt

# Activate virtual environment
source venv/bin/activate

# Run scanner directly (terminal-only)
python radio_scanner.py [options]

# Run demo mode (no hardware required)
python demo_scanner.py [options]

# Deactivate virtual environment
deactivate
```

## Code Style Guidelines

### General Principles
- Write clear, readable, and maintainable code
- Follow DRY (Don't Repeat Yourself) principle
- Use descriptive variable and function names
- Keep functions small and focused on single responsibility
- Add comments for complex logic, not obvious code
- Handle errors gracefully with appropriate error messages

### Language-Specific Guidelines

#### JavaScript/TypeScript
```typescript
// Use const for constants, let for variables
const PI = 3.14159;
let counter = 0;

// Prefer arrow functions for anonymous functions
const calculateTotal = (items) => items.reduce((sum, item) => sum + item.price, 0);

// Use template literals instead of string concatenation
const greeting = `Hello, ${name}!`;

// Prefer async/await over promises for readability
async function fetchUserData(userId) {
  try {
    const response = await fetch(`/api/users/${userId}`);
    const userData = await response.json();
    return userData;
  } catch (error) {
    console.error('Failed to fetch user data:', error);
    throw new Error('Unable to retrieve user information');
  }
}
```

### File Organization
```
src/
├── components/     # Reusable UI components
├── pages/         # Page-level components
├── hooks/         # Custom React hooks
├── utils/         # Utility functions
├── services/      # API calls and external services
├── types/         # TypeScript type definitions
├── constants/     # Application constants
└── styles/        # CSS/SCSS files
```

### Naming Conventions

#### Files and Directories
- Use kebab-case for file names: `user-profile.tsx`
- Use PascalCase for component files: `UserProfile.tsx`
- Use camelCase for utility files: `dateHelpers.js`

#### Variables and Functions
- camelCase for variables and functions: `userName`, `calculateTotal`
- PascalCase for classes and components: `UserService`, `Button`
- UPPER_SNAKE_CASE for constants: `MAX_RETRY_ATTEMPTS`

#### TypeScript Specific
```typescript
// Interface names with 'I' prefix
interface IUser {
  id: number;
  name: string;
}

// Type aliases without prefix
type UserRole = 'admin' | 'user' | 'guest';

// Generic type parameters with descriptive names
interface ApiResponse<TData> {
  data: TData;
  status: number;
}
```

### Import/Export Guidelines
```typescript
// Group imports by type, separate with blank lines
import React from 'react';
import { useState, useEffect } from 'react';

import { Button } from '../components/Button';
import { formatDate } from '../utils/dateHelpers';
import type { User } from '../types/User';

// Prefer named exports over default exports
export const calculateTax = (amount, rate) => amount * rate;

// Use default export only for main component of a file
const UserProfile = () => { /* ... */ };
export default UserProfile;
```

### Error Handling
```typescript
// Always handle promise rejections
async function processData() {
  try {
    const result = await riskyOperation();
    return result;
  } catch (error) {
    // Log error with context
    console.error('Failed to process data:', error);

    // Re-throw with meaningful message or handle gracefully
    throw new Error('Data processing failed. Please try again later.');
  }
}

// Use custom error classes for specific error types
class ValidationError extends Error {
  constructor(field, message) {
    super(`Validation failed for ${field}: ${message}`);
    this.name = 'ValidationError';
    this.field = field;
  }
}
```

### Testing Guidelines
```typescript
// Use descriptive test names
describe('User Authentication', () => {
  test('should authenticate valid user credentials', async () => {
    // Arrange
    const validCredentials = { email: 'user@example.com', password: 'password123' };

    // Act
    const result = await authenticateUser(validCredentials);

    // Assert
    expect(result.success).toBe(true);
    expect(result.user).toBeDefined();
  });

  test('should reject invalid credentials', async () => {
    // Arrange
    const invalidCredentials = { email: 'user@example.com', password: 'wrong' };

    // Act & Assert
    await expect(authenticateUser(invalidCredentials)).rejects.toThrow('Invalid credentials');
  });
});
```

### Performance Considerations
- Avoid unnecessary re-renders in React components
- Use memoization for expensive computations
- Optimize bundle size by code splitting
- Use appropriate data structures for performance-critical operations
- Profile and optimize database queries

### Security Best Practices
- Never log sensitive information (passwords, tokens, keys)
- Validate and sanitize user inputs
- Use HTTPS for all external requests
- Implement proper authentication and authorization
- Regularly update dependencies for security patches
- Use environment variables for configuration, not hardcoded values

### Git Commit Guidelines
```bash
# Use conventional commit format
git commit -m "feat: add user authentication feature"
git commit -m "fix: resolve login timeout issue"
git commit -m "docs: update API documentation"
git commit -m "refactor: simplify user validation logic"

# Commit message format: type(scope): description
# Types: feat, fix, docs, style, refactor, test, chore
```

### Code Review Checklist
- [ ] Code follows established patterns and conventions
- [ ] Functions are small and focused on single responsibility
- [ ] Error handling is appropriate and comprehensive
- [ ] Tests are included and provide good coverage
- [ ] No sensitive information is logged or committed
- [ ] Performance considerations are addressed
- [ ] Documentation is updated if needed

This document should be updated as the project evolves and new conventions are established.