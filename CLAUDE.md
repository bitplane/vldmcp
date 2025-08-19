# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project summary

vldmcp is a distributed Friend-of-a-Friend (FoaF) MCP server built on the Veilid
network and podman containers. It enables bots and humans to collaboratively
build and share capabilities, vote on services, and manage resources in a
decentralized peer-to-peer network. The project provides a CLI, REST API,
and TUI for managing Veilid identities, containerized services, and P2P
connections.

## Commands

### Build and Development
```bash
# Install dependencies and prepare for development
make dev

# Run all tests
make test

# Run pre-commit hooks
pre-commit run --all-files

# Clean all build artifacts
make clean
```

## CODING STANDARDS

* IMPORTANT: DON'T USE IMPORT IN FUNCTIONS
* IMPORTANT: DON'T ADD MORE FUNCTIONALITY THAN WHAT WAS ASKED FOR
* Python 3.11+ required. So type hints rarely need `typing` module.
* Line length for code: 120 characters (configured in `pyproject.toml`).
* Line length for Markdown is 80 wide so it fits in a standard terminal.
* All imports should be at module level (not in functions).
* The project will degrade into verbose, brittle spaghetti if left unchecked.
  Periodically propose simplifications.
* Branches are a source of shame, disgust and anger. They should be used
  sparingly, because dogs get kicked to death when there are too many branches.
* Defensive programming is for the weak. If their input is shit, them eat stack
  traces.
* Do not guess, read the docs. All the files are in source control or in the
  `.venv` dir at the project root.
* Also, don't use imports in functions.
* The version of this project is 0.0.1. We don't need legacy versions of
  anything. They're branches that cause people's wives to walk into doors and
  stepchildren to fall down the stairs.

### Testing

* Do not run `python -m pytest`. This must be authorized each run. Use
  `make test` or `./scripts/test.sh` which can actually be executed without
  bugging the user.
* Use `pytest` functional style for tests. No `TestClassBasedTestBSThanks`
* When there's a bug, write a test case for the component.
* Failing tests are good tests; they tested something. Don't write tests to
  pass, they are adversarial.
* The only functionality that is required, is functionality that is covered by
  a test. The only exception to this is where it has a comment that explains
  what it supposed to do, why it is important enough to exist yet simultaneously
  not important enough to be covered by a test. Tests
* Do not use mocks in tests unless required; they make a mockery of our
  codebase.
* And once again, it's important to remember: Don't use import in functions.

## Architecture & Implementation Status

### Client-Server Separation
vldmcp uses a client-server model with cryptographic key separation for
security:

**Client Process (`vldmcp` CLI):**
- Has access to user's private key (`~/.local/share/vldmcp/keys/user.key`)
- Signs requests using user's key
- Forwards signed requests to daemon via HTTP
- Will run TUI that communicates with daemon
- No direct P2P network access

**Daemon Process (`vldmcpd` server):**
- Runs in background (native Python or podman container)
- Has its own daemon key (separate from user key)
- Hosts HTTP API for client requests
- Connects to Veilid P2P network
- Verifies incoming requests using registered user public keys
- Maintains permissions/authorization for known users
- No access to user's private key

### Service Tree Architecture
The Service model provides composable, hierarchical components that can be
proxied/replaced. Each service can host child services and expose methods with
security decorators.

**Key Service Components:**
- `Service`: Base class with lifecycle, routing, and method exposure
- `@expose(security="...")`: Decorator for exposing methods with permissions
- `Context`: Request context with user identity, roles, groups
- `Security`: Rules engine for permission evaluation
- `Platform`: Root service that manages deployment environment

**Current Service Tree (Client):**
```
Platform (root)
├── Storage (file operations, paths)
├── Config (configuration management)
├── Crypto (key management)
└── Daemon (process management)
```

**Planned Service Trees:**

Client Tree:
```
Platform (root)
├── Storage (user key path)
├── Config
├── Crypto (signs with user key)
├── HTTPClient (sends signed requests)
└── TUI (future)
```

Daemon Tree:
```
DaemonPlatform (root)
├── Storage (daemon key path)
├── Config
├── Crypto (verifies/signs)
├── HTTPServer (FastAPI)
├── Security (permissions)
├── IDService (user/key registry)
├── CRUDService (persistence)
└── VeilidService (P2P)
```

### Request Flow & Signing

1. **JWT-Style Signing**: Custom format using existing `Context.to_jwt_payload()`
   with added cryptographic signatures
2. **Request Path**: User → CLI → HTTPClient.sign() → HTTP → HTTPServer.verify()
   → Daemon services
3. **Key Usage**:
   - User key signs client requests
   - Daemon key signs forwarded P2P requests
   - Context determines which key to use

### Permission Model (Already Implemented)
- `Security` model with rules for user/group/role/path matching
- `Context` carries user identity and permissions
- Admin users can register keys and assign to groups
- Default groups: admin, user (more can be added)

### MCP Integration (Future)
MCP servers will become Service nodes in the tree, running as isolated
processes with stdin/stdout communication to the FastAPI service. This is not
immediate priority.

### Implementation Requirements

**Required Components:**
1. **HTTPClient Service**: Client-side service that signs requests with user key
2. **HTTPServer Service**: Daemon-side FastAPI service with authentication
3. **Daemon Root Service**: Separate Platform with daemon-specific storage paths
4. **JWT Signing**: Extend SecurityService with real Ed25519 signatures
5. **Key Registration API**: Admin endpoints to register user public keys

**Needs Reshaping:**
1. **Storage Service**: Need separate instances for client vs daemon paths
2. **Platform Classes**: Need DaemonPlatform variant with different key paths
3. **Security Service**: Add actual cryptographic operations (currently
   placeholder)

**Surplus/Defer:**
1. **MCP Server Integration**: Not needed for initial HTTP API
2. **Veilid Integration**: Can be added after HTTP API works
3. **TUI**: Can be added after core client-server communication works

### Next Implementation Steps
1. Create HTTPServer service with FastAPI
2. Create HTTPClient service with request signing
3. Implement real JWT signing in SecurityService
4. Create DaemonPlatform with separate storage paths
5. Add key registration endpoints
6. Test client-server communication

## todo

I'll update `todo.md` with next steps while you are working. Keep the todo list
up to date, I'll review, commit, push etc and add the next steps.
